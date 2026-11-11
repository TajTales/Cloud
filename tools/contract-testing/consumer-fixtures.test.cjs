'use strict';
// DRAFT fixture inspection in browser-compatible JavaScript. Does not import the React app.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = path.resolve(__dirname, '../../contracts/fixtures');
const read = (filename) => JSON.parse(fs.readFileSync(path.join(base, filename), 'utf8'));

test('DRAFT: use code points rather than UTF-16 offsets; preserve combining marks', () => {
  const value = read('lexicon/unicode-code-points.json');
  const points = Array.from(value.text);
  assert.equal(value.text.length, points.length + 1);
  for (const token of value.tokens) {
    assert.equal(points.slice(token.start, token.end).join(''), token.surface);
  }
  assert.notEqual(value.text.slice(0, 1), value.tokens[0].surface);
  assert.equal(value.text, '😀喫茶店é');
});

test('DRAFT: poll, WS notification and HTTP detail share result references', () => {
  const job = read('http/job-succeeded.json').data;
  const result = read('http/getOcrResult-200.json').data;
  const event = read('ws/ocr-result_available.json');
  for (const key of ['session_id', 'source_id', 'frame_id', 'job_id', 'result_id']) {
    assert.equal(job[key], result[key]);
    assert.equal(event.data[key], result[key]);
  }
  assert.equal(event.seq, result.seq);
  assert.equal(event.data.media_time_ms, result.media_time_ms);
});

test('DRAFT: duplicate event and duplicate job retain their identities', () => {
  const first = read('ws/ocr-result_available.json');
  const again = read('ws/duplicate-result-event.json');
  assert.deepEqual(first, again);
  assert.equal(new Set([first.event_id, again.event_id]).size, 1);
  assert.equal(read('http/duplicate-job-new.json').data.job_id, read('http/duplicate-job-retry.json').data.job_id);
});

test('DRAFT: valid historical result is stale after the source switches', () => {
  const current = read('http/current-source-after-switch.json').data;
  const late = read('http/late-result-old-source.json').data;
  assert.equal(current.session_id, late.session_id);
  assert.notEqual(current.current_source_id, late.source_id);
});

test('DRAFT: higher event seq can still carry an older frame', () => {
  const displayed = read('http/getOcrResult-200.json').data;
  const late = read('ct04-draft/out-of-order-frame.json').data;
  const event = read('ct04-draft/out-of-order-event.json');
  assert.equal(late.source_id, displayed.source_id);
  assert.ok(event.seq > displayed.seq);
  assert.ok(late.frame_index < displayed.frame_index);
  assert.ok(late.media_time_ms < displayed.media_time_ms);
  assert.equal(event.data.result_id, late.result_id);
});

test('DRAFT: raw success/no-text mapping preserves provider content', () => {
  assert.deepEqual(read('ocr/success.json'), read('http/getOcrResult-200.json').data.ocr);
  assert.deepEqual(read('ocr/no-text.json'), read('http/ocr-no-text.json').data.ocr);
  assert.deepEqual(read('ocr/no-text.json').paragraphs, []);
  assert.ok(read('ocr/invalid-image-raw.json').error);
});

test('DRAFT: inflected surface differs from lemma; senses remain distinct', () => {
  const token = read('ct04-draft/lexicon-inflected.json').tokens[0];
  assert.notEqual(token.surface, token.lemma);
  assert.ok(token.inflection);
  const a = read('ct04-draft/lexicon-polysemy-a.json').tokens[0];
  const b = read('ct04-draft/lexicon-polysemy-b.json').tokens[0];
  assert.equal(a.entry_id, b.entry_id);
  assert.notEqual(a.sense_id, b.sense_id);
});

test('DRAFT: duplicate vocabulary is stable; unknown/empty are data, not service errors', () => {
  assert.deepEqual(read('http/saveVocabulary-201.json').data, read('http/saveVocabulary-200.json').data);
  assert.equal(read('lexicon/not-found.json').status, 'not_found');
  assert.deepEqual(read('http/listHistory-200.json').data.items, []);
  assert.ok(read('http/request-timeout.json').error);
});
