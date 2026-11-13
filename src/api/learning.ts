export const REAL_API = import.meta.env.VITE_API_MODE !== "preview";
export type ApiProfile = { user_id: string; display_name: string; email: string; email_verified: boolean; roles: string[]; permissions: string[]; status: string; locale: "vi" | "en"; timezone: string; learning_language: string; version: number };
export type SavedWord = { word_id: string; lemma: string; entry_id: string; sense_id: string; language: string; reading: { kana: string | null; romaji: string | null; pinyin: string | null } | null; meanings: { text: string; language: string; origin: string }[]; review_state: "new" | "learning" | "known"; version: number; created_at: string };
export type StudySession = { session_id: string; title: string; language: string; status: string; version: number; started_at: string; ended_at: string | null; current_source_id: string | null; latest_seq: number };
export type OcrSource = { source_id: string; session_id: string; source_index: number; session_version: number };
export type FrameMetadata = { source_id: string; frame_id: string; frame_index: number; media_time_ms: number; captured_at: string; width_px: number; height_px: number; content_type: string; size_bytes: number };
export type FrameUpload = { upload_id: string; source_id: string; frame_id: string; upload: { method: "PUT"; url: string; headers: Record<string, string>; expires_at: string } };
export type OcrJob = { job_id: string; session_id: string; source_id: string; frame_id: string; frame_index: number; media_time_ms: number; status: "queued" | "processing" | "succeeded" | "failed" | "expired"; result_id: string | null; poll_after_ms: number | null; error: { code: string; message: string; retryable: boolean } | null };
export type OcrBox = { center_x: number; center_y: number; width: number; height: number };
export type OcrResult = { result_id: string; job_id: string; session_id: string; source_id: string; frame_id: string; frame_index: number; media_time_ms: number; seq: number; created_at: string; language: string; provider: string; image: { width_px: number; height_px: number }; ocr: { elapsed_ms: number; paragraphs: { full_text: string; is_vertical: boolean; box: OcrBox; words: { text: string; separator: string; box: OcrBox }[] }[] } };
export type HistoryItem = { session_id: string; title: string; mode: string; language: string; started_at: string; ended_at: string | null; duration_ms: number | null; saved_words_count: number | null; playback_state: string };
export type Stats = { study_duration_ms: number | null; saved_words_count: number | null; streak_days: number | null; weekly_sessions: number | null };
type AuthData = { access_token: string; profile: ApiProfile; auth_provider: "local_password"; expires_at_s: number };
type Page<T> = { items: T[]; next_cursor: string | null };

export class ApiFailure extends Error {
  constructor(message: string, public status: number, public code: string, public details: Record<string, unknown> = {}) { super(message); }
}

