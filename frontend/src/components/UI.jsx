import { createContext, useContext, useState } from "react";
import {
  X,
  CheckCircle2,
  AlertCircle,
  Inbox,
  LoaderCircle,
} from "lucide-react";
const ToastContext = createContext(null);
export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);
  const notify = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 6000);
  };
  return (
    <ToastContext.Provider value={notify}>
      {children}
      {toast && (
        <div role="status" className={`toast ${toast.type}`}>
          {toast.type === "error" ? (
            <AlertCircle size={19} />
          ) : (
            <CheckCircle2 size={19} />
          )}
          <span>{toast.message}</span>
          <button
            aria-label="Dismiss notification"
            onClick={() => setToast(null)}
          >
            <X size={16} />
          </button>
        </div>
      )}
    </ToastContext.Provider>
  );
}
export const useToast = () => useContext(ToastContext);
export function Button({
  children,
  variant = "primary",
  loading = false,
  ...props
}) {
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={`button ${variant} ${props.className || ""}`}
    >
      {loading && <LoaderCircle size={16} className="spin" />}
      {children}
    </button>
  );
}
export function Field({ label, children, ...props }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children || <input {...props} />}
    </label>
  );
}
export function Badge({ children, tone = "" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
export function Empty({
  title = "Nothing here yet",
  description = "Your next step will appear here.",
  children,
}) {
  return (
    <div className="empty">
      <Inbox size={32} />
      <h3>{title}</h3>
      <p>{description}</p>
      {children}
    </div>
  );
}
export function Loading() {
  return (
    <div aria-label="Loading" className="skeletons">
      {[1, 2, 3].map((i) => (
        <div className="skeleton" key={i} />
      ))}
    </div>
  );
}
export function ErrorState({ message, retry }) {
  return (
    <div role="alert" className="notice error">
      <AlertCircle size={20} />
      <span>{message}</span>
      {retry && (
        <Button variant="secondary" onClick={retry}>
          Try again
        </Button>
      )}
    </div>
  );
}
export function Modal({ title, children, onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <header>
          <h2>{title}</h2>
          <button aria-label="Close dialog" onClick={onClose}>
            <X />
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
export function PageHeader({ eyebrow, title, description, children }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {children && <div className="header-actions">{children}</div>}
    </div>
  );
}
