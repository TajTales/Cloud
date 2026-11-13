import type { SavedWord } from "../api/learning";
import "./SavedVocabulary.css";

type Props = {
  words: SavedWord[];
  pending: boolean;
  onReview: () => void;
  onDelete: (word: string) => void;
  onSpeak: (word: string) => void;
};

const reviewLabels = { new: "Mới lưu", learning: "Đang ôn", known: "Đã nhớ" };

export default function SavedVocabulary({ words, pending, onReview, onDelete, onSpeak }: Props) {
  const canSpeak = typeof window !== "undefined" && "speechSynthesis" in window;

  return (
    <section className="saved-vocabulary" aria-labelledby="saved-vocabulary-title">
      <header className="saved-vocabulary-header">
        <div>
          <div className="saved-vocabulary-heading">
            <h2 id="saved-vocabulary-title">Từ đã lưu</h2>
            <span className="saved-vocabulary-count">{words.length} từ</span>
          </div>
          <p>Xem lại cách đọc, ý nghĩa và những từ bạn đang ôn tập.</p>
        </div>
        <button className="app-btn" type="button" onClick={onReview} disabled={pending || !words.length}>
          Ôn tập từ đã lưu <span aria-hidden="true">↗</span>
        </button>
      </header>

      {!words.length ? (
        <div className="saved-vocabulary-empty">
          <strong>Bộ từ của bạn đang chờ những khám phá mới</strong>
          <p>Chọn một từ trong phần phiên âm và lưu lại để bắt đầu ôn tập.</p>
        </div>
      ) : (
        <div className="saved-vocabulary-list">
          {words.map(word => (
            <article className="saved-vocabulary-row" key={word.word_id}>
              <div className="saved-vocabulary-term">
                <strong lang={word.language}>{word.lemma}</strong>
                <span lang={word.language}>{word.reading?.kana || word.reading?.pinyin || word.reading?.romaji || "Chưa có cách đọc"}</span>
              </div>
              <div className="saved-vocabulary-meaning">
                <p>{word.meanings.map(meaning => meaning.text).join("; ")}</p>
                {word.meanings.some(meaning => meaning.origin === "fixture") && <small>Nội dung mẫu</small>}
              </div>
              <div className="saved-vocabulary-meta">
                <span className="saved-vocabulary-status" data-state={word.review_state}>{reviewLabels[word.review_state]}</span>
                <div className="saved-vocabulary-actions">
                  <button type="button" onClick={() => onSpeak(word.lemma)} disabled={!canSpeak} aria-label={`Nghe ${word.lemma}`}>
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m11 5-5 4H3v6h3l5 4zM15 9a4 4 0 0 1 0 6M18 6a8 8 0 0 1 0 12" /></svg>
                    Nghe
                  </button>
                  <button className="saved-vocabulary-delete" type="button" onClick={() => onDelete(word.lemma)} disabled={pending} aria-label={`Xóa ${word.lemma}`}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" aria-hidden="true"><path d="M5 7h14M9 7V4h6v3M7 7l1 13h8l1-13M10 11v5M14 11v5" /></svg>
                    Xóa
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
