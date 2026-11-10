import { useEffect, useState } from "react";
import TranscriptVocabulary from "./components/TranscriptVocabulary";

type IconName =
  | "book"
  | "camera"
  | "captions"
  | "chevron"
  | "clock"
  | "copy"
  | "grid"
  | "headphones"
  | "history"
  | "logout"
  | "menu"
  | "message"
  | "mic"
  | "moon"
  | "more"
  | "people"
  | "play"
  | "plus"
  | "send"
  | "settings"
  | "sparkles"
  | "sun"
  | "user"
  | "volume"
  | "x";

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, React.ReactNode> = {
    book: (
      <>
        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
        <path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5z" />
      </>
    ),
    camera: (
      <>
        <path d="M14 9.5 19 7v10l-5-2.5z" />
        <rect x="3" y="5" width="11" height="14" rx="3" />
      </>
    ),
    captions: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="3" />
        <path d="M7 10h4M7 14h3M14 10h3M13 14h4" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    copy: (
      <>
        <rect x="8" y="8" width="11" height="11" rx="2" />
        <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
      </>
    ),
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="2" />
        <rect x="14" y="3" width="7" height="7" rx="2" />
        <rect x="3" y="14" width="7" height="7" rx="2" />
        <rect x="14" y="14" width="7" height="7" rx="2" />
      </>
    ),
    headphones: (
      <>
        <path d="M4 14v-2a8 8 0 0 1 16 0v2" />
        <path d="M4 14a2 2 0 0 1 2-2h1v7H6a2 2 0 0 1-2-2zM20 14a2 2 0 0 0-2-2h-1v7h1a2 2 0 0 0 2-2z" />
      </>
    ),
    history: (
      <>
        <path d="M4.9 5.3A9 9 0 1 1 3 12" />
        <path d="M3 5v5h5M12 7v5l3 2" />
      </>
    ),
    logout: (
      <>
        <path d="M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4M14 8l4 4-4 4M18 12H9" />
      </>
    ),
    menu: <path d="M4 7h16M4 12h16M4 17h16" />,
    message: (
      <>
        <path d="M20 15a3 3 0 0 1-3 3H9l-5 3v-6a3 3 0 0 1-1-2V7a3 3 0 0 1 3-3h11a3 3 0 0 1 3 3z" />
        <path d="M8 10h.01M12 10h.01M16 10h.01" />
      </>
    ),
    mic: (
      <>
        <rect x="9" y="3" width="6" height="12" rx="3" />
        <path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6" />
      </>
    ),
    moon: <path d="M20 15.2A8.5 8.5 0 0 1 8.8 4 8.5 8.5 0 1 0 20 15.2z" />,
    more: (
      <>
        <circle cx="5" cy="12" r="1" fill="currentColor" />
        <circle cx="12" cy="12" r="1" fill="currentColor" />
        <circle cx="19" cy="12" r="1" fill="currentColor" />
      </>
    ),
    people: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3.5 19a5.5 5.5 0 0 1 11 0M16 5.5a3 3 0 0 1 0 5.5M17 14a5 5 0 0 1 4 5" />
      </>
    ),
    play: <path d="m9 7 8 5-8 5z" />,
    plus: <path d="M12 5v14M5 12h14" />,
    send: <path d="m21 3-7 18-4-7-7-4zM10 14 21 3" />,
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6 1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1z" />
      </>
    ),
    sparkles: (
      <>
        <path d="m12 3 1.1 3.4L16.5 8l-3.4 1.1L12 12.5l-1.1-3.4L7.5 8l3.4-1.6z" />
        <path d="m18 14 .7 2.3L21 17l-2.3.7L18 20l-.7-2.3L15 17l2.3-.7z" />
      </>
    ),
    sun: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </>
    ),
    user: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </>
    ),
    volume: (
      <>
        <path d="M11 5 6 9H3v6h3l5 4zM15 9a4 4 0 0 1 0 6M18 6a8 8 0 0 1 0 12" />
      </>
    ),
    x: <path d="m6 6 12 12M18 6 6 18" />,
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}

type MotionButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  magnetic?: boolean;
};

function MotionButton({ magnetic = false, className = "", onPointerMove, onPointerLeave, ...props }: MotionButtonProps) {
  const handleMove = (event: React.PointerEvent<HTMLButtonElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    event.currentTarget.style.setProperty("--spot-x", `${x}px`);
    event.currentTarget.style.setProperty("--spot-y", `${y}px`);
    onPointerMove?.(event);
  };

  const handleLeave = (event: React.PointerEvent<HTMLButtonElement>) => {
    event.currentTarget.style.setProperty("--mag-x", "0px");
    event.currentTarget.style.setProperty("--mag-y", "0px");
    event.currentTarget.style.setProperty("--tilt-x", "0deg");
    event.currentTarget.style.setProperty("--tilt-y", "0deg");
    onPointerLeave?.(event);
  };

  return <button className={`motion-button ${className}`} onPointerMove={handleMove} onPointerLeave={handleLeave} {...props} />;
}

