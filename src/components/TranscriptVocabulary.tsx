import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { tokenizeTranscript, type VocabularyEntry } from "../data/transcriptVocabulary";
import "./TranscriptVocabulary.css";
import YomitanEntry from "./YomitanEntry";

type TranscriptLine = { time: string; japanese: string; reading: string; translation: string };
type Props = {
  lines: TranscriptLine[];
  savedWords: string[];
  onSave: (entry: VocabularyEntry) => void;
  onSpeak: (word: string, rate?: number) => void;
};
type ActiveWord = { entry: VocabularyEntry; anchor: HTMLButtonElement; tokenId: string };

export default function TranscriptVocabulary({ lines, savedWords, onSave, onSpeak }: Props) {
  const id = useId();
  const popupId = `${id}-word-popup`;
  const [active, setActive] = useState<ActiveWord | null>(null);
  const [pinned, setPinned] = useState(false);
  const [position, setPosition] = useState<{ left: number; top: number } | null>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<ActiveWord | null>(null);
  const pinnedRef = useRef(false);
  const hoverRef = useRef(false);
  const suppressFocusRef = useRef(false);
  const openTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cancelTimers = () => {
    if (openTimer.current) clearTimeout(openTimer.current);
    if (closeTimer.current) clearTimeout(closeTimer.current);
    openTimer.current = closeTimer.current = null;
  };
  const dismiss = (restoreFocus = false) => {
    cancelTimers();
    const anchor = activeRef.current?.anchor;
    activeRef.current = null;
    pinnedRef.current = false;
    hoverRef.current = false;
    setActive(null); setPinned(false); setPosition(null);
    if (restoreFocus && anchor?.isConnected) {
      suppressFocusRef.current = true;
      anchor.focus({ preventScroll: true });
      suppressFocusRef.current = false;
    }
  };
  const open = (word: ActiveWord, pin = false) => {
    cancelTimers();
    activeRef.current = word;
    pinnedRef.current = pin;
    setActive(word); setPinned(pin);
  };
  const leave = () => {
    if (openTimer.current) clearTimeout(openTimer.current);
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = setTimeout(() => {
      if (!pinnedRef.current && !hoverRef.current && document.activeElement !== activeRef.current?.anchor && !popupRef.current?.contains(document.activeElement)) dismiss();
    }, 240);
  };

  useEffect(() => {
    const outside = (event: PointerEvent) => {
      if (!(event.target instanceof Node)) return;
      if (!popupRef.current?.contains(event.target) && !activeRef.current?.anchor.contains(event.target)) dismiss();
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && activeRef.current) { event.preventDefault(); dismiss(pinnedRef.current || !!popupRef.current?.contains(document.activeElement)); }
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      cancelTimers();
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, []);

  useLayoutEffect(() => {
    if (!active) return;
    const reposition = () => {
      const anchor = active.anchor.getBoundingClientRect();
      const list = active.anchor.closest(".transcript-list")?.getBoundingClientRect();
      if (!active.anchor.isConnected || anchor.bottom < Math.max(0, list?.top ?? 0) || anchor.top > Math.min(window.innerHeight, list?.bottom ?? window.innerHeight)) { dismiss(); return; }
      const popup = popupRef.current;
      if (!popup) return;
      const { width, height } = popup.getBoundingClientRect();
      const gap = 10, padding = 12;
      const left = Math.max(padding, Math.min(anchor.left + anchor.width / 2 - width / 2, window.innerWidth - width - padding));
      const below = anchor.bottom + gap;
      const top = below + height <= window.innerHeight - padding ? below : Math.max(padding, Math.min(anchor.top - height - gap, window.innerHeight - height - padding));
      setPosition({ left, top });
    };
    reposition();
    window.addEventListener("resize", reposition);
    window.addEventListener("scroll", reposition, true);
    const observer = new ResizeObserver(reposition);
    if (popupRef.current) observer.observe(popupRef.current);
    return () => { observer.disconnect(); window.removeEventListener("resize", reposition); window.removeEventListener("scroll", reposition, true); };
  }, [active]);

  const renderWords = (text: string, lineIndex: number, romanized = false) => tokenizeTranscript(text, romanized).map((token, index) => {
    if (!token.entry) return token.text;
    const tokenId = `${id}-${lineIndex}-${romanized ? "reading" : "original"}-${index}`;
    const entry = token.entry;
    const expanded = active?.tokenId === tokenId;
    return <button key={tokenId} type="button" className={`transcript-token ${expanded ? "is-active" : ""}`} lang={romanized ? undefined : "ja"}
      aria-label={`Tra từ ${token.text}`} aria-haspopup="dialog" aria-expanded={expanded} aria-controls={expanded ? popupId : undefined}
      onPointerEnter={event => {
        if (event.pointerType !== "mouse" || pinnedRef.current) return;
        cancelTimers(); hoverRef.current = false;
        const anchor = event.currentTarget;
        openTimer.current = setTimeout(() => open({ entry, anchor, tokenId }), 130);
      }}
      onPointerLeave={leave}
      onFocus={event => { if (!suppressFocusRef.current) open({ entry, anchor: event.currentTarget, tokenId }); }}
      onBlur={event => { if (!popupRef.current?.contains(event.relatedTarget as Node | null)) leave(); }}
      onClick={event => {
        if (pinnedRef.current && activeRef.current?.tokenId === tokenId) dismiss();
        else open({ entry, anchor: event.currentTarget, tokenId }, true);
      }}
      onKeyDown={event => {
        if (event.key === "ArrowDown") {
          event.preventDefault(); open({ entry, anchor: event.currentTarget, tokenId }, true);
          requestAnimationFrame(() => popupRef.current?.querySelector<HTMLButtonElement>("button")?.focus());
        }
      }}
    >{token.text}</button>;
  });

  const entry = active?.entry;
  const isSaved = !!entry && savedWords.includes(entry.lemma || entry.word);
  return <>
    <p className="transcript-lookup-hint">Rê chuột hoặc chạm vào từ để xem nghĩa và cách dùng.</p>
    <div className="transcript-list">
      {lines.map((line, index) => <article className={index === 0 ? "current" : ""} key={line.time}>
        <time>{line.time}</time><div>
          <h3 lang="ja">{renderWords(line.japanese, index)}</h3>
          <p className="transcript-reading">{renderWords(line.reading, index, true)}</p>
          <span>{line.translation}</span>
        </div>
      </article>)}
    </div>
    {entry && createPortal(<div ref={popupRef} id={popupId} role="dialog" aria-modal="false" aria-label={`Thông tin từ ${entry.word}`} className="vocabulary-popover yomitan-popover"
      style={{ left: position?.left ?? 0, top: position?.top ?? 0, visibility: position ? "visible" : "hidden" }}
      onPointerEnter={() => { hoverRef.current = true; cancelTimers(); }}
      onPointerLeave={() => { hoverRef.current = false; leave(); }}
      onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget as Node | null) && event.relatedTarget !== activeRef.current?.anchor) dismiss(); }}>
      <div className="vocabulary-popover-top"><span className="yomitan-title">Yomitan <span>· LinguaLive</span></span><button type="button" aria-label="Đóng bảng tra từ" onClick={() => dismiss(true)}><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg></button></div>
      <YomitanEntry entry={entry} isSaved={isSaved} onSave={onSave} onSpeak={onSpeak} />
      <p className="yomitan-reading-line"><span lang="ja">{entry.kana}</span><span>{entry.romaji}</span></p>
      {entry.lemma && <p className="yomitan-context">Trong câu: <strong lang="ja">{entry.word}</strong></p>}
      <section className="yomitan-usage"><h3>CÁCH DÙNG</h3><p className="vocabulary-usage">{entry.usage}</p></section>
      <div className="vocabulary-example"><span>VÍ DỤ</span><p lang="ja">{entry.example}</p><small>{entry.exampleTranslation}</small></div>
      <p className="yomitan-source">Nguồn nghĩa: LinguaLive · dữ liệu mẫu.</p>
      <div className="yomitan-attribution"><a href="https://github.com/yomidevs/yomitan" target="_blank" rel="noopener noreferrer">Mã nguồn Yomitan ↗</a><a href={`${import.meta.env.BASE_URL}licenses/yomitan-GPL-3.0.txt`} target="_blank" rel="noopener noreferrer">GPL-3.0-or-later</a></div>
      <p className="vocabulary-footnote">{pinned ? "Đang giữ bảng · Nhấn Esc hoặc bấm bên ngoài để đóng." : "Bấm vào từ để giữ bảng mở."}</p>
    </div>, document.body)}
  </>;
}
