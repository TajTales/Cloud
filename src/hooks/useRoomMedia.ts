import { useEffect, useRef, useState } from "react";
export default function useRoomMedia(enabled: boolean) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const urlRef = useRef<string | null>(null);
  const generation = useRef(0);
  const active = useRef(enabled);
  const [source, setSource] = useState<"file" | "screen" | null>(null);
  const [sourceToken, setSourceToken] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const release = () => {
    streamRef.current?.getTracks().forEach(track => { track.onended = null; track.stop(); }); streamRef.current = null;
    if (urlRef.current) { URL.revokeObjectURL(urlRef.current); urlRef.current = null; }
    if (videoRef.current) { videoRef.current.pause(); videoRef.current.srcObject = null; videoRef.current.removeAttribute("src"); videoRef.current.load(); }
  };
  const stop = () => { generation.current++; release(); setSource(null); setSourceToken(""); setName(""); setPending(false); setError(""); };
  useEffect(() => { active.current = enabled; if (!enabled) stop(); return () => { active.current = false; generation.current++; release(); }; }, [enabled]);
  const share = async () => {
    if (!navigator.mediaDevices?.getDisplayMedia) { setError("Trình duyệt chưa hỗ trợ chia sẻ màn hình. Bạn có thể chọn video trên máy."); return false; }
    const request = ++generation.current;
    setError(""); setPending(true);
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
      if (!active.current || request !== generation.current) { stream.getTracks().forEach(track => track.stop()); return false; }
      release(); streamRef.current = stream; stream.getVideoTracks()[0].onended = stop;
      setSource("screen"); setSourceToken(crypto.randomUUID()); setName(stream.getVideoTracks()[0].label || "Màn hình đang chia sẻ");
      if (videoRef.current) { videoRef.current.srcObject = stream; void videoRef.current.play().catch(() => { if (active.current && request === generation.current) setError("Nguồn đã được chọn nhưng video chưa phát. Hãy thử chọn lại nguồn."); }); }
      return true;
    } catch (err) {
      if (active.current && request === generation.current) setError(err instanceof DOMException && err.name === "NotAllowedError" ? "Bạn chưa cho phép chia sẻ. Hãy thử lại hoặc mở một video." : "Chưa chia sẻ được màn hình. Hãy thử lại.");
      return false;
    } finally { if (active.current && request === generation.current) setPending(false); }
  };
  const openFile = (file?: File) => {
    if (!file) return;
    if (!file.type.startsWith("video/")) { setError("Vui lòng chọn tệp video MP4, WebM hoặc định dạng trình duyệt hỗ trợ."); return; }
    stop(); urlRef.current = URL.createObjectURL(file); setSource("file"); setSourceToken(crypto.randomUUID()); setName(file.name);
    if (videoRef.current) { videoRef.current.src = urlRef.current; videoRef.current.load(); }
  };
  return { source, sourceToken, name, error, pending, videoRef, fileRef, stop, share, openFile, onVideoError: () => { stop(); setError("Video này chưa phát được trên trình duyệt. Hãy chọn một tệp MP4 hoặc WebM khác."); } };
}
