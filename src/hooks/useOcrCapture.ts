import { useEffect, useRef, useState, type RefObject } from "react";
import { ApiFailure, learningClient as client, type OcrResult, type StudySession } from "../api/learning";
import { captureSize } from "../api/ocrGeometry";

function pause(ms: number, signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal.aborted) { reject(new DOMException("Aborted", "AbortError")); return; }
    const abort = () => { clearTimeout(timer); reject(new DOMException("Aborted", "AbortError")); };
    const timer = setTimeout(() => { signal.removeEventListener("abort", abort); resolve(); }, ms);
    signal.addEventListener("abort", abort, { once: true });
  });
}

async function capture(video: HTMLVideoElement) {
  const size = captureSize(video.videoWidth, video.videoHeight);
  const canvas = document.createElement("canvas");
  canvas.width = size.width; canvas.height = size.height;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Trình duyệt chưa hỗ trợ chụp frame.");
  context.drawImage(video, 0, 0, size.width, size.height);
  let blob: Blob | null = null;
  for (const quality of [.8, .6, .4]) {
    blob = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, "image/jpeg", quality));
    if (blob && blob.size <= 1048576) return { blob, width: size.width, height: size.height };
  }
  throw new Error("Frame quá lớn. Hãy thử video có độ phân giải thấp hơn.");
}

