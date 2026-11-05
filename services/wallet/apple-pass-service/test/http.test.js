import { test } from "node:test";
import assert from "node:assert/strict";
import { once } from "node:events";

// Configure the real limiter before importing the application.
process.env.PKPASS_RATE_MAX_REQUESTS = "3";
const { app } = await import("../server.js");

test("wallet HTTP contract under Express 5 and rate-limit 8", async () => {
  const server = app.listen(0, "127.0.0.1");
  await once(server, "listening");
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    const health = await fetch(`${base}/health`);
    assert.equal(health.status, 200);
    assert.deepEqual(await health.json(), { ok: true, service: "crown-apple-pass" });

    // Express 5 leaves req.body undefined if an empty POST is not parsed.
    // Reject absent ticket inputs as client errors, not signing failures.
    for (let count = 0; count < 3; count += 1) {
      const response = await fetch(`${base}/pkpass`, { method: "POST" });
      assert.equal(response.status, 400, `request ${count + 1} must fail closed`);
      assert.deepEqual(await response.json(), { ok: false, message: "ticketId is required" });
    }

    const limited = await fetch(`${base}/pkpass`, { method: "POST" });
    assert.equal(limited.status, 429);
    assert.deepEqual(await limited.json(), { ok: false, message: "Too many requests" });
    assert.ok(limited.headers.get("retry-after"), "rate limiter must provide retry guidance");
  } finally {
    await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  }
});
