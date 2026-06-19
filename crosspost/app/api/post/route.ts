import { NextRequest, NextResponse } from "next/server";

const HASHTAG_LINE = /^(#[^\s#]+)(\s+#[^\s#]+)*$/;

// A trailing line of only "#tag1 #tag2 ..." is treated as category metadata,
// not body copy, so it's split off and turned into WordPress categories instead.
function extractHashtags(content: string): { content: string; tags: string[] } {
  const lines = content.split("\n");
  let lastIndex = lines.length - 1;
  while (lastIndex >= 0 && lines[lastIndex].trim() === "") {
    lastIndex--;
  }

  if (lastIndex < 0 || !HASHTAG_LINE.test(lines[lastIndex].trim())) {
    return { content, tags: [] };
  }

  const tags = lines[lastIndex].trim().split(/\s+/).map((tag) => tag.slice(1));
  const strippedContent = lines.slice(0, lastIndex).join("\n").trimEnd();
  return { content: strippedContent, tags };
}

async function getOrCreateWordPressCategoryIds(
  categories: string[],
  url: string,
  authHeader: string
): Promise<{ categoryIds: number[]; warnings: string[] }> {
  const categoryIds: number[] = [];
  const warnings: string[] = [];

  for (const categoryName of categories) {
    const searchResponse = await fetch(`${url}/wp-json/wp/v2/categories?search=${encodeURIComponent(categoryName)}`, {
      headers: { Authorization: authHeader },
    });

    if (!searchResponse.ok) {
      const error = await searchResponse.text();
      throw new Error(`WordPress category lookup error (${searchResponse.status}): ${error}`);
    }

    const matches: { id: number; name: string }[] = await searchResponse.json();
    const exact = matches.find((category) => category.name.toLowerCase() === categoryName.toLowerCase());

    if (exact) {
      categoryIds.push(exact.id);
      continue;
    }

    const createResponse = await fetch(`${url}/wp-json/wp/v2/categories`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader,
      },
      body: JSON.stringify({ name: categoryName }),
    });

    if (!createResponse.ok) {
      const error = await createResponse.text();
      // Creating a new category needs the manage_categories capability (Editor/Admin).
      // Don't fail the whole post over a missing category — skip it and warn instead.
      warnings.push(
        `Could not create WordPress category "#${categoryName}" (${createResponse.status}): ${error}. The WordPress user needs Editor or Administrator role to create new categories.`
      );
      continue;
    }

    const created = await createResponse.json();
    categoryIds.push(created.id);
  }

  return { categoryIds, warnings };
}

async function postToWordPress(title: string, content: string, hashtags: string[]) {
  const url = process.env.WORDPRESS_URL;
  const username = process.env.WORDPRESS_USERNAME;
  const appPassword = process.env.WORDPRESS_APP_PASSWORD;

  if (!url || !username || !appPassword) {
    throw new Error("WordPress credentials not configured in .env.local");
  }

  const credentials = Buffer.from(`${username}:${appPassword}`).toString("base64");
  const authHeader = `Basic ${credentials}`;

  const { categoryIds, warnings } =
    hashtags.length > 0
      ? await getOrCreateWordPressCategoryIds(hashtags, url, authHeader)
      : { categoryIds: [], warnings: [] };

  const response = await fetch(`${url}/wp-json/wp/v2/posts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: authHeader,
    },
    body: JSON.stringify({
      title,
      content,
      status: "publish",
      ...(categoryIds.length > 0 && { categories: categoryIds }),
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`WordPress error (${response.status}): ${error}`);
  }

  const data = await response.json();
  return { url: data.link, id: data.id, warnings };
}

async function postToLinkedIn(content: string) {
  const accessToken = process.env.LINKEDIN_ACCESS_TOKEN;
  const authorUrn = process.env.LINKEDIN_AUTHOR_URN;

  if (!accessToken || !authorUrn) {
    throw new Error("LinkedIn credentials not configured in .env.local");
  }

  const response = await fetch("https://api.linkedin.com/v2/ugcPosts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "X-Restli-Protocol-Version": "2.0.0",
    },
    body: JSON.stringify({
      author: authorUrn,
      lifecycleState: "PUBLISHED",
      specificContent: {
        "com.linkedin.ugc.ShareContent": {
          shareCommentary: { text: content },
          shareMediaCategory: "NONE",
        },
      },
      visibility: {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
      },
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`LinkedIn error (${response.status}): ${error}`);
  }

  const data = await response.json();
  return { id: data.id };
}

export async function POST(req: NextRequest) {
  try {
    const { title, content } = await req.json();

    if (!title?.trim() || !content?.trim()) {
      return NextResponse.json({ error: "Title and content are required" }, { status: 400 });
    }

    const results: { wordpress?: { url: string; id: number }; linkedin?: { id: string }; errors: string[] } = {
      errors: [],
    };

    const { content: wpContent, tags: hashtags } = extractHashtags(content);

    const [wpResult, liResult] = await Promise.allSettled([
      postToWordPress(title, wpContent, hashtags),
      postToLinkedIn(content),
    ]);

    if (wpResult.status === "fulfilled") {
      results.wordpress = { url: wpResult.value.url, id: wpResult.value.id };
      results.errors.push(...wpResult.value.warnings);
    } else {
      results.errors.push(`WordPress: ${wpResult.reason.message}`);
    }

    if (liResult.status === "fulfilled") {
      results.linkedin = liResult.value;
    } else {
      results.errors.push(`LinkedIn: ${liResult.reason.message}`);
    }

    const bothFailed = !results.wordpress && !results.linkedin;
    if (bothFailed) {
      return NextResponse.json({ error: "All posts failed", details: results.errors }, { status: 500 });
    }

    return NextResponse.json(results);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unexpected error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
