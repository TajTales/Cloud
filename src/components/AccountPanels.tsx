import { useState } from "react";
import AppDialog from "./AppDialog";
export type UserProfile = { name: string; email: string; timezone: string; learningLanguage: string };
export type AccountView = "profile" | "settings" | "signup" | "reset-password";
type Props = { view: AccountView; profile: UserProfile; onClose: () => void; onSave: (profile: UserProfile) => void };
export default function AccountPanels({ view, profile, onClose, onSave }: Props) {
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState("");
  const title = { profile: "Hồ sơ cá nhân", settings: "Cài đặt tài khoản", signup: "Đăng ký tài khoản", "reset-password": "Đặt lại mật khẩu" }[view];
  return <AppDialog title={title} description={view === "signup" || view === "reset-password" ? "Xem trước luồng tài khoản. Chưa kết nối dịch vụ xác thực và gửi email." : "Thông tin dùng thử trên thiết bị này; chưa đồng bộ tài khoản trên máy chủ."} onClose={onClose}>
    {complete ? <div><p className="app-notice app-notice-success" role="status">{view === "signup" ? "Biểu mẫu hợp lệ. Khi kết nối Cognito, bước tiếp theo sẽ là xác nhận email; hiện chưa tạo tài khoản thật." : view === "reset-password" ? "Biểu mẫu đã sẵn sàng. Hiện chưa gửi email đặt lại mật khẩu vì dịch vụ xác thực chưa kết nối." : "Đã lưu thiết lập dùng thử trên thiết bị này."}</p><div className="app-dialog-actions"><button className="app-btn app-btn-primary" onClick={onClose}>Hoàn tất</button></div></div> : <form className="app-form" onSubmit={event => { event.preventDefault(); setError(""); const values = new FormData(event.currentTarget); if (view === "signup") { if (values.get("password") !== values.get("confirmation")) { setError("Hai mật khẩu chưa trùng nhau."); return; } } else if (view === "profile" || view === "settings") { const name = String(values.get("name") || profile.name).trim(); if (!name) { setError("Vui lòng nhập tên hiển thị."); return; } onSave({ ...profile, name, email: String(values.get("email") || profile.email).trim(), timezone: String(values.get("timezone") || profile.timezone), learningLanguage: String(values.get("learningLanguage") || profile.learningLanguage) }); } setComplete(true); }}>
      {(view === "profile" || view === "signup") && <label>Tên hiển thị<input name="name" defaultValue={view === "profile" ? profile.name : ""} maxLength={60} required autoComplete="name" /></label>}
      {view !== "settings" && <label>Địa chỉ email<input type="email" name="email" defaultValue={view === "profile" ? profile.email : ""} required autoComplete="email" /></label>}
      {view === "signup" && <><label>Mật khẩu<input type="password" name="password" minLength={8} required autoComplete="new-password" /></label><label>Nhập lại mật khẩu<input type="password" name="confirmation" minLength={8} required autoComplete="new-password" /></label></>}
      {view === "profile" && <p className="app-notice">Vai trò: Người học. Quyền Admin không thể cấp qua hồ sơ cá nhân.</p>}
      {view === "settings" && <><label>Ngôn ngữ đang học<select name="learningLanguage" defaultValue={profile.learningLanguage}><option value="ja">Tiếng Nhật</option><option value="zh">Tiếng Trung</option><option value="en">Tiếng Anh</option><option value="fr">Tiếng Pháp</option></select></label><label>Múi giờ<select name="timezone" defaultValue={profile.timezone}><option value="Asia/Ho_Chi_Minh">Việt Nam · UTC+7</option><option value="Asia/Tokyo">Nhật Bản · UTC+9</option><option value="UTC">UTC</option></select></label><p className="app-notice">Thiết lập này chỉ lưu trong trình duyệt. Đăng nhập và dữ liệu học thật sẽ cần kết nối backend.</p></>}
      {error && <p className="app-inline-error" role="alert">{error}</p>}
      <div className="app-dialog-actions"><button type="button" className="app-btn" onClick={onClose}>Hủy</button><button type="submit" className="app-btn app-btn-primary">{view === "signup" ? "Kiểm tra đăng ký mẫu" : view === "reset-password" ? "Tiếp tục bản xem trước" : "Lưu thiết lập"}</button></div>
    </form>}
  </AppDialog>;
}
