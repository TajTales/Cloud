import { useEffect, useState, type RefObject } from "react";
import { containedRect, boxRect } from "../api/ocrGeometry";
import { learningClient as client, type OcrResult } from "../api/learning";
import "./OcrContent.css";

export function OcrOverlay({ result, videoRef }: { result: OcrResult | null; videoRef: RefObject<HTMLVideoElement | null> }) {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [mediaTime, setMediaTime] = useState(0);
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const update = () => { setSize({ width: video.clientWidth, height: video.clientHeight }); setMediaTime(video.currentTime * 1000); };
    const observer = new ResizeObserver(update); observer.observe(video); update();
    video.addEventListener("timeupdate", update); video.addEventListener("seeked", update);
    return () => { observer.disconnect(); video.removeEventListener("timeupdate", update); video.removeEventListener("seeked", update); };
  }, [videoRef, result?.result_id]);
  if (!result) return null;
  const content = containedRect(size.width, size.height, result.image.width_px, result.image.height_px);
  if (!content || (videoRef.current?.srcObject === null && Math.abs(mediaTime - result.media_time_ms) > 4000)) return null;
  return <div className="live-ocr-overlay" aria-label="Vị trí chữ nhận dạng">{result.ocr.paragraphs.map((paragraph, index) => <span key={index} title={paragraph.full_text} className="live-ocr-box" style={boxRect(paragraph.box, content)}><span>{paragraph.full_text}</span></span>)}</div>;
}

export function OcrTranscript({ results, pending }: { results: OcrResult[]; pending: boolean }) {
  const [selected, setSelected] = useState<string | null>(null);
  useEffect(() => setSelected(null), [results[0]?.source_id]);
  return <div className="live-ocr-transcript">
    <p className="transcript-lookup-hint">Văn bản đọc từ nguồn học của bạn. Cách đọc và bản dịch cần dữ liệu từ điển riêng.</p>
    {!results.length && <p className="app-muted">{pending ? "Đang chờ kết quả nhận dạng đầu tiên…" : "Bấm Nhận dạng chữ để bắt đầu."}</p>}
    <div className="transcript-list">{[...results].reverse().map(result => <article key={result.result_id}><time>{Math.floor(result.media_time_ms / 60000).toString().padStart(2, "0")}:{Math.floor(result.media_time_ms / 1000 % 60).toString().padStart(2, "0")}</time><div>{result.ocr.paragraphs.length ? result.ocr.paragraphs.map((paragraph, index) => <div key={index}><h3 lang={result.language}>{paragraph.words.length ? paragraph.words.map((word, i) => <button key={i} className="transcript-token" onClick={() => setSelected(word.text)} title={word.text}>{word.text}{word.separator}</button>) : paragraph.full_text}</h3><p className="app-muted">{paragraph.is_vertical ? "Chữ dọc" : "Chữ ngang"}</p></div>) : <p className="app-muted">Không tìm thấy chữ trong frame.</p>}</div></article>)}</div>
    {selected && <div className="app-notice" role="status"><strong lang="ja">{selected}</strong><p>Chưa có mục từ và cách đọc cho nội dung này.</p><button className="app-btn" onClick={() => setSelected(null)}>Đóng</button></div>}
  </div>;
}

export function OcrHistory({ sessionId }: { sessionId: string }) {
  const [results, setResults] = useState<OcrResult[]>([]);
  const [snapshot, setSnapshot] = useState<{ through: number; cursor: string | null } | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const session = await client.getSession(sessionId);
        const page = await client.resultPage(sessionId, session.latest_seq);
        const data = await Promise.all(page.items.map(item => client.getResult(item.result_id)));
        if (!cancelled) { setResults(data); setSnapshot({ through: page.through_seq, cursor: page.next_cursor }); }
      } catch (reason) { if (!cancelled) setError(reason instanceof Error ? reason.message : "Chưa tải được văn bản."); }
      finally { if (!cancelled) setBusy(false); }
    })();
    return () => { cancelled = true; };
  }, [sessionId]);
  return <section><h3>Văn bản đã nhận dạng</h3>{error && <p className="app-inline-error" role="alert">{error}</p>}{busy && <p className="app-muted">Đang tải văn bản…</p>}{results.length ? <OcrTranscript results={results} pending={false} /> : !busy && !error && <p className="app-muted">Phiên này chưa có kết quả OCR.</p>}{snapshot?.cursor && <button className="app-btn" disabled={busy} onClick={async () => { setBusy(true); setError(""); try { const page = await client.resultPage(sessionId, snapshot.through, snapshot.cursor!); const data = await Promise.all(page.items.map(item => client.getResult(item.result_id))); setResults(items => [...items, ...data]); setSnapshot({ through: page.through_seq, cursor: page.next_cursor }); } catch (reason) { setError(reason instanceof Error ? reason.message : "Chưa tải được văn bản."); } finally { setBusy(false); } }}>Xem thêm văn bản</button>}</section>;
}