class LearningClient {
  private token: string | null = null;
  private expiresAt = 0;
  private refreshing: Promise<ApiProfile> | null = null;
  private authGeneration = 0;
  private subject: string | null = null;
  private async withCookieLock<T>(work: () => Promise<T>): Promise<T> {
    if (typeof navigator !== "undefined" && navigator.locks) return await navigator.locks.request("lingualive-local-auth-cookie", work);
    return await work();
  }
  private base = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(/\/$/, "");
  private async request<T>(path: string, method = "GET", body?: unknown, key?: string, localAuth = false, retry = true, signal?: AbortSignal): Promise<T> {
    const requiresAccess = !localAuth || /^(verification|email|password\/change|logout-all|admin)/.test(path);
    if (requiresAccess && this.token && Date.now() / 1000 >= this.expiresAt - 30 && retry) await this.renew();
    const sentToken = this.token;
    const headers: Record<string, string> = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (localAuth) headers["X-Local-Client"] = "browser";
    if (requiresAccess && this.token) headers.Authorization = `Bearer ${this.token}`;
    if (key) headers["Idempotency-Key"] = key;
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (signal?.aborted) controller.abort();
    signal?.addEventListener("abort", abort, { once: true });
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(localAuth ? `/local-auth/${path}` : `${this.base}${path}`, { method, headers, credentials: "same-origin", signal: controller.signal, body: body === undefined ? undefined : JSON.stringify(body) });
      if (response.status === 204) return undefined as T;
      let envelope;
      try { envelope = await response.json(); }
      catch { throw new ApiFailure("API local chưa phản hồi đúng. Hãy kiểm tra dịch vụ ở cổng 8081.", response.status, "CONNECTION_ERROR"); }
      if (!response.ok) {
        if (response.status === 401 && requiresAccess && sentToken && retry && envelope.error?.code === "TOKEN_EXPIRED") {
          if (sentToken === this.token) await this.renew();
          return this.request<T>(path, method, body, key, localAuth, false, signal);
        }
        throw new ApiFailure(envelope.error?.message || "Không thực hiện được yêu cầu.", response.status, envelope.error?.code || "REQUEST_FAILED", envelope.error?.details || {});
      }
      if (!("data" in envelope)) throw new ApiFailure("Phản hồi API không đúng contract.", 502, "INVALID_RESPONSE");
      return envelope.data as T;
    } catch (error) {
      if (error instanceof ApiFailure) throw error;
      throw new ApiFailure("Mất kết nối API local. Thao tác có thể đã được lưu; hãy tải lại dữ liệu trước khi thử lại.", 0, "CONNECTION_ERROR");
    } finally { window.clearTimeout(timeout); signal?.removeEventListener("abort", abort); }
  }
  private async pages<T>(path: string): Promise<T[]> {
    const items: T[] = [];
    let cursor: string | null = null;
    for (let page = 0; page < 200; page++) {
      const data: Page<T> = await this.request(`${path}?limit=100${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`);
      items.push(...data.items); cursor = data.next_cursor;
      if (!cursor) return items;
    }
    throw new ApiFailure("Dữ liệu vượt giới hạn tải local.", 503, "PAGE_LIMIT");
  }
  async authenticate(action: "login" | "register" | "session", body?: unknown) {
    if (action === "session") return this.renew();
    const data = await this.withCookieLock(() => this.request<AuthData>(action, "POST", body, undefined, true));
    this.token = data.access_token; this.expiresAt = data.expires_at_s; this.subject = data.profile.user_id; return data.profile;
  }
  private renew(): Promise<ApiProfile> {
    if (this.refreshing) return this.refreshing;
    const generation = this.authGeneration;
    this.refreshing = this.withCookieLock(() => this.request<AuthData>("refresh", "POST", {}, undefined, true, false)).then(data => {
      if (generation !== this.authGeneration) throw new ApiFailure("Phiên đăng nhập đã thay đổi.", 401, "TOKEN_EXPIRED");
      if (this.subject && this.subject !== data.profile.user_id) throw new ApiFailure("Tài khoản ở tab khác đã thay đổi. Vui lòng tải lại trang.", 401, "TOKEN_EXPIRED");
      this.token = data.access_token; this.expiresAt = data.expires_at_s; this.subject = data.profile.user_id; return data.profile;
    }).catch(error => { if (generation === this.authGeneration && error instanceof ApiFailure && [401, 403].includes(error.status)) this.clearToken(); throw error; }).finally(() => { this.refreshing = null; });
    return this.refreshing;
  }
  async logout() { if (this.refreshing) { try { await this.refreshing; } catch { /* Still revoke the cookie. */ } } await this.withCookieLock(() => this.request("logout", "POST", undefined, undefined, true)); this.clearToken(); }
  clearToken() { this.token = null; this.subject = null; this.expiresAt = 0; this.authGeneration++; }
  authAction = <T = { accepted: boolean; delivery_mode: string }>(action: string, body: unknown = {}) => this.request<T>(action, "POST", body, undefined, true);
  adminUsers = () => this.localPages<ApiProfile>("admin/users");
  adminAudit = (cursor?: string) => this.request<Page<{ event_id: string; occurred_at: string; action: string; actor: { user_id: string }; target: { label: string }; reason: string | null }>>(`admin/audit${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`, "GET", undefined, undefined, true);
  private async localPages<T>(path: string): Promise<T[]> {
    const items: T[] = []; let cursor: string | null = null;
    for (let page = 0; page < 200; page++) {
      const data: Page<T> = await this.request(`${path}?limit=100${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`, "GET", undefined, undefined, true);
      items.push(...data.items); cursor = data.next_cursor; if (!cursor) return items;
    }
    throw new ApiFailure("Danh sách vượt giới hạn tải.", 503, "PAGE_LIMIT");
  }
  me = () => this.request<ApiProfile>("/me");
  updateProfile = (body: unknown) => this.request<ApiProfile>("/me", "PATCH", body);
  words = () => this.pages<SavedWord>("/vocabulary");
  history = () => this.pages<HistoryItem>("/history");
  stats = () => this.request<Stats>("/stats");
  saveWord = (word: string) => this.request<SavedWord>("/vocabulary", "POST", { language: "ja", entry_id: `sample:v1:${encodeURIComponent(word)}`, sense_id: "sample:v1:meaning", collection_id: null, occurrence: null }, crypto.randomUUID());
  deleteWord = (id: string) => this.request<void>(`/vocabulary/${id}`, "DELETE");
  reviewWord = (word: SavedWord, review_state: "learning" | "known") => this.request<SavedWord>(`/vocabulary/${word.word_id}/review`, "PATCH", { review_state, expected_version: word.version });
  createSession = (title: string, language: string) => this.request<StudySession>("/sessions", "POST", { mode: "solo", title, language }, crypto.randomUUID());
  getSession = (id: string) => this.request<StudySession>(`/sessions/${id}`);
  endSession = async (session: StudySession) => {
    for (let attempt = 0; attempt < 3; attempt++) {
      const current = await this.getSession(session.session_id);
      try { return await this.request<StudySession>(`/sessions/${session.session_id}/end`, "POST", { expected_version: current.version }, crypto.randomUUID()); }
      catch (error) { if (!(error instanceof ApiFailure) || error.code !== "VERSION_CONFLICT" || attempt === 2) throw error; }
    }
    throw new ApiFailure("Phiên học đang thay đổi. Vui lòng thử lại.", 409, "VERSION_CONFLICT");
  };
  registerSource = (sessionId: string, body: unknown, key: string, signal?: AbortSignal) => this.request<OcrSource>(`/sessions/${sessionId}/sources`, "POST", body, key, false, true, signal);
  createUpload = (sessionId: string, body: FrameMetadata, key: string, signal?: AbortSignal) => this.request<FrameUpload>(`/sessions/${sessionId}/uploads`, "POST", body, key, false, true, signal);
  createJob = (sessionId: string, upload: FrameUpload, key: string, signal?: AbortSignal) => this.request<OcrJob>(`/sessions/${sessionId}/ocr-jobs`, "POST", { upload_id: upload.upload_id, frame_id: upload.frame_id }, key, false, true, signal);
  getJob = (id: string, signal?: AbortSignal) => this.request<OcrJob>(`/ocr-jobs/${id}`, "GET", undefined, undefined, false, true, signal);
  getResult = (id: string, signal?: AbortSignal) => this.request<OcrResult>(`/results/${id}`, "GET", undefined, undefined, false, true, signal);
  resultPage = (sessionId: string, throughSeq: number, cursor?: string) => this.request<{ items: Pick<OcrResult, "result_id" | "source_id" | "seq">[]; next_cursor: string | null; through_seq: number }>(`/sessions/${sessionId}/results?through_seq=${throughSeq}&limit=20${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`);
  async putFrame(upload: FrameUpload, content: Blob, signal?: AbortSignal) {
    const url = new URL(upload.upload.url);
    if (url.protocol !== "http:" || !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) || !url.pathname.startsWith("/local-uploads/") || url.username || url.password || url.search || url.hash || upload.upload.method !== "PUT") throw new ApiFailure("Địa chỉ tải frame không được hỗ trợ.", 502, "INVALID_RESPONSE");
    const controller = new AbortController(), abort = () => controller.abort();
    if (signal?.aborted) controller.abort();
    signal?.addEventListener("abort", abort, { once: true });
    const timeout = window.setTimeout(abort, 15000);
    try {
      const response = await fetch(url, { method: "PUT", headers: upload.upload.headers, body: content, signal: controller.signal, credentials: "omit" });
      if (!response.ok) { const data = await response.json(); throw new ApiFailure(data.error?.message || "Chưa tải được frame.", response.status, data.error?.code || "REQUEST_FAILED"); }
      if (response.status !== 204) throw new ApiFailure("Phản hồi upload không hợp lệ.", 502, "INVALID_RESPONSE");
    } catch (error) { if (error instanceof ApiFailure) throw error; throw new ApiFailure("Mất kết nối khi tải frame. Hãy thử lại.", 0, "CONNECTION_ERROR"); }
    finally { window.clearTimeout(timeout); signal?.removeEventListener("abort", abort); }
  }
}
export const learningClient = new LearningClient();