function SplitText({ children, className = "" }: { children: string; className?: string }) {
  return (
    <span className={`split-text ${className}`} aria-label={children}>
      {children.split(" ").map((word, index) => (
        <span className={word.toLowerCase().includes("hình") ? "accent-word" : ""} aria-hidden="true" key={`${word}-${index}`} style={{ "--word-index": index } as React.CSSProperties}>
          {word}&nbsp;
        </span>
      ))}
    </span>
  );
}

function SpotlightTracking() {
  useEffect(() => {
    const move = (event: PointerEvent) => {
      if (!(event.target instanceof Element)) return;
      const card = event.target.closest<HTMLElement>(".spotlight-card");
      if (!card) return;
      const rect = card.getBoundingClientRect();
      card.style.setProperty("--spot-x", `${event.clientX - rect.left}px`);
      card.style.setProperty("--spot-y", `${event.clientY - rect.top}px`);
    };
    window.addEventListener("pointermove", move, { passive: true });
    return () => window.removeEventListener("pointermove", move);
  }, []);
  return null;
}

function ThemeToggle({ darkMode, onToggle, label }: { darkMode: boolean; onToggle: (event: React.MouseEvent<HTMLButtonElement>) => void; label: string }) {
  return (
    <MotionButton className="theme-toggle" onClick={onToggle} aria-label={label}>
      <span className="theme-icon"><Icon name={darkMode ? "sun" : "moon"} size={18} /></span>
    </MotionButton>
  );
}

function tiltCard(event: React.PointerEvent<HTMLButtonElement>) {
  const rect = event.currentTarget.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  event.currentTarget.style.setProperty("--tilt-y", `${((x / rect.width) - 0.5) * 3}deg`);
  event.currentTarget.style.setProperty("--tilt-x", `${((0.5 - y / rect.height) * 3)}deg`);
}

const transcript = [
  {
    time: "01:42",
    japanese: "すみません、この近くにおすすめのカフェはありますか？",
    reading: "Sumimasen, kono chikaku ni osusume no kafe wa arimasu ka?",
    translation: "Xin lỗi, gần đây có quán cà phê nào bạn đề xuất không?",
  },
  {
    time: "01:49",
    japanese: "はい、角を曲がったところに静かな喫茶店があります。",
    reading: "Hai, kado o magatta tokoro ni shizuka na kissaten ga arimasu.",
    translation: "Có, ngay sau khi rẽ ở góc đường có một quán cà phê yên tĩnh.",
  },
];

const words = [
  { word: "喫茶店", reading: "きっさてん", meaning: "quán cà phê", color: "coral" },
  { word: "おすすめ", reading: "osusume", meaning: "đề xuất", color: "violet" },
  { word: "静か", reading: "しずか", meaning: "yên tĩnh", color: "green" },
];

const detectedWords = [
  { word: "居酒屋", reading: "いざかや · izakaya", meaning: "quán nhậu", color: "coral" },
  { word: "営業中", reading: "えいぎょうちゅう", meaning: "đang mở cửa", color: "green" },
];

function pronounce(word: string, rate = 0.85) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const speech = new SpeechSynthesisUtterance(word);
  speech.lang = "ja-JP";
  speech.rate = rate;
  window.speechSynthesis.speak(speech);
}

const previousSessions = [
  { date: "Hôm qua, 20:30", title: "Khám phá Tokyo về đêm", language: "Tiếng Nhật · N4", duration: "38 phút", words: 12 },
  { date: "12 tháng 6, 19:15", title: "Gọi món tại Paris", language: "Tiếng Pháp · A2", duration: "24 phút", words: 8 },
  { date: "09 tháng 6, 08:40", title: "Một ngày ở New York", language: "Tiếng Anh · B1", duration: "42 phút", words: 17 },
];

type Language = "vi" | "en";

