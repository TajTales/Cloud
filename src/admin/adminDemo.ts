export type DemoUser = { id: string; name: string; email: string; role: "user" | "admin"; status: "active" | "suspended" | "pending"; joined: string; sessions: number; words: number };
export type DemoRoom = { id: string; code: string; title: string; host: string; members: number; language: string; status: "open" | "closed"; started: string; ocrJobs: number };
export type DemoActivity = { id: string; time: string; level: "success" | "warning" | "error"; action: string; actor: string; target: string; detail: string };
export type DemoConfig = { provider: string; frameInterval: number; workers: number; maxImageMb: number; maintenance: boolean };
export const initialConfig: DemoConfig = { provider: "meikiocr", frameInterval: 2000, workers: 2, maxImageMb: 1, maintenance: false };
export const demoUsers: DemoUser[] = [
  { id: "demo-admin", name: "Quản trị viên demo", email: "admin@example.com", role: "admin", status: "active", joined: "01/11/2026", sessions: 0, words: 0 },
  { id: "demo-u1", name: "Mai Anh", email: "mai.anh@example.com", role: "user", status: "active", joined: "02/11/2026", sessions: 14, words: 48 },
  { id: "demo-u2", name: "Minh Khang", email: "khang@example.com", role: "user", status: "active", joined: "03/11/2026", sessions: 8, words: 26 },
  { id: "demo-u3", name: "Thu Hà", email: "thuha@example.com", role: "user", status: "active", joined: "04/11/2026", sessions: 11, words: 37 },
  { id: "demo-u4", name: "Hoàng An", email: "hoangan@example.com", role: "user", status: "suspended", joined: "05/11/2026", sessions: 3, words: 9 },
  { id: "demo-u5", name: "Julia", email: "julia@example.com", role: "user", status: "active", joined: "06/11/2026", sessions: 6, words: 21 },
  { id: "demo-u6", name: "Thanh Linh", email: "linh@example.com", role: "user", status: "pending", joined: "09/11/2026", sessions: 0, words: 0 },
  { id: "demo-u7", name: "Đức Minh", email: "ducminh@example.com", role: "user", status: "active", joined: "10/11/2026", sessions: 2, words: 5 },
];
export const demoRooms: DemoRoom[] = [
  { id: "demo-r1", code: "LINGO-3821", title: "Khám phá Tokyo về đêm", host: "Mai Anh", members: 5, language: "Tiếng Nhật", status: "open", started: "20:30", ocrJobs: 24 },
  { id: "demo-r2", code: "LINGO-1048", title: "Cùng đọc biển hiệu", host: "Minh Khang", members: 3, language: "Tiếng Nhật", status: "open", started: "20:42", ocrJobs: 16 },
  { id: "demo-r3", code: "LINGO-6612", title: "Luyện đọc cuối ngày", host: "Thu Hà", members: 2, language: "Tiếng Trung", status: "open", started: "21:00", ocrJobs: 9 },
  { id: "demo-r4", code: "LINGO-2380", title: "Một ngày ở Kyoto", host: "Julia", members: 0, language: "Tiếng Nhật", status: "closed", started: "18:15", ocrJobs: 31 },
];
export const demoActivity: DemoActivity[] = [
  { id: "demo-log-1", time: "21:08", level: "error", action: "OCR hết thời gian chờ", actor: "OCR worker mẫu", target: "demo-job-49", detail: "Tình huống minh họa OCR_TIMEOUT. Không phải cảnh báo từ server thực tế." },
  { id: "demo-log-2", time: "21:05", level: "success", action: "Thành viên tham gia phòng", actor: "Mai Anh (mẫu)", target: "LINGO-3821", detail: "Thành viên thứ 5 tham gia phòng học mẫu." },
  { id: "demo-log-3", time: "21:02", level: "warning", action: "Frame vượt giới hạn", actor: "Ứng dụng mẫu", target: "demo-frame-17", detail: "Minh họa IMAGE_TOO_LARGE; client cần nén ảnh trước khi gửi lại." },
  { id: "demo-log-4", time: "21:00", level: "success", action: "Tạo phòng học", actor: "Thu Hà (mẫu)", target: "LINGO-6612", detail: "Phòng học minh họa được tạo cho giao diện quản trị." },
  { id: "demo-log-5", time: "20:50", level: "success", action: "Lưu từ vựng", actor: "Julia (mẫu)", target: "喫茶店", detail: "Tình huống lưu từ trong phiên học mẫu." },
];
export function searchText(value: string) { return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase(); }
