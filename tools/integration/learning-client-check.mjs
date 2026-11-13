// Runs the production FE client against a real local TestServer; no fake API.
// Cookies/timers below adapt Node to browser APIs, not application responses.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import ts from "typescript";

const base = new URL(process.argv[2]);
assert(["127.0.0.1", "localhost", "[::1]"].includes(base.hostname));
const fetchHttp = globalThis.fetch;
const cookies = new Map();
globalThis.window = { setTimeout, clearTimeout };
globalThis.fetch = async (input, init = {}) => {
  const url = new URL(input, base);
  assert.equal(url.origin, base.origin);
  const headers = new Headers(init.headers);
  if (url.pathname.startsWith("/local-auth/")) headers.set("Cookie", [...cookies].map(([key, value]) => `${key}=${value}`).join("; "));
  const response = await fetchHttp(url, { ...init, headers });
  for (const value of response.headers.getSetCookie()) {
    const [name, ...parts] = value.split(";", 1)[0].split("=");
    const content = parts.join("=");
    if (content) cookies.set(name, content); else cookies.delete(name);
  }
  return response;
};
const code = ts.transpileModule(readFileSync(new URL("../../src/api/learning.ts", import.meta.url), "utf8"), {
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext },
}).outputText.replaceAll("import.meta.env", "({VITE_API_MODE:'real'})");
const { learningClient: client } = await import("data:text/javascript;base64," + Buffer.from(code).toString("base64"));
const checks = [];
const email = `fe-client-${crypto.randomUUID()}@example.invalid`;
const password = `Local-${crypto.randomUUID()}!`;
const profile = await client.authenticate("register", { email, password, display_name: "FE client integration" });
assert.equal(profile.email, email); checks.push("register_actual_account");
const updated = await client.updateProfile({ display_name: "FE name persisted", expected_version: profile.version });
assert.equal((await client.me()).display_name, updated.display_name); checks.push("profile_write_read");
const first = await client.saveWord("カフェ");
assert.equal((await client.saveWord("カフェ")).word_id, first.word_id); checks.push("save_deduplicate");
await client.saveWord("近く");
assert.equal((await client.words()).length, 2); checks.push("load_vocabulary");
assert.equal((await client.reviewWord(first, "known")).review_state, "known"); checks.push("persist_review");
await client.deleteWord(first.word_id);
assert.equal((await client.words()).length, 1); checks.push("delete_204_without_json");
const session = await client.createSession("FE session persisted", "ja");
assert.equal((await client.getSession(session.session_id)).status, "active"); checks.push("create_session");
assert.equal((await client.endSession(session)).status, "ended"); checks.push("end_session");
const history = await client.history();
assert(history.some(item => item.session_id === session.session_id && item.ended_at)); checks.push("history_from_database");
assert.equal((await client.stats()).saved_words_count, 1); checks.push("statistics_from_database");
client.clearToken();
const restored = await client.authenticate("session");
assert.equal(restored.user_id, profile.user_id); checks.push("reload_restore_cookie");
await client.logout();
await assert.rejects(client.me(), error => error.status === 401); checks.push("logout_revoked");
await client.authenticate("login", { email, password });
assert.equal((await client.words())[0].lemma, "近く"); checks.push("login_persisted_account_and_word");
await client.logout();
console.log(JSON.stringify({ status: "PASS", checks, user_id: profile.user_id, session_id: session.session_id, browser_dom_tested: false }));
