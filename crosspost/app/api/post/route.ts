import { NextRequest, NextResponse } from "next/server";

async function postToWordPress(title: string, content: string) {
  const url = process.env.WORDPRESS_URL;
  const username = process.env.WORDPRESS_USERNAME;
  const appPassword = process.env.WORDPRESS_APP_PASSWORD;

  if (!url || !username || !appPassword) {
    throw new Error("WordPress credentials not configured in .env.local");
  }

  const credentials = Buffer.from(`${username}:${appPassword}`).toString("base64");

  const response = await fetch(`${url}/wp-json/wp/v2/posts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Basic ${credentials}`,
    },
    body: JSON.stringify({
      title,
      content,
      status: "publish",
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`WordPress error (${response.status}): ${error}`);
  }

  const data = await response.json();
  return { url: data.link, id: data.id };
}

async function postToLinkedIn(title: string, content: string) {
  const accessToken = process.env.LINKEDIN_ACCESS_TOKEN;
  const authorUrn = process.env.LINKEDIN_AUTHOR_URN;

  if (!accessToken || !authorUrn) {
    throw new Error("LinkedIn credentials not configured in .env.local");
  }

  const text = `${title}\n\n${content}`;

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
          shareCommentary: { text },
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

    const [wpResult, liResult] = await Promise.allSettled([
      postToWordPress(title, content),
      postToLinkedIn(title, content),
    ]);

    if (wpResult.status === "fulfilled") {
      results.wordpress = wpResult.value;
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