type Props = { enabled: boolean; session: StudySession | null; source: "file" | "screen" | null; sourceToken: string; videoRef: RefObject<HTMLVideoElement | null>; onAuthError: () => void };
export default function useOcrCapture({ enabled, session, source, sourceToken, videoRef, onAuthError }: Props) {
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState("Sẵn sàng nhận dạng");
  const [error, setError] = useState("");
  const [results, setResults] = useState<OcrResult[]>([]);
  const [result, setResult] = useState<OcrResult | null>(null);
  const [sourceId, setSourceId] = useState<string | null>(null);
  const inFlight = useRef(false);
  const registration = useRef<{ token: string; sessionId: string; sourceId: string; nextFrame: number; width: number; height: number; clockOrigin: number } | null>(null);
  const stopRef = useRef<AbortController | null>(null);
  const onAuthErrorRef = useRef(onAuthError); onAuthErrorRef.current = onAuthError;

  useEffect(() => {
    stopRef.current?.abort(); setRunning(false); setResult(null); setResults([]); setError(""); setSourceId(null);
    registration.current = null;
    setStatus(source ? "Sẵn sàng nhận dạng" : "Chọn nguồn học để bắt đầu");
  }, [enabled, sourceToken, session?.session_id]);

  useEffect(() => {
    if (!enabled || !running || !session || !source || !sourceToken) return;
    const controller = new AbortController(), signal = controller.signal;
    let ownsSlot = false;
    stopRef.current = controller;
    let lastMediaTime = -1;
    void (async () => {
      try {
        while (inFlight.current && !signal.aborted) await pause(50, signal);
        if (signal.aborted) return;
        inFlight.current = true;
        ownsSlot = true;
        const video = videoRef.current;
        if (!video) throw new Error("Chưa tìm thấy video.");
        for (let attempt = 0; video.readyState < 2 || !video.videoWidth; attempt++) {
          if (attempt >= 100) throw new Error("Video chưa sẵn sàng. Hãy phát video rồi thử lại.");
          await pause(100, signal);
        }
        setStatus("Đang chuẩn bị nguồn học…");
        const current = await client.getSession(session.session_id);
        if (signal.aborted) return;
        const cached = registration.current;
        if (!cached || cached.token !== sourceToken || cached.sessionId !== session.session_id || cached.sourceId !== current.current_source_id || cached.width !== video.videoWidth || cached.height !== video.videoHeight) {
          const source = await client.registerSource(session.session_id, {
            source_id: crypto.randomUUID(), kind: video.srcObject ? "screen_share" : "local_video",
            width_px: video.videoWidth, height_px: video.videoHeight, duration_ms: video.srcObject || !Number.isFinite(video.duration) ? null : Math.round(video.duration * 1000), expected_version: current.version,
          }, crypto.randomUUID(), signal);
          registration.current = { token: sourceToken, sessionId: session.session_id, sourceId: source.source_id, nextFrame: 0, width: video.videoWidth, height: video.videoHeight, clockOrigin: performance.now() };
          setResult(null); setResults([]);
        }
        const registered = registration.current!;
        if (signal.aborted) return;
        setSourceId(registered.sourceId);
        while (!signal.aborted) {
          if (registered.width !== video.videoWidth || registered.height !== video.videoHeight) throw new Error("Độ phân giải nguồn đã thay đổi. Bấm Nhận dạng chữ để tiếp tục với nguồn mới.");
          if (video.ended) { setStatus("Video đã kết thúc"); setRunning(false); break; }
          if (video.readyState < 2 || (source === "file" && Math.abs(video.currentTime - lastMediaTime) < .05)) { await pause(500, signal); continue; }
          const captured = await capture(video);
          if (signal.aborted) return;
          const mediaTime = source === "screen" ? Math.round((performance.now() - registered.clockOrigin)) : Math.round(video.currentTime * 1000);
          lastMediaTime = video.currentTime;
          setStatus("Đang nhận dạng chữ…");
          try {
            const upload = await client.createUpload(session.session_id, { source_id: registered.sourceId, frame_id: crypto.randomUUID(), frame_index: registered.nextFrame++,
              media_time_ms: mediaTime, captured_at: new Date().toISOString(), width_px: captured.width, height_px: captured.height,
              content_type: captured.blob.type, size_bytes: captured.blob.size }, crypto.randomUUID(), signal);
            await client.putFrame(upload, captured.blob, signal);
            let job = await client.createJob(session.session_id, upload, crypto.randomUUID(), signal);
            const deadline = performance.now() + 70000;
            while (job.status === "queued" || job.status === "processing") {
              if (performance.now() > deadline) throw new Error("Job nhận dạng quá thời gian. Hãy thử lại.");
              await pause(Math.max(250, job.poll_after_ms || 500), signal);
              job = await client.getJob(job.job_id, signal);
            }
            if (!job.result_id || job.status !== "succeeded") throw new ApiFailure(job.error?.message || "Chưa nhận dạng được frame.", 503, job.error?.code || "REQUEST_FAILED");
            const next = await client.getResult(job.result_id, signal);
            if (signal.aborted) return;
            if (next.session_id !== session.session_id || next.source_id !== registered.sourceId || next.frame_id !== upload.frame_id || next.job_id !== job.job_id) throw new Error("Kết quả nhận dạng không khớp nguồn hiện tại.");
            setResult(previous => previous && previous.frame_index >= next.frame_index ? previous : next);
            setResults(items => [...items.filter(item => item.result_id !== next.result_id), next].slice(-50));
            setStatus(next.ocr.paragraphs.length ? "Đã nhận dạng" : "Không tìm thấy chữ trong frame");
          } catch (reason) {
            if (signal.aborted) return;
            if (reason instanceof ApiFailure && reason.status === 429) { setStatus("Đang chờ frame trước hoàn tất…"); lastMediaTime = -1; await pause(2000, signal); continue; }
            throw reason;
          }
          await pause(2000, signal);
        }
      } catch (reason) {
        if (signal.aborted) return;
        setError(reason instanceof Error ? reason.message : "Chưa nhận dạng được video."); setStatus("Nhận dạng đã dừng"); setRunning(false); setResult(null);
        if (reason instanceof ApiFailure && (reason.status === 401 || reason.details.account_status)) onAuthErrorRef.current();
      } finally { if (ownsSlot) inFlight.current = false; }
    })();
    return () => { controller.abort(); };
  }, [enabled, running, session?.session_id, source, sourceToken, videoRef]);

  return { running, status, error, result, results, sourceId,
    start: () => { if (!enabled || !session || !source) return; setError(""); setRunning(true); },
    stop: () => { stopRef.current?.abort(); setRunning(false); setStatus("Đã dừng nhận dạng"); },
  };
}
