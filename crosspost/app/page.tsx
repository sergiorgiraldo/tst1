"use client";

import { useState } from "react";

type PostResult = {
  wordpress?: { url: string; id: number };
  linkedin?: { id: string };
  errors?: string[];
};

type LogEntry = {
  type: "info" | "success" | "error";
  message: string;
  timestamp: string;
};

export default function Home() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [posting, setPosting] = useState(false);
  const [log, setLog] = useState<LogEntry[]>([]);

  function addLog(type: LogEntry["type"], message: string) {
    const timestamp = new Date().toLocaleTimeString();
    setLog((prev) => [...prev, { type, message, timestamp }]);
  }

  async function handlePost() {
    if (!title.trim() || !content.trim()) {
      addLog("error", "Title and content cannot be empty.");
      return;
    }

    setPosting(true);
    addLog("info", "Starting crosspost...");

    try {
      const res = await fetch("/api/post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content }),
      });

      const data: PostResult & { error?: string; details?: string[] } = await res.json();

      if (!res.ok) {
        addLog("error", data.error ?? "Unknown error");
        if (data.details) {
          data.details.forEach((d) => addLog("error", d));
        }
        return;
      }

      if (data.wordpress) {
        addLog("success", `WordPress: Published — ${data.wordpress.url}`);
      }
      if (data.linkedin) {
        addLog("success", `LinkedIn: Published — Post ID ${data.linkedin.id}`);
      }
      if (data.errors && data.errors.length > 0) {
        data.errors.forEach((e) => addLog("error", e));
      }
    } catch {
      addLog("error", "Network error — could not reach the server.");
    } finally {
      setPosting(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-100 flex flex-col items-center py-14 px-4">
      <div className="w-full max-w-2xl">
        <h1 className="text-3xl font-bold text-orange-500 mb-8 tracking-wide">
          Crosspost
        </h1>

        <div className="bg-white rounded-2xl shadow-md p-8 flex flex-col gap-6">
          {/* Title input */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Post title"
              disabled={posting}
              className="border border-gray-200 rounded-lg px-4 py-2.5 text-gray-800 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-400 placeholder-gray-300 disabled:opacity-50"
            />
          </div>

          {/* Content editor */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
              Content
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your post here..."
              rows={12}
              disabled={posting}
              className="border border-gray-200 rounded-lg px-4 py-3 text-gray-800 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-400 placeholder-gray-300 resize-y disabled:opacity-50"
            />
          </div>

          {/* Post button */}
          <button
            onClick={handlePost}
            disabled={posting}
            className="bg-orange-500 hover:bg-orange-600 active:bg-orange-700 text-white font-semibold rounded-lg py-3 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {posting ? "Posting…" : "Publish to WordPress & LinkedIn"}
          </button>
        </div>

        {/* Log / status placeholder */}
        {log.length > 0 && (
          <div className="mt-6 bg-white rounded-2xl shadow-md p-6">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">
              Activity Log
            </h2>
            <ul className="flex flex-col gap-2">
              {log.map((entry, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="text-gray-300 font-mono shrink-0">{entry.timestamp}</span>
                  <span
                    className={
                      entry.type === "success"
                        ? "text-orange-500 font-medium"
                        : entry.type === "error"
                        ? "text-red-500"
                        : "text-gray-500"
                    }
                  >
                    {entry.type === "success" ? "✓" : entry.type === "error" ? "✗" : "·"}{" "}
                    {entry.message}
                  </span>
                </li>
              ))}
            </ul>
            <button
              onClick={() => setLog([])}
              className="mt-4 text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              Clear log
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
