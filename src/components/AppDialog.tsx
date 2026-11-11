import { useEffect, useId, useRef, type ReactNode } from "react";
import "./AppDialog.css";

type Props = { title: string; description?: string; children: ReactNode; onClose: () => void; wide?: boolean };
export default function AppDialog({ title, description, children, onClose, wide = false }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const id = useId();
  useEffect(() => {
    const dialog = ref.current;
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog?.showModal();
    return () => { dialog?.close(); document.body.style.overflow = overflow; previous?.focus({ preventScroll: true }); };
  }, []);
  return <dialog ref={ref} className={`app-dialog ${wide ? "app-dialog-wide" : ""}`} aria-labelledby={id} aria-describedby={description ? `${id}-description` : undefined} onCancel={event => { event.preventDefault(); closeRef.current(); }} onClick={event => { if (event.target === event.currentTarget) { const r = event.currentTarget.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) closeRef.current(); } }}>
    <header className="app-dialog-heading"><div><span className="app-dialog-eyebrow">LINGUALIVE</span><h2 id={id}>{title}</h2></div><button className="app-dialog-close" type="button" aria-label="Đóng hộp thoại" onClick={onClose}>×</button></header>
    {description && <p id={`${id}-description`} className="app-dialog-description">{description}</p>}
    {children}
  </dialog>;
}
