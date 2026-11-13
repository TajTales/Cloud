import { useEffect, useState } from "react";
import { ApiFailure, learningClient as client, type ApiProfile } from "../api/learning";
import AppDialog from "../components/AppDialog";
import "./AdminWorkspace.css";

type Props = { profile: ApiProfile; darkMode: boolean; onToggleTheme: () => void; onLogout: () => void; onExit: () => void; onCheckSession: () => void };
export default function LocalAdminWorkspace({ profile, darkMode, onToggleTheme, onLogout, onExit, onCheckSession }: Props) {
  const [page, setPage] = useState<"users" | "audit">("users");
  const [users, setUsers] = useState<ApiProfile[]>([]);
  const [audit, setAudit] = useState<Awaited<ReturnType<typeof client.adminAudit>> | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [target, setTarget] = useState<ApiProfile | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  function report(reason: unknown) {
    setError(reason instanceof Error ? reason.message : "Chưa tải được dữ liệu.");
    if (reason instanceof ApiFailure && (reason.status === 401 || reason.details.account_status)) onCheckSession();
  }
  async function load() {
    if (busy) return;
    setBusy(true); setError("");
    try {
      if (page === "users") setUsers(await client.adminUsers());
      else setAudit(await client.adminAudit());
    } catch (reason) { report(reason); }
    finally { setBusy(false); }
  }
  useEffect(() => { void load(); }, [page]);
  const filtered = users.filter(user => `${user.display_name} ${user.email}`.toLocaleLowerCase("vi").includes(query.trim().toLocaleLowerCase("vi")) && (filter === "all" || user.status === filter));
  async function confirm(event: React.FormEvent) {
    event.preventDefault(); if (!target || busy) return;
    setBusy(true); setError("");
    try {
      const changed = await client.authAction<ApiProfile>("admin/status", { user_id: target.user_id, status: target.status === "suspended" ? "active" : "suspended", expected_version: target.version, reason });
      setUsers(items => items.map(user => user.user_id === changed.user_id ? changed : user));
      setTarget(null); setReason(""); setNotice("Đã cập nhật trạng thái tài khoản và lưu nhật ký.");
    } catch (reason) { report(reason); }
    finally { setBusy(false); }
  }
  return <div className="ad-root">
    <aside className="ad-sidebar"><div className="ad-brand"><div>Lingua<span>Live</span><small>QUẢN TRỊ TÀI KHOẢN</small></div></div><nav aria-label="Quản trị"><button className={page === "users" ? "is-active" : ""} disabled={busy} onClick={() => setPage("users")}>Người dùng</button><button className={page === "audit" ? "is-active" : ""} disabled={busy} onClick={() => setPage("audit")}>Nhật ký phân quyền</button></nav><div className="ad-sidebar-footer"><button onClick={onExit}>Về không gian học tập</button></div></aside>
    <main className="ad-main"><header className="ad-header"><strong>{page === "users" ? "Người dùng" : "Nhật ký phân quyền"}</strong><div><span>{profile.display_name}</span><button className="app-btn" onClick={onToggleTheme}>{darkMode ? "Giao diện sáng" : "Giao diện tối"}</button><button className="app-btn" onClick={onLogout}>Đăng xuất</button></div></header>
      <div className="ad-content"><div className="ad-page-heading"><div><h1>{page === "users" ? "Quản lý tài khoản" : "Những thay đổi gần đây"}</h1><p>{page === "users" ? "Xem tài khoản, kiểm tra quyền và quản lý trạng thái truy cập." : "Các thay đổi quyền và trạng thái tài khoản đã được ghi lại."}</p></div><button className="app-btn" disabled={busy} onClick={() => void load()}>{busy ? "Đang tải…" : "Tải lại"}</button></div>
      {error && <p className="app-inline-error" role="alert">{error}</p>}{notice && <p className="app-notice app-notice-success" role="status">{notice}</p>}
      {page === "users" ? <section className="ad-panel"><div className="ad-filters"><label className="ad-search"><input aria-label="Tìm người dùng" placeholder="Tìm tên hoặc email…" value={query} onChange={event => setQuery(event.target.value)} /></label><select aria-label="Trạng thái tài khoản" value={filter} onChange={event => setFilter(event.target.value)}><option value="all">Mọi trạng thái</option><option value="active">Hoạt động</option><option value="suspended">Đã khóa</option></select></div><div className="ad-table-scroll"><table className="ad-table"><caption className="ad-sr-only">Tài khoản trong hệ thống</caption><thead><tr><th>Người dùng</th><th>Vai trò</th><th>Email</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{filtered.map(user => <tr key={user.user_id}><td><strong>{user.display_name}</strong><small className="ad-subtle-label">{user.user_id === profile.user_id ? " · Bạn" : ""}</small></td><td>{user.roles.includes("admin") ? "Quản trị viên" : "Người học"}</td><td>{user.email}<br /><small className="ad-subtle-label">{user.email_verified ? "Đã xác nhận" : "Chưa xác nhận"}</small></td><td><span className={`ad-status ad-status-${user.status}`}>{user.status === "active" ? "Hoạt động" : user.status === "suspended" ? "Đã khóa" : "Chờ xác nhận"}</span></td><td><button className="app-btn" disabled={busy || user.user_id === profile.user_id || user.status === "pending" || !profile.permissions.includes("users.status.write")} onClick={() => { setTarget(user); setReason(""); setError(""); }}>{user.status === "suspended" ? "Mở khóa" : "Khóa"}</button></td></tr>)}</tbody></table>{!filtered.length && <p className="ad-empty">{busy ? "Đang tải tài khoản…" : "Chưa có tài khoản khớp bộ lọc."}</p>}</div></section> : <section className="ad-panel"><div className="ad-log-list">{audit?.items.map(event => <article className="ad-log" key={event.event_id}><div><strong>{event.action}</strong><p>{event.target.label} · {event.reason}</p><p>{event.actor.user_id}</p></div><time>{new Date(event.occurred_at).toLocaleString("vi-VN")}</time></article>)}</div>{!audit?.items.length && <p className="ad-empty">Chưa có sự kiện.</p>}{audit?.next_cursor && <button className="app-btn" disabled={busy} onClick={async () => { setBusy(true); try { const next = await client.adminAudit(audit.next_cursor!); setAudit({ ...next, items: [...audit.items, ...next.items] }); } catch (reason) { report(reason); } finally { setBusy(false); } }}>Xem thêm</button>}</section>}
      </div>
    </main>
    {target && <AppDialog title={`${target.status === "suspended" ? "Mở khóa" : "Khóa"} tài khoản?`} description={target.email} onClose={() => { if (!busy) setTarget(null); }}><form className="app-form" onSubmit={confirm}><label>Lý do<textarea required minLength={3} maxLength={300} value={reason} onChange={event => setReason(event.target.value)} /></label>{error && <p className="app-inline-error" role="alert">{error}</p>}<p className="app-muted">Thao tác sẽ thu hồi các phiên hiện tại của tài khoản này.</p><div className="app-dialog-actions"><button type="button" className="app-btn" disabled={busy} onClick={() => setTarget(null)}>Hủy</button><button className="app-btn app-btn-danger" disabled={busy || reason.trim().length < 3}>Xác nhận</button></div></form></AppDialog>}
  </div>;
}
