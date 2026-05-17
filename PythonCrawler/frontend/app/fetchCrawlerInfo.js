"use client";

export async function callCrawler({ url, maxPages }) {
  console.log("Function was called...");

  const response = await fetch("/api/crawler", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url,
      max_pages: maxPages,
    }),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const data = await response.json();
  console.log("Crawler Response: ", data);
  return data;
}