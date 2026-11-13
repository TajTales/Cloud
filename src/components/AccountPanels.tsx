import { useState } from "react";
import AppDialog from "./AppDialog";
export type UserProfile = { name: string; email: string; timezone: string; learningLanguage: string };
export type AccountView = "profile" | "settings" | "signup" | "reset-password" | "verify-email" | "change-password" | "change-email";
type AuthAction = (action: string, body?: unknown) => Promise<{ signed_out?: boolean; accepted?: boolean; delivery_mode?: string }>;
type Props = { view: AccountView; profile: UserProfile; onClose: () => void; onSave: (profile: UserProfile) => void | Promise<void>; connected?: boolean; emailVerified?: boolean; isAdmin?: boolean; onNavigate?: (view: AccountView) => void; onAuthAction?: AuthAction; onRegister?: (name: string, email: string, password: string) => Promise<void> };
export default function AccountPanels({ view, profile, onClose, onSave, connected = false, emailVerified = false, isAdmin = false, onNavigate, onAuthAction, onRegister }: Props) {
  const [complete, setComplete] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState(0);
  const [email, setEmail] = useState("");
  const [notice, setNotice] = useState("");
  const title = { profile: "Hồ sơ cá nhân", settings: "Cài đặt tài khoản", signup: "Đăng ký tài khoản", "reset-password": "Đặt lại mật khẩu", "verify-email": "Xác nhận email", "change-password": "Đổi mật khẩu", "change-email": "Đổi email đăng nhập" }[view];
  const codeFlow = ["reset-password", "verify-email", "change-email"].includes(view);
  const passwordFields = view === "signup" || view === "change-password" || (view === "reset-password" && step === 1);
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); if (pending) return;
    const values = new FormData(event.currentTarget);
    const value = (key: string) => String(values.get(key) || "");
    setError(""); setPending(true);
    try {
      if (passwordFields && value("password") !== value("confirmation")) throw new Error("Hai mật khẩu chưa trùng nhau.");
      if (view === "signup") {
        if (connected && onRegister) { await onRegister(value("name"), value("email"), value("password")); onClose(); return; }
      } else if (connected && onAuthAction && (codeFlow || view === "change-password")) {
        let action: string; let body: unknown;
        if (view === "reset-password") { action = step ? "password/reset" : "password/forgot"; body = step ? { email, code: value("code"), password: value("password") } : { email: value("email") }; }
        else if (view === "verify-email") { action = step ? "verification/confirm" : "verification/request"; body = step ? { code: value("code") } : {}; }
        else if (view === "change-email") { action = step ? "email/confirm" : "email/request"; body = step ? { code: value("code") } : { email: value("email"), password: value("current_password") }; }
        else { action = "password/change"; body = { current_password: value("current_password"), password: value("password") }; }
        const result = await onAuthAction(action, body);
        if (codeFlow && step === 0) {
          setEmail(view === "verify-email" ? profile.email : value("email")); setStep(1);
          setNotice(result.delivery_mode === "local_mailbox" ? "Đang dùng hộp thư thử trên máy, chưa gửi ra email. Nếu địa chỉ phù hợp, mã gồm 8 số sẽ xuất hiện trong hộp thư và hết hạn sau 10 phút." : "Nếu địa chỉ phù hợp, bạn sẽ nhận được mã xác nhận.");
          return;
        }
      } else if (view === "profile" || view === "settings") {
        const name = String(values.get("name") || profile.name).trim();
        if (!name) throw new Error("Vui lòng nhập tên hiển thị.");
        await onSave({ ...profile, name, email: String(values.get("email") || profile.email).trim(), timezone: String(values.get("timezone") || profile.timezone), learningLanguage: String(values.get("learningLanguage") || profile.learningLanguage) });
      }
      setComplete(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Chưa lưu được dữ liệu."); }
    finally { setPending(false); }
  };
  const resend = async () => {
    if (pending || !onAuthAction || view === "change-email") return;
    setPending(true); setError("");
    try { await onAuthAction(view === "verify-email" ? "verification/request" : "password/forgot", view === "verify-email" ? {} : { email }); setNotice("Đã tiếp nhận yêu cầu mã mới. Kiểm tra thư có thời gian hết hạn mới nhất."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Chưa yêu cầu được mã mới."); }
    finally { setPending(false); }
  };
  return <AppDialog title={title} description={connected ? view === "signup" ? "Tạo tài khoản để lưu từ vựng và theo dõi tiến độ học tập." : codeFlow ? "Xác nhận thông tin bằng mã dùng một lần." : "Cập nhật thông tin cá nhân và tùy chọn học tập của bạn." : "Bản xem trước; chưa đồng bộ với máy chủ."} onClose={onClose}>
    {complete ? <div><p className="app-notice app-notice-success" role="status">{connected ? view === "reset-password" || view === "change-password" || view === "change-email" ? "Đã cập nhật. Vui lòng đăng nhập lại." : "Đã lưu thay đổi." : "Đã hoàn tất thao tác trong bản xem trước."}</p><div className="app-dialog-actions"><button className="app-btn app-btn-primary" onClick={onClose}>Hoàn tất</button></div></div> : <form className="app-form" onSubmit={submit}>
      {(view === "profile" || view === "signup") && <label>Tên hiển thị<input name="name" defaultValue={view === "profile" ? profile.name : ""} maxLength={60} required autoComplete="name" /></label>}
      {(["profile", "signup"].includes(view) || (["reset-password", "change-email"].includes(view) && step === 0)) && <label>Địa chỉ email<input type="email" name="email" defaultValue={view === "profile" ? profile.email : ""} required autoComplete="email" readOnly={connected && view === "profile"} /></label>}
      {(view === "change-password" || (view === "change-email" && step === 0)) && <label>Mật khẩu hiện tại<input type="password" name="current_password" required minLength={8} maxLength={128} autoComplete="current-password" /></label>}
      {passwordFields && <><label>{view === "signup" ? "Mật khẩu" : "Mật khẩu mới"}<input type="password" name="password" minLength={8} maxLength={128} required autoComplete="new-password" /></label><label>Nhập lại mật khẩu<input type="password" name="confirmation" minLength={8} maxLength={128} required autoComplete="new-password" /></label></>}
      {codeFlow && step === 1 && <><p className="app-muted">Địa chỉ xác nhận: {email}</p><label>Mã xác nhận<input name="code" inputMode="numeric" pattern="[0-9]{8}" minLength={8} maxLength={8} required autoComplete="one-time-code" /></label><div className="app-dialog-actions">{view !== "change-email" && <button type="button" className="app-btn" onClick={resend} disabled={pending}>Yêu cầu mã mới</button>}<button type="button" className="app-btn" disabled={pending} onClick={() => { setStep(0); setNotice(""); setError(""); }}>Nhập lại thông tin</button></div></>}
      {view === "verify-email" && step === 0 && <p className="app-muted">Xác nhận địa chỉ {profile.email}.</p>}
      {view === "profile" && <><p className="app-notice">Vai trò: {isAdmin ? "Quản trị viên" : "Người học"}. {connected && (emailVerified ? "Email đã xác nhận trong môi trường hiện tại." : "Email chưa xác nhận.")}</p>{connected && !emailVerified && <button type="button" className="app-btn" onClick={() => onNavigate?.("verify-email")}>Xác nhận email</button>}</>}
      {view === "settings" && <><label>Ngôn ngữ đang học<select name="learningLanguage" defaultValue={profile.learningLanguage}><option value="ja">Tiếng Nhật</option><option value="zh">Tiếng Trung</option>{!connected && <><option value="en">Tiếng Anh</option><option value="fr">Tiếng Pháp</option></>}</select></label><label>Múi giờ<select name="timezone" defaultValue={profile.timezone}><option value="Asia/Ho_Chi_Minh">Việt Nam · UTC+7</option><option value="Asia/Tokyo">Nhật Bản · UTC+9</option><option value="UTC">UTC</option></select></label>{connected && <div className="app-dialog-actions"><button type="button" className="app-btn" onClick={() => onNavigate?.("change-password")}>Đổi mật khẩu</button><button type="button" className="app-btn" onClick={() => onNavigate?.("change-email")}>Đổi email</button><button type="button" className="app-btn" disabled={pending} onClick={async () => { if (!onAuthAction || pending) return; setPending(true); try { await onAuthAction("logout-all"); onClose(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Chưa đăng xuất được."); } finally { setPending(false); } }}>Đăng xuất mọi phiên</button></div>}</>}
      {notice && <p className="app-notice" role="status">{notice}</p>}
      {error && <p className="app-inline-error" role="alert">{error}</p>}
      <div className="app-dialog-actions"><button type="button" className="app-btn" onClick={onClose} disabled={pending}>Hủy</button><button type="submit" className="app-btn app-btn-primary" disabled={pending}>{pending ? "Đang xử lý…" : view === "signup" ? connected ? "Tạo tài khoản" : "Kiểm tra đăng ký mẫu" : codeFlow ? step ? "Xác nhận" : "Yêu cầu mã xác nhận" : "Lưu thay đổi"}</button></div>
    </form>}
  </AppDialog>;
}
