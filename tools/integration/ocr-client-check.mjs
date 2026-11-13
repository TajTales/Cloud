// Real production FE client → application TestServer → synthetic HTTP OCR
// producer → actual DynamoDB Local. No DOM or model accuracy claim here.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import ts from "typescript";
const base = new URL(process.argv[2]);
assert.equal(base.hostname, "127.0.0.1");
const bytes = readFileSync(process.argv[3]);
const fetchHttp = globalThis.fetch, cookies = new Map();
globalThis.window = { setTimeout, clearTimeout };
globalThis.fetch = async (input, init = {}) => {
  const url = new URL(input, base); assert.equal(url.origin, base.origin);
  const headers = new Headers(init.headers);
  if (url.pathname.startsWith("/local-auth/")) headers.set("Cookie", [...cookies].map(([name, value]) => `${name}=${value}`).join("; "));
  const response = await fetchHttp(url, { ...init, headers });
  for (const cookie of response.headers.getSetCookie()) {
    const [name, ...parts] = cookie.split(";", 1)[0].split("=");
    const value = parts.join("="); if (value) cookies.set(name, value); else cookies.delete(name);
  }
  return response;
};
const code = ts.transpileModule(readFileSync(new URL("../../src/api/learning.ts", import.meta.url), "utf8"), { compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext } }).outputText.replaceAll("import.meta.env", "({VITE_API_MODE:'real'})");
const { learningClient: client } = await import("data:text/javascript;base64," + Buffer.from(code).toString("base64"));
const checks = [];
await client.authenticate("register", { display_name: "OCR FE test", email: `ocr-${crypto.randomUUID()}@example.invalid`, password: "A synthetic integration password!" });
const session = await client.createSession("FE OCR client", "ja");
const source = await client.registerSource(session.session_id, { source_id: crypto.randomUUID(), kind: "local_video", width_px: 640, height_px: 360, duration_ms: 30000, expected_version: session.version }, crypto.randomUUID()); checks.push("register_source");
const metadata = { source_id: source.source_id, frame_id: crypto.randomUUID(), frame_index: 0, media_time_ms: 1000, captured_at: new Date().toISOString(), width_px: 640, height_px: 360, content_type: "image/png", size_bytes: bytes.length };
const upload = await client.createUpload(session.session_id, metadata, crypto.randomUUID());
await client.putFrame(upload, new Blob([bytes], { type: "image/png" })); checks.push("upload_real_png");
let job = await client.createJob(session.session_id, upload, crypto.randomUUID()); checks.push("create_durable_job");
const deadline = Date.now() + 10000;
while (["queued", "processing"].includes(job.status)) { assert(Date.now() < deadline); await new Promise(resolve => setTimeout(resolve, 100)); job = await client.getJob(job.job_id); }
assert.equal(job.status, "succeeded");
const result = await client.getResult(job.result_id);
assert.equal(result.frame_id, metadata.frame_id); assert.equal(result.job_id, job.job_id); assert.equal(result.source_id, source.source_id); assert.equal(result.provider, "fixture.synthetic"); checks.push("poll_result_reference_consistency");
assert.equal((await client.createJob(session.session_id, upload, crypto.randomUUID())).job_id, job.job_id); checks.push("duplicate_job_same_resource");
const current = await client.getSession(session.session_id);
const page = await client.resultPage(session.session_id, current.latest_seq);
assert.equal(page.items[0].result_id, result.result_id); checks.push("history_manifest_matches_detail");
await client.registerSource(session.session_id, { source_id: crypto.randomUUID(), kind: "local_video", width_px: 640, height_px: 360, duration_ms: 30000, expected_version: current.version }, crypto.randomUUID());
await assert.rejects(client.createUpload(session.session_id, { ...metadata, frame_id: crypto.randomUUID(), frame_index: 1 }, crypto.randomUUID()), error => error.code === "STALE_SOURCE"); checks.push("old_source_rejected");
assert.equal((await client.endSession(session)).status, "ended"); checks.push("end_uses_latest_session_version");
await client.logout();
console.log(JSON.stringify({ status: "PASS", checks, real_http: true, actual_dynamodb_local: true, ocr_producer: "synthetic", browser_dom_tested: false }));
