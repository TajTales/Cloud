// SPDX-License-Identifier: GPL-3.0-or-later
// LinguaLive adapter for Yomitan's actual DisplayGenerator and term-entry templates.
import { useEffect, useRef, useState } from "react";
import { DisplayGenerator } from "../../third_party/yomitan/js/display/display-generator.js";
import templatesHtml from "../../third_party/yomitan/templates-display.html?raw";
import type { VocabularyEntry } from "../data/transcriptVocabulary";
import "./YomitanEntry.css";

let generatorPromise: Promise<DisplayGenerator> | null = null;
function getGenerator() {
  if (!generatorPromise) {
    const generator = new DisplayGenerator(null, null);
    generatorPromise = generator.prepare(templatesHtml).then(() => generator).catch(error => { generatorPromise = null; throw error; });
  }
  return generatorPromise;
}

export function toYomitanEntry(entry: VocabularyEntry) {
  const dictionary = "LinguaLive Demo";
  const term = entry.lemma || entry.word;
  const reading = entry.lemmaReading || entry.kana;
  const tag = { name: entry.partOfSpeech, category: "partOfSpeech", order: 0, score: 0, content: [entry.partOfSpeech], dictionaries: [dictionary], redundant: false };
  return {
    type: "term", isPrimary: true, textProcessorRuleChainCandidates: [],
    inflectionRuleChainCandidates: entry.lemma && entry.lemma !== entry.word ? [{ source: "dictionary", inflectionRules: [{ name: `${entry.word} → ${entry.lemma}`, description: "Dạng gốc theo dữ liệu mẫu LinguaLive" }] }] : [],
    score: 0, frequencyOrder: 0, dictionaryIndex: 0, dictionaryAlias: "LinguaLive · Mẫu",
    sourceTermExactMatchCount: 1, matchPrimaryReading: true, maxOriginalTextLength: entry.word.length,
    headwords: [{ index: 0, headwordIndex: 0, term, reading, tags: [], wordClasses: [], sources: [{ matchType: "exact", matchSource: "term", isPrimary: true }] }],
    definitions: [{ index: 0, headwordIndices: [0], dictionary, dictionaryAlias: "LinguaLive · Mẫu", id: 0, score: 0, frequencyOrder: 0, sequences: [-1], isPrimary: true, tags: [tag], entries: [entry.lemmaMeaning || entry.meaning] }],
    frequencies: [], pronunciations: [],
  };
}

const speakerSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4zM15 9a4 4 0 0 1 0 6M18 6a8 8 0 0 1 0 12"/></svg>';
const saveSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';

type Props = { entry: VocabularyEntry; isSaved: boolean; onSave: (entry: VocabularyEntry) => void; onSpeak: (word: string, rate?: number) => void };
export default function YomitanEntry({ entry, isSaved, onSave, onSpeak }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const saveRef = useRef<HTMLButtonElement | null>(null);
  const callbacks = useRef({ isSaved, onSave, onSpeak });
  callbacks.current = { isSaved, onSave, onSpeak };
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    let cancelled = false;
    const root = rootRef.current;
    setState("loading");
    saveRef.current = null;
    root?.replaceChildren();
    getGenerator().then(generator => {
      if (cancelled || !root) return;
      // Only text glossary entries are passed to the extension renderer. No untrusted HTML/media.
      const node = generator.createTermEntry(toYomitanEntry(entry), [{ title: "LinguaLive Demo", revision: "1", author: "LinguaLive", description: "Dữ liệu mẫu của giao diện, chưa kết nối từ điển trực tuyến." }]);
      node.dataset.renderer = "yomitan";
      node.querySelectorAll('.entry-current-indicator, .entry-current-indicator-icon, .headword-details, .expansion-button, .tag[data-category="search"], [data-action="menu"]').forEach(element => element.remove());
      node.querySelectorAll('.entry-body-section[data-section-type="frequencies"], .entry-body-section[data-section-type="pronunciations"]').forEach(element => element.remove());
      // Kanji navigation belongs to the extension's database. Keep readable text rather than dead links.
      node.querySelectorAll("a.headword-kanji-link").forEach(link => { const span = document.createElement("span"); span.textContent = link.textContent; link.replaceWith(span); });
      const heading = node.querySelector<HTMLElement>(".headword");
      heading?.setAttribute("role", "heading"); heading?.setAttribute("aria-level", "2");
      node.querySelectorAll<HTMLElement>('.tag[data-category="partOfSpeech"]').forEach(tag => tag.classList.add("vocabulary-pos"));
      const audio = node.querySelector<HTMLButtonElement>('[data-action="play-audio"]');
      if (audio) {
        audio.innerHTML = speakerSvg;
        audio.title = "Nghe phát âm"; audio.setAttribute("aria-label", `Nghe phát âm ${entry.word}`);
        audio.disabled = !("speechSynthesis" in window);
        audio.addEventListener("click", () => callbacks.current.onSpeak(entry.word));
      }
      const actionButtons = node.querySelector(".action-button-container");
      const slow = document.createElement("button"); slow.type = "button"; slow.className = "action-button slow-audio"; slow.textContent = "0.6×";
      slow.title = "Nghe chậm"; slow.setAttribute("aria-label", `Nghe chậm ${entry.word}`); slow.disabled = !("speechSynthesis" in window);
      slow.addEventListener("click", () => callbacks.current.onSpeak(entry.word, .6));
      actionButtons?.appendChild(slow);
      const save = document.createElement("button"); save.type = "button"; save.className = "action-button yomitan-save";
      const updateSave = () => { const saved = callbacks.current.isSaved; save.setAttribute("aria-disabled", String(saved)); save.setAttribute("aria-label", saved ? "Đã lưu từ" : "Lưu từ"); save.title = saved ? "Đã lưu từ" : "Lưu từ"; save.innerHTML = saved ? '<span aria-hidden="true">✓</span>' : saveSvg; };
      updateSave(); saveRef.current = save;
      save.addEventListener("click", () => { if (!callbacks.current.isSaved) callbacks.current.onSave(entry); });
      node.querySelector(".note-actions-container")?.appendChild(save);
      root.replaceChildren(node);
      setState("ready");
    }).catch(error => {
      if (cancelled) return;
      console.error("Yomitan popup renderer:", error);
      setState("error");
    });
    return () => { cancelled = true; saveRef.current = null; root?.replaceChildren(); };
  }, [entry]);

  useEffect(() => {
    const save = saveRef.current;
    if (!save) return;
    save.setAttribute("aria-disabled", String(isSaved));
    save.setAttribute("aria-label", isSaved ? "Đã lưu từ" : "Lưu từ");
    save.title = isSaved ? "Đã lưu từ" : "Lưu từ";
    save.innerHTML = isSaved ? '<span aria-hidden="true">✓</span>' : saveSvg;
  }, [isSaved]);

  return <div className="yomitan-renderer" data-state={state}>
    {state === "loading" && <p className="yomitan-render-state" role="status">Đang mở mục từ…</p>}
    {state === "error" && <p className="yomitan-render-state" role="alert">Chưa dựng được mục từ Yomitan. Hãy đóng và mở lại.</p>}
    <div ref={rootRef} className="yomitan-entry-root" />
  </div>;
}
