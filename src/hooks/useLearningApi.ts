import { useEffect, useRef, useState } from "react";
import { ApiFailure, learningClient as client, type ApiProfile, type SavedWord, type StudySession, type HistoryItem, type Stats } from "../api/learning";

export default function useLearningApi(enabled: boolean) {
  const [profile, setProfile] = useState<ApiProfile | null>(null);
  const [words, setWords] = useState<SavedWord[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [active, setActive] = useState<StudySession | null>(null);
  const [busy, setBusy] = useState(0);
  const [restoring, setRestoring] = useState(enabled);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const generation = useRef(0);
  const lock = useRef(false);
  async function refresh() {
    const epoch = generation.current;
    const [nextProfile, nextWords, nextHistory, nextStats] = await Promise.all([client.me(), client.words(), client.history(), client.stats()]);
    if (epoch !== generation.current) return;
    setProfile(nextProfile); setWords(nextWords); setHistory(nextHistory); setStats(nextStats); setUpdatedAt(new Date().toISOString());
  }
  async function run<T>(work: () => Promise<T>): Promise<T> {
    if (lock.current) throw new Error("Đang xử lý thao tác trước, vui lòng chờ.");
    lock.current = true; setBusy(value => value + 1); setError("");
    try { return await work(); }
    catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thực hiện được yêu cầu.");
      if (reason instanceof ApiFailure && (reason.status === 401 || (reason.status === 403 && reason.details.account_status))) { client.clearToken(); setProfile(null); setWords([]); setHistory([]); setStats(null); setActive(null); generation.current++; }
      throw reason;
    } finally { lock.current = false; setBusy(value => value - 1); }
  }
  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    void (async () => {
      try { const restored = await client.authenticate("session"); if (cancelled) return; setProfile(restored); await refresh(); }
      catch (reason) { if (!cancelled && (!(reason instanceof ApiFailure) || reason.status !== 401)) setError(reason instanceof Error ? reason.message : "Chưa kết nối API local."); }
      finally { if (!cancelled) setRestoring(false); }
    })();
    return () => { cancelled = true; generation.current++; };
  }, [enabled]);
  return {
    profile, words, history, stats, active, updatedAt, busy: busy > 0 || restoring, restoring, error, setError,
    refresh: () => run(refresh),
    login: (email: string, password: string) => run(async () => { setProfile(await client.authenticate("login", { email, password })); await refresh(); }),
    register: (display_name: string, email: string, password: string) => run(async () => { setProfile(await client.authenticate("register", { display_name, email, password })); await refresh(); }),
    authAction: (action: string, body: unknown = {}) => run(async () => {
      const result = await client.authAction<{ signed_out?: boolean; accepted?: boolean; delivery_mode?: string }>(action, body);
      if (result.signed_out) { client.clearToken(); setProfile(null); setWords([]); setHistory([]); setStats(null); setActive(null); generation.current++; }
      else if (action === "verification/confirm") await refresh();
      return result;
    }),
    updateProfile: (body: unknown) => run(async () => { setProfile(await client.updateProfile(body)); }),
    saveWord: (word: string) => run(async () => { await client.saveWord(word); await refresh(); }),
    deleteWord: (word: string) => run(async () => { const record = words.find(item => item.lemma === word); if (record) await client.deleteWord(record.word_id); await refresh(); }),
    reviewWord: (word: string, state: "learning" | "known") => run(async () => { const record = words.find(item => item.lemma === word); if (!record) throw new Error("Không tìm thấy từ đã lưu."); const updated = await client.reviewWord(record, state); setWords(items => items.map(item => item.word_id === updated.word_id ? updated : item)); }),
    startSession: (title: string, language: string) => run(async () => { const session = await client.createSession(title, language); setActive(session); return session; }),
    resumeSession: (id: string) => run(async () => { const session = await client.getSession(id); if (session.status !== "active") throw new Error("Phiên đã kết thúc. Hãy bắt đầu buổi học mới."); setActive(session); return session; }),
    endSession: () => run(async () => { if (active) await client.endSession(active); setActive(null); await refresh(); }),
    logout: () => run(async () => { if (active) { try { await client.endSession(active); } catch { /* Session history can stay active; sign-out must still be attempted. */ } } await client.logout(); generation.current++; setActive(null); setProfile(null); setWords([]); setHistory([]); setStats(null); }),
  };
}