const copy = {
  vi: {
    rooms: "Phòng học",
    library: "Thư viện",
    history: "Lịch sử",
    streak: "ngày liên tiếp",
    account: "Tài khoản",
    profile: "Hồ sơ cá nhân",
    settings: "Cài đặt tài khoản",
    appearance: "Giao diện",
    light: "Sáng",
    dark: "Tối",
    language: "Ngôn ngữ",
    logout: "Đăng xuất",
    loginEyebrow: "HỌC NGÔN NGỮ QUA MỌI KHUNG HÌNH",
    loginTitle: "Chào mừng bạn trở lại",
    loginSubtitle: "Tiếp tục hành trình học ngôn ngữ theo cách tự nhiên nhất.",
    email: "Địa chỉ email",
    password: "Mật khẩu",
    remember: "Ghi nhớ đăng nhập",
    forgot: "Quên mật khẩu?",
    login: "Đăng nhập",
    or: "hoặc tiếp tục với",
    noAccount: "Chưa có tài khoản?",
    signup: "Đăng ký miễn phí",
    quote: "Mỗi khung hình là một cơ hội để hiểu thêm một ngôn ngữ mới.",
    ready: "Sẵn sàng luyện tập",
    heroTitle: "Hôm nay bạn muốn\nhọc theo cách nào?",
    heroText: "Học từ mọi video với phụ đề, phiên âm và từ vựng được nhận diện bằng OCR theo thời gian thực.",
    solo: "Học một mình",
    create: "Tạo phòng mới",
    join: "Tham gia phòng",
    logs: "Nhật ký đã học",
    start: "Bắt đầu học",
    createAction: "Tạo phòng",
    joinAction: "Nhập mã phòng",
    historyAction: "Xem lịch sử",
  },
  en: {
    rooms: "Study rooms",
    library: "Library",
    history: "History",
    streak: "day streak",
    account: "Account",
    profile: "Personal profile",
    settings: "Account settings",
    appearance: "Appearance",
    light: "Light",
    dark: "Dark",
    language: "Language",
    logout: "Log out",
    loginEyebrow: "LEARN A LANGUAGE FROM EVERY FRAME",
    loginTitle: "Welcome back",
    loginSubtitle: "Continue your journey to learning languages naturally.",
    email: "Email address",
    password: "Password",
    remember: "Remember me",
    forgot: "Forgot password?",
    login: "Sign in",
    or: "or continue with",
    noAccount: "New to LinguaLive?",
    signup: "Create a free account",
    quote: "Every frame is an opportunity to understand a new language.",
    ready: "Ready to practice",
    heroTitle: "How would you like\nto learn today?",
    heroText: "Learn from any video with real-time OCR-powered subtitles, transcripts and vocabulary.",
    solo: "Learn solo",
    create: "Create a room",
    join: "Join a room",
    logs: "Learning history",
    start: "Start learning",
    createAction: "Create room",
    joinAction: "Enter room code",
    historyAction: "View history",
  },
};

