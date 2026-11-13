// Production TypeScript client + real HTTP. Clock adjustment only forces renewal;
// cookies/timers adapt Node, no API response or token is invented here.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import ts from "typescript";

const base = new URL(process.argv[2]);
assert(["127.0.0.1", "localhost", "[::1]"].includes(base.hostname));
const cookies = new Map();
const fetchHttp = globalThis.fetch;
let renewals = 0;
globalThis.window = { setTimeout, clearTimeout };
globalThis.fetch = async (input, init = {}) => {
  const url = new URL(input, base); assert.equal(url.origin, base.origin);
  const headers = new Headers(init.headers);
  if (url.pathname.startsWith("/local-auth/")) headers.set("Cookie", [...cookies].map(([key, value]) => `${key}=${value}`).join("; "));
  if (url.pathname === "/local-auth/refresh") renewals++;
  const response = await fetchHttp(url, { ...init, headers });
  for (const cookie of response.headers.getSetCookie()) {
    const [name, ...value] = cookie.split(";", 1)[0].split("=");
    if (value.join("=")) cookies.set(name, value.join("=")); else cookies.delete(name);
  }
  return response;
};
const code = ts.transpileModule(readFileSync(new URL("../../src/api/learning.ts", import.meta.url), "utf8"), {
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext },
}).outputText.replaceAll("import.meta.env", "({VITE_API_MODE:'real'})");
const { learningClient: client } = await import("data:text/javascript;base64," + Buffer.from(code).toString("base64"));
const checks = [];
const email = `auth-client-${crypto.randomUUID()}@example.invalid`;
let password = `Local-${crypto.randomUUID()}!`;
const profile = await client.authenticate("register", { email, password, display_name: "Auth client test" });
const actualNow = Date.now;
Date.now = () => actualNow() + 3600000;
try {
  const results = await Promise.all([client.me(), client.words(), client.history(), client.stats(), client.me()]);
  assert.equal(results[0].user_id, profile.user_id);
  assert.equal(renewals, 1); checks.push("concurrent_refresh_is_single_flight");
} finally { Date.now = actualNow; }
client.clearToken();
await Promise.all([client.authenticate("session"), client.authenticate("session")]);
assert.equal(renewals, 2); checks.push("concurrent_restore_is_single_flight");
await assert.rejects(client.adminUsers(), error => error.status === 403);
assert.equal((await client.me()).user_id, profile.user_id); checks.push("forbidden_admin_preserves_learner_session");
await client.authAction("password/change", { current_password: password, password: "Changed client test password!" });
password = "Changed client test password!";
const before = renewals;
await assert.rejects(client.me(), error => error.status === 401);
assert.equal(renewals - before, 1); checks.push("revoked_session_does_not_loop_refresh");
await client.authenticate("login", { email, password });
await client.authAction("logout-all");
await assert.rejects(client.me(), error => error.status === 401); checks.push("logout_all_revokes_real_session");
await client.authenticate("login", { email, password });
await client.logout();
await assert.rejects(client.me(), error => error.status === 401); checks.push("logout_does_not_silently_restore");
console.log(JSON.stringify({ status: "PASS", checks, browser_dom_tested: false, external_email_tested: false }));
