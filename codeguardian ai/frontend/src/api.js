async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

export const reviewCode = (code, language, filename, use_ai) =>
  post("/api/review", { code, language, filename, use_ai });

export const reviewPR = (pr_url, github_token, use_ai, post_comment) =>
  post("/api/github/pr", { pr_url, github_token: github_token || null, use_ai, post_comment });