export default function App() {
  const [authenticated, setAuthenticated] = useState(() => localStorage.getItem("lingualive-auth") === "true");
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("lingualive-theme");
    return saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  const [language, setLanguage] = useState<Language>(() => (localStorage.getItem("lingualive-language") as Language) || "vi");
  const [accountMenu, setAccountMenu] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [screen, setScreen] = useState<"lobby" | "room" | "history" | "library">("lobby");
  const [dialog, setDialog] = useState<"create" | "join" | null>(null);
  const [roomMode, setRoomMode] = useState<"solo" | "group">("group");
  const [roomTitle, setRoomTitle] = useState("Khám phá Tokyo về đêm");
  const [joinCode, setJoinCode] = useState("");
  const [playing, setPlaying] = useState(false);
  const [panel, setPanel] = useState<"transcript" | "chat">("transcript");
  const [savedWords, setSavedWords] = useState(words);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [cameraOn, setCameraOn] = useState(true);
  const [micOn, setMicOn] = useState(true);
  const [copied, setCopied] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [email, setEmail] = useState("");
  const [loginStatus, setLoginStatus] = useState<"idle" | "loading" | "done">("idle");
  const [tipIndex, setTipIndex] = useState(0);
  const text = copy[language];
  const inspectedWord = [...detectedWords, ...savedWords].find(item => item.word === selectedWord);

  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? "dark" : "light";
    localStorage.setItem("lingualive-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  useEffect(() => {
    localStorage.setItem("lingualive-language", language);
    document.documentElement.lang = language;
  }, [language]);

  useEffect(() => {
    const interval = window.setInterval(() => setTipIndex((index) => (index + 1) % 3), 4200);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const escape = (event: KeyboardEvent) => { if (event.key === "Escape") setSelectedWord(null); };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, []);

  useEffect(() => () => { if ("speechSynthesis" in window) window.speechSynthesis.cancel(); }, [screen]);

  const toggleTheme = (event: React.MouseEvent<HTMLButtonElement>) => {
    const next = !darkMode;
    const x = event.clientX;
    const y = event.clientY;
    document.documentElement.style.setProperty("--theme-x", `${x}px`);
    document.documentElement.style.setProperty("--theme-y", `${y}px`);
    const documentWithTransition = document as Document & { startViewTransition?: (callback: () => void) => void };
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches && documentWithTransition.startViewTransition) {
      documentWithTransition.startViewTransition(() => setDarkMode(next));
    } else {
      setDarkMode(next);
    }
  };

  const copyRoom = () => {
    navigator.clipboard?.writeText("LINGO-3821");
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };

  const goTo = (next: typeof screen) => {
    setScreen(next);
    setMobileNav(false);
  };

  const enterRoom = (mode: "solo" | "group", title = "Khám phá Tokyo về đêm") => {
    setSelectedWord(null);
    setRoomMode(mode);
    setRoomTitle(title);
    setDialog(null);
    setScreen("room");
  };

  const login = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoginStatus("loading");
    window.setTimeout(() => {
      setLoginStatus("done");
      localStorage.setItem("lingualive-auth", "true");
      window.setTimeout(() => setAuthenticated(true), 420);
    }, 760);
  };

  const logout = () => {
    localStorage.removeItem("lingualive-auth");
    setAuthenticated(false);
    setAccountMenu(false);
    setScreen("lobby");
  };

  if (!authenticated) {
    return (
      <main className="login-page">
        <SpotlightTracking />

        <section className="login-visual">
          <img
            src="https://images.unsplash.com/photo-1573455494060-c5595004fb6c?crop=entropy&cs=tinysrgb&fit=crop&fm=jpg&q=86&w=1400&h=1600"
            alt="Con phố Tokyo với những biển hiệu vào ban đêm"
          />
          <div className="login-overlay" />
          <div className="film-grain" />
          <div className="scan-line" />
          <div className="floating-captions" aria-hidden="true">
            <span className="caption-chip chip-one">酒<small>さけ · sake</small></span>
            <span className="caption-chip chip-two">Bonjour<small>xin chào</small></span>
            <span className="caption-chip chip-three">水車<small>すいしゃ</small></span>
            <span className="caption-chip chip-four">Hello<small>/həˈləʊ/</small></span>
          </div>
          <div className="login-brand brand">
            <span className="brand-mark"><Icon name="captions" size={22} /></span>
            <span>Lingua<span>Live</span></span>
          </div>
          <div className="visual-copy">
            <span><Icon name="sparkles" size={16} /> OCR · LIVE TRANSCRIPT · VOCABULARY</span>
            <blockquote>“<SplitText>{text.quote}</SplitText>”</blockquote>
            <div className="learner-proof">
              <div className="participant-stack"><span>AN</span><span>TK</span><span>JL</span><b>+2k</b></div>
              <p><strong>2.000+ người học</strong><small>đang luyện tập mỗi ngày</small></p>
            </div>
          </div>
        </section>
        <section className="login-form-side">
          <div className="aurora-mesh" aria-hidden="true" />
          <div className="dot-grid" aria-hidden="true" />
          <div className="login-top-actions">
            <MotionButton onClick={() => setLanguage(language === "vi" ? "en" : "vi")}><span>{language === "vi" ? "VN" : "EN"}</span>{language === "vi" ? "Tiếng Việt" : "English"}<Icon name="chevron" size={14} /></MotionButton>
            <ThemeToggle darkMode={darkMode} onToggle={toggleTheme} label={darkMode ? text.light : text.dark} />
          </div>
          <div className="login-card spotlight-card">
            <div className="mobile-login-brand brand">
              <span className="brand-mark"><Icon name="captions" size={22} /></span>
              <span>Lingua<span>Live</span></span>
            </div>
            <div className="login-eyebrow">{text.loginEyebrow}</div>
            <h1><SplitText>{text.loginTitle}</SplitText></h1>
            <p>{text.loginSubtitle}</p>
            <form onSubmit={login}>
              <label>{text.email}
                <div className={`login-input ${email.includes("@") ? "valid" : ""}`}><span>@</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="mai@example.com" required /><i>✓</i></div>
              </label>
              <label>{text.password}
                <div className="login-input"><Icon name="clock" size={17} /><input type={showPassword ? "text" : "password"} placeholder="••••••••" minLength={6} required /><button type="button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? (language === "vi" ? "Ẩn" : "Hide") : (language === "vi" ? "Hiện" : "Show")}</button></div>
              </label>
              <div className="login-options">
                <label><input type="checkbox" defaultChecked /> {text.remember}</label>
                <button type="button">{text.forgot}</button>
              </div>
              <MotionButton magnetic className={`login-submit spark-action ${loginStatus}`} type="submit" disabled={loginStatus !== "idle"}>
                <span>{loginStatus === "idle" ? text.login : loginStatus === "loading" ? "Đang đăng nhập" : "Hoàn tất"}</span>
                {loginStatus === "loading" ? <i className="spinner" /> : loginStatus === "done" ? <i className="checkmark">✓</i> : <Icon name="chevron" size={17} />}
              </MotionButton>
            </form>
            <div className="login-divider"><span>{text.or}</span></div>
            <div className="social-logins">
              <button><b>G</b> Google</button>
              <button><b>f</b> Facebook</button>
            </div>
            <p className="signup-prompt">{text.noAccount} <button>{text.signup}</button></p>
          </div>
          <footer>© 2025 LinguaLive <span>{language === "vi" ? "Quyền riêng tư" : "Privacy"}</span><span>{language === "vi" ? "Điều khoản" : "Terms"}</span></footer>
        </section>
      </main>
    );
  }

  return (
    <div className="app-shell">
      <SpotlightTracking />

      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">
            <Icon name="captions" size={22} />
          </span>
          <span>Lingua<span>Live</span></span>
        </div>
        <nav className={`main-nav ${mobileNav ? "open" : ""}`}>
          <button className={screen === "lobby" || screen === "room" ? "active" : ""} onClick={() => goTo("lobby")}><Icon name="grid" size={18} /> {text.rooms}</button>
          <button className={screen === "library" ? "active" : ""} onClick={() => goTo("library")}><Icon name="book" size={18} /> {text.library}</button>
          <button className={screen === "history" ? "active" : ""} onClick={() => goTo("history")}><Icon name="history" size={18} /> {text.history}</button>
        </nav>
        <div className="header-actions">
          <button className="streak-pill"><span>12</span> {text.streak}</button>
          <ThemeToggle darkMode={darkMode} onToggle={toggleTheme} label={darkMode ? text.light : text.dark} />
          <div className="account-wrap">
            <button className={`avatar ${accountMenu ? "active" : ""}`} aria-label="Tài khoản của Mai" aria-expanded={accountMenu} onClick={() => setAccountMenu(!accountMenu)}>MA</button>
            {accountMenu && (
              <div className="account-menu">
                <div className="account-summary">
                  <span className="avatar large">MA</span>
                  <div><strong>Mai Anh</strong><small>mai.anh@example.com</small></div>
                </div>
                <div className="account-links">
                  <button><Icon name="user" size={17} /><span>{text.profile}<small>{language === "vi" ? "Xem và chỉnh sửa thông tin" : "View and edit your details"}</small></span><Icon name="chevron" size={15} /></button>
                  <button><Icon name="settings" size={17} /><span>{text.settings}<small>{language === "vi" ? "Bảo mật và thông báo" : "Security and notifications"}</small></span><Icon name="chevron" size={15} /></button>
                </div>
                <div className="setting-row">
                  <span><Icon name={darkMode ? "moon" : "sun"} size={17} /> {text.appearance}</span>
                  <div className="segmented-control">
                    <button className={!darkMode ? "active" : ""} onClick={() => setDarkMode(false)}>{text.light}</button>
                    <button className={darkMode ? "active" : ""} onClick={() => setDarkMode(true)}>{text.dark}</button>
                  </div>
                </div>
                <div className="setting-row">
                  <span><Icon name="captions" size={17} /> {text.language}</span>
                  <div className="segmented-control language">
                    <button className={language === "vi" ? "active" : ""} onClick={() => setLanguage("vi")}>VI</button>
                    <button className={language === "en" ? "active" : ""} onClick={() => setLanguage("en")}>EN</button>
                  </div>
                </div>
                <button className="logout-button" onClick={logout}><Icon name="logout" size={17} /> {text.logout}</button>
              </div>
            )}
          </div>
          <button className="mobile-menu" onClick={() => setMobileNav(!mobileNav)} aria-label="Mở menu">
            <Icon name={mobileNav ? "x" : "menu"} />
          </button>
        </div>
      </header>

      {screen === "lobby" ? (
        <main className="workspace lobby-workspace">
          <section className="lobby-hero">
            <div>
              <div className="eyebrow"><span className="live-dot" /> {text.ready}</div>
              <h1>{text.heroTitle.split("\n").map((line, index) => <span className="hero-title-line" key={index}><SplitText>{line}</SplitText></span>)}</h1>
              <p>{text.heroText}</p>
            </div>
            <div className="weekly-card">
              <div className="weekly-ring"><strong>4</strong><span>/ 5 buổi</span></div>
              <div><span>Mục tiêu tuần</span><strong>Chỉ còn 1 buổi nữa</strong><small>Tiếp tục duy trì chuỗi học của bạn</small></div>
            </div>
          </section>

          <section className="mode-grid">
            <MotionButton data-cursor="PLAY" className="mode-card featured spotlight-card" onPointerMove={tiltCard} onClick={() => enterRoom("solo", "Buổi học cá nhân")}>
              <span className="card-scene scene-solo" aria-hidden="true"><span className="scene-glyph">あ</span><span className="scene-caption">東京 · TOKYO</span><i /><i /><i /></span>
              <span className="mode-icon"><Icon name="headphones" size={25} /></span>
              <span className="mode-tag">Tập trung</span>
              <h2>{text.solo}</h2>
              <p>Tải video hoặc chia sẻ màn hình. OCR sẽ giúp bạn nhận diện, dịch và lưu từ mới.</p>
              <span className="mode-link">{text.start} <Icon name="chevron" size={16} /></span>
              <span className="card-number">01</span>
            </MotionButton>
            <MotionButton data-cursor="MỞ" className="mode-card spotlight-card" onPointerMove={tiltCard} onClick={() => setDialog("create")}>
              <span className="card-scene scene-create" aria-hidden="true"><span className="scene-glyph">語</span><span className="scene-caption">LEARN TOGETHER</span><i /><i /><i /></span>
              <span className="mode-icon coral"><Icon name="plus" size={25} /></span>
              <h2>{text.create}</h2>
              <p>Mời bạn bè cùng xem, trò chuyện và xây dựng bộ từ vựng chung trong một phòng riêng.</p>
              <span className="mode-link">{text.createAction} <Icon name="chevron" size={16} /></span>
              <span className="card-number">02</span>
            </MotionButton>
            <MotionButton data-cursor="MỞ" className="mode-card spotlight-card" onPointerMove={tiltCard} onClick={() => setDialog("join")}>
              <span className="card-scene scene-join" aria-hidden="true"><span className="scene-glyph">話</span><span className="scene-caption">A SHARED MOMENT</span><i /><i /><i /></span>
              <span className="mode-icon violet"><Icon name="people" size={25} /></span>
              <h2>{text.join}</h2>
              <p>Nhập mã mời để tham gia ngay vào buổi học đang diễn ra cùng bạn bè.</p>
              <span className="mode-link">{text.joinAction} <Icon name="chevron" size={16} /></span>
              <span className="card-number">03</span>
            </MotionButton>
            <MotionButton data-cursor="XEM" className="mode-card history-mode spotlight-card" onPointerMove={tiltCard} onClick={() => goTo("history")}>
              <span className="card-scene scene-history" aria-hidden="true"><span className="scene-glyph">学</span><span className="scene-caption">YOUR LEARNING STORY</span><i /><i /><i /></span>
              <span className="mode-icon amber"><Icon name="history" size={25} /></span>
              <div className="last-session">
                <small>Buổi gần nhất</small>
                <strong>Khám phá Tokyo về đêm</strong>
                <span>Hôm qua · 38 phút · 12 từ mới</span>
              </div>
              <h2>{text.logs}</h2>
              <p>Xem lại video, bản dịch và những từ bạn đã lưu trong các buổi học trước.</p>
              <span className="mode-link">{text.historyAction} <Icon name="chevron" size={16} /></span>
              <span className="card-number">04</span>
            </MotionButton>
          </section>

          <section className="quick-tip">
            <Icon name="sparkles" size={18} />
            <span className="rotating-tip" key={tipIndex}><strong>Mẹo nhỏ:</strong> {[
              "Bạn có thể nhấp vào bất kỳ từ nào OCR nhận diện trên video để nghe phát âm và lưu vào thư viện.",
              "Ôn lại từ mới sau mỗi buổi học giúp bạn ghi nhớ lâu hơn.",
              "Bật phụ đề song ngữ khi cần, rồi thử nghe lại mà không nhìn bản dịch.",
            ][tipIndex]}</span>
          </section>
        </main>
      ) : screen === "history" ? (
        <main className="workspace page-workspace">
          <section className="page-heading">
            <div><div className="eyebrow">Tiến trình của bạn</div><h1>Nhật ký học tập</h1><p>Xem lại nội dung và tiếp tục những buổi học gần đây.</p></div>
            <MotionButton magnetic className="primary-action spark-action" onClick={() => goTo("lobby")}><Icon name="plus" size={17} /> Buổi học mới</MotionButton>
          </section>
          <div className="stats-row">
            <article className="spotlight-card"><span>Thời gian học</span><strong>8.4<small> giờ</small></strong><b>+12% tuần này</b><i className="mini-chart" /></article>
            <article className="spotlight-card"><span>Từ đã lưu</span><strong>124</strong><b>18 từ mới</b><i className="mini-chart chart-two" /></article>
            <article className="spotlight-card"><span>Chuỗi hiện tại</span><strong>12<small> ngày</small></strong><b>Kỷ lục: 18 ngày</b><i className="mini-chart chart-three" /></article>
          </div>
          <section className="session-list">
            <div className="section-title"><h2>Các buổi gần đây</h2><span>{previousSessions.length} buổi học</span></div>
            {previousSessions.map((session, index) => (
              <article className={`session-row session-${index + 1}`} key={session.title}>
                <div className={`session-thumb thumb-${index + 1}`}><Icon name={index === 0 ? "captions" : index === 1 ? "message" : "headphones"} size={24} /></div>
                <div className="session-name"><small>{session.date}</small><strong>{session.title}</strong><span>{session.language}</span></div>
                <div className="session-meta"><span><Icon name="clock" size={15} /> {session.duration}</span><span><Icon name="book" size={15} /> {session.words} từ</span></div>
                <div className="session-preview"><span>{index === 0 ? "東京 · 喫茶店" : index === 1 ? "bonjour · merci" : "coffee · subway"}</span></div>
                <button onClick={() => enterRoom("solo", session.title)}>Xem lại <Icon name="chevron" size={15} /></button>
              </article>
            ))}
          </section>
        </main>
      ) : screen === "library" ? (
        <main className="workspace page-workspace">
          <section className="page-heading">
            <div><div className="eyebrow">Bộ sưu tập cá nhân</div><h1>Thư viện từ vựng</h1><p>Ôn lại những từ bạn đã bắt gặp trong các video.</p></div>
            <MotionButton magnetic className="primary-action spark-action" onClick={() => goTo("lobby")}><Icon name="play" size={17} /> Bắt đầu luyện</MotionButton>
          </section>
          <div className="library-grid">
            {[
              { title: "Tiếng Nhật giao tiếp", count: 48, level: "N4", tone: "green" },
              { title: "Tiếng Pháp du lịch", count: 31, level: "A2", tone: "coral" },
              { title: "Tiếng Anh hằng ngày", count: 45, level: "B1", tone: "violet" },
            ].map((collection) => (
              <article className={`collection-card ${collection.tone}`} data-cursor="LẬT" key={collection.title}>
                <span className="collection-icon"><Icon name="book" size={23} /></span>
                <small>{collection.level} · BỘ TỪ</small>
                <h2>{collection.title}</h2>
                <p>{collection.count} từ vựng đã lưu</p>
                <span className="deck-progress" style={{ "--deck-progress": `${Math.min(82, collection.count + 25)}%` } as React.CSSProperties}><b>{Math.min(82, collection.count + 25)}%</b></span>
                <button>Ôn tập ngay <Icon name="chevron" size={15} /></button>
              </article>
            ))}
          </div>
        </main>
      ) : (
      <main className="workspace room-workspace">
        <div className="learning-grid">
          <section className="video-column">
            <div className="video-frame">
              <img
                src="https://images.unsplash.com/photo-1564284369929-026ba231f89b?crop=entropy&cs=tinysrgb&fit=crop&fm=jpg&q=86&w=1600&h=1000"
                alt="Một cửa hàng Nhật Bản với đèn lồng vào buổi tối"
              />
              <div className="video-shade" />
              <div className="video-top">
                <span className="ocr-status"><Icon name="sparkles" size={15} /> OCR đang nhận diện</span>
                <span className="quality-pill">HD</span>
              </div>

              <button className={`ocr-box ocr-box-one ${selectedWord === "居酒屋" ? "selected" : ""}`} onClick={() => setSelectedWord(selectedWord === "居酒屋" ? null : "居酒屋")} aria-expanded={selectedWord === "居酒屋"}>
                <span>居酒屋</span>
                <small>izakaya · quán nhậu</small>
              </button>
              <button className={`ocr-box ocr-box-two ${selectedWord === "営業中" ? "selected" : ""}`} onClick={() => setSelectedWord(selectedWord === "営業中" ? null : "営業中")} aria-expanded={selectedWord === "営業中"}>
                <span>営業中</span>
                <small>đang mở cửa</small>
              </button>

              {inspectedWord && <div className="word-inspector" role="region" aria-label="Từ đang chọn">
                <button className="inspector-close" aria-label="Đóng từ đang chọn" onClick={() => setSelectedWord(null)}><Icon name="x" size={16} /></button>
                <span className="inspector-label">TỪ ĐANG CHỌN</span><strong>{inspectedWord.word}</strong><small>{inspectedWord.reading}</small><p>{inspectedWord.meaning}</p>
                <div><button disabled={!("speechSynthesis" in window)} onClick={() => pronounce(inspectedWord.word)}><Icon name="volume" size={16} /> Nghe</button><button onClick={() => setSavedWords(current => current.some(item => item.word === inspectedWord.word) ? current : [...current, inspectedWord])} disabled={savedWords.some(item => item.word === inspectedWord.word)}><Icon name="plus" size={16} />{savedWords.some(item => item.word === inspectedWord.word) ? "Đã lưu" : "Lưu từ"}</button></div>
              </div>}

              <div className="subtitle">
                <span>すみません、この近くにおすすめのカフェはありますか？</span>
                <p>Xin lỗi, gần đây có quán cà phê nào bạn đề xuất không?</p>
              </div>

              <div className="video-controls">
                <button onClick={() => setPlaying(!playing)} aria-label={playing ? "Tạm dừng" : "Phát"}>
                  {playing ? <span className="pause-icon" /> : <Icon name="play" size={22} />}
                </button>
                <button aria-label="Âm lượng"><Icon name="volume" size={21} /></button>
                <span className="timecode">{playing ? "01:47" : "01:42"} / 08:24</span>
                <div className="timeline"><span style={{ width: playing ? "25%" : "21%" }} /></div>
                <button aria-label="Phụ đề"><Icon name="captions" size={21} /></button>
                <button aria-label="Toàn màn hình"><span className="fullscreen-icon" /></button>
              </div>
            </div>

            <div className="call-bar">
              <div className="room-code">
                <span>Mã phòng</span>
                <strong>LINGO-3821</strong>
                <button onClick={copyRoom}><Icon name="copy" size={16} /> {copied ? "Đã chép" : ""}</button>
              </div>
              <div className="call-controls">
                <button className={!micOn ? "off" : ""} onClick={() => setMicOn(!micOn)} aria-label="Bật tắt micro">
                  <Icon name={micOn ? "mic" : "x"} />
                </button>
                <button className={!cameraOn ? "off" : ""} onClick={() => setCameraOn(!cameraOn)} aria-label="Bật tắt camera">
                  <Icon name={cameraOn ? "camera" : "x"} />
                </button>
                <button className="leave-call" onClick={() => goTo("lobby")}>Rời phòng</button>
              </div>
              <div className="participants-label"><Icon name="people" size={18} /> 5 người tham gia</div>
            </div>
          </section>

          <aside className="side-panel">
            <div className="panel-tabs">
              <button className={panel === "transcript" ? "active" : ""} onClick={() => setPanel("transcript")}>
                Phiên âm
              </button>
              <button className={panel === "chat" ? "active" : ""} onClick={() => setPanel("chat")}>
                Trò chuyện <span>3</span>
              </button>
            </div>

            {panel === "transcript" ? (
              <div className="transcript-panel">
                <div className="panel-label"><span>Nội dung trực tiếp</span><button><Icon name="sparkles" size={15} /> Dịch tự động</button></div>
                <TranscriptVocabulary lines={transcript} savedWords={savedWords.map(item => item.word)} onSpeak={pronounce} onSave={entry => {
                  const word = entry.lemma || entry.word;
                  setSavedWords(current => current.some(item => item.word === word) ? current : [...current, { word, reading: entry.lemmaReading || entry.kana, meaning: entry.lemmaMeaning || entry.meaning, color: "coral" }]);
                }} />
                <div className="listening-card">
                  <span className="sound-wave"><i /><i /><i /><i /><i /></span>
                  <div><strong>Đang lắng nghe...</strong><small>Lời thoại sẽ xuất hiện tại đây</small></div>
                </div>
              </div>
            ) : (
              <div className="chat-panel">
                <div className="chat-message">
                  <span className="mini-avatar violet">AN</span>
                  <div><b>Anh</b><small>01:38</small><p>Mọi người nghe rõ không?</p></div>
                </div>
                <div className="chat-message">
                  <span className="mini-avatar green">JL</span>
                  <div><b>Julia</b><small>01:40</small><p>Rõ lắm! Từ trên biển hiệu vừa rồi rất hay.</p></div>
                </div>
                <div className="chat-message mine">
                  <div><b>Bạn</b><small>01:41</small><p>Mình đã lưu vào danh sách từ vựng rồi.</p></div>
                </div>
                <div className="chat-input"><input placeholder="Nhắn tin cho cả phòng..." /><button><Icon name="send" size={18} /></button></div>
              </div>
            )}

            <div className="vocab-section">
              <div className="vocab-header">
                <div><span>Từ vựng đã lưu</span><b>{savedWords.length}</b></div>
                <button><Icon name="chevron" size={17} /></button>
              </div>
              <div className="word-list">
                {savedWords.map((item) => (
                  <article className={`word-card ${selectedWord === item.word ? "selected" : ""}`} key={item.word}>
                    <span className={`word-accent ${item.color}`} />
                    <button className="word-main" onClick={() => setSelectedWord(item.word)} aria-label={`Xem từ ${item.word}`}><strong>{item.word}</strong><small>{item.reading}</small></button>
                    <span className="word-meaning">{item.meaning}</span>
                    <button className="word-audio" disabled={!("speechSynthesis" in window)} onClick={() => pronounce(item.word)} aria-label={`Nghe ${item.word}`}><Icon name="volume" size={15} /></button>
                    <button onClick={() => setSavedWords(savedWords.filter((word) => word.word !== item.word))} aria-label={`Xóa ${item.word}`}>
                      <Icon name="x" size={15} />
                    </button>
                  </article>
                ))}
                {savedWords.length === 0 && <p className="empty-state">Chọn từ trên video để lưu lại.</p>}
              </div>
              <button className="review-button"><Icon name="book" size={18} /> Ôn tập {savedWords.length} từ</button>
            </div>
          </aside>
        </div>
      </main>
      )}

      {dialog && (
        <div className="dialog-backdrop" role="presentation" onMouseDown={() => setDialog(null)}>
          <section className="room-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onMouseDown={(event) => event.stopPropagation()}>
            <button className="dialog-close" onClick={() => setDialog(null)} aria-label="Đóng"><Icon name="x" size={19} /></button>
            <span className={`dialog-icon ${dialog === "join" ? "violet" : ""}`}>
              <Icon name={dialog === "create" ? "plus" : "people"} size={25} />
            </span>
            <small>{dialog === "create" ? "PHÒNG HỌC MỚI" : "THAM GIA CÙNG BẠN BÈ"}</small>
            <h2 id="dialog-title">{dialog === "create" ? "Tạo phòng học" : "Nhập mã phòng"}</h2>
            <p>{dialog === "create" ? "Thiết lập một không gian học và chia sẻ mã mời với bạn bè." : "Mã phòng gồm 10 ký tự và được gửi bởi người tạo phòng."}</p>
            {dialog === "create" ? (
              <form onSubmit={(event) => { event.preventDefault(); enterRoom("group", roomTitle || "Phòng học mới"); }}>
                <label>Tên phòng<input value={roomTitle} onChange={(event) => setRoomTitle(event.target.value)} placeholder="Ví dụ: Luyện nghe tối thứ 6" autoFocus /></label>
                <label>Ngôn ngữ
                  <select defaultValue="ja"><option value="ja">Tiếng Nhật</option><option value="en">Tiếng Anh</option><option value="fr">Tiếng Pháp</option></select>
                </label>
                <div className="dialog-options"><span>Cho phép thành viên lưu từ chung</span><input type="checkbox" defaultChecked /></div>
                <button className="dialog-submit" type="submit">Tạo phòng và tiếp tục <Icon name="chevron" size={16} /></button>
              </form>
            ) : (
              <form onSubmit={(event) => { event.preventDefault(); if (joinCode.trim()) enterRoom("group"); }}>
                <label>Mã phòng
                  <input className="code-input" value={joinCode} onChange={(event) => setJoinCode(event.target.value.toUpperCase())} placeholder="LINGO-3821" autoFocus />
                </label>
                <button className="dialog-submit" type="submit" disabled={!joinCode.trim()}>Tham gia phòng <Icon name="chevron" size={16} /></button>
                <span className="dialog-help">Chưa có mã? Hãy nhờ chủ phòng gửi liên kết mời.</span>
              </form>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
