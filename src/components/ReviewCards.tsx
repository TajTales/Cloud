import { useState } from "react";
import AppDialog from "./AppDialog";
type Word = { word: string; reading: string; meaning: string };
export default function ReviewCards({ words, title, onClose, onReview }: { words: Word[]; title: string; onClose: () => void; onReview?: (word: string, state: "learning" | "known") => Promise<void> }) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const current = words[index];
  const next = async (remembered: boolean) => { if (pending) return; setPending(true); setError(""); try { if (onReview) await onReview(current.word, remembered ? "known" : "learning"); setKnown(items => remembered ? [...new Set([...items, current.word])] : items.filter(word => word !== current.word)); setFlipped(false); if (index === words.length - 1) setDone(true); else setIndex(value => value + 1); } catch (reason) { setError(reason instanceof Error ? reason.message : "Chưa lưu được kết quả ôn tập."); } finally { setPending(false); } };
  return <AppDialog title={title} description={onReview ? "Kết quả được lưu sau mỗi thẻ để bạn tiếp tục ôn tập lần sau." : "Ôn tập nội dung mẫu; kết quả chưa lưu lên máy chủ."} onClose={onClose}>
    {error && <p className="app-inline-error" role="alert">{error}</p>}
    {!words.length ? <p className="app-notice">Bạn chưa lưu từ nào. Hãy chọn từ trong phần phiên âm để bắt đầu bộ từ của mình.</p> : done ? <div className="review-summary"><span>完</span><h3>Bạn đã đi hết bộ từ!</h3><p>Đã nhớ {known.length} / {words.length} từ trong lượt ôn này.</p><div className="app-dialog-actions"><button className="app-btn" onClick={onClose}>Kết thúc</button><button className="app-btn app-btn-primary" onClick={() => { setIndex(0); setKnown([]); setDone(false); setFlipped(false); }}>Ôn lại từ đầu</button></div></div> : <><div className="review-progress"><span>Từ {index + 1} / {words.length}</span><span>{known.length} từ đã nhớ</span></div><button className={`review-flashcard ${flipped ? "is-flipped" : ""}`} onClick={() => setFlipped(value => !value)} aria-label="Lật thẻ từ"><small>{flipped ? "NGHĨA VÀ CÁCH ĐỌC" : "BẠN CÒN NHỚ TỪ NÀY?"}</small><strong>{flipped ? current.meaning : current.word}</strong><span>{flipped ? `${current.word} · ${current.reading}` : "Bấm để xem mặt sau"}</span></button><div className="review-decisions"><button className="app-btn" disabled={pending} onClick={() => next(false)}>Cần ôn lại</button><button className="app-btn app-btn-primary" disabled={pending} onClick={() => next(true)}>Đã nhớ · Tiếp theo</button></div></>}
  </AppDialog>;
}
