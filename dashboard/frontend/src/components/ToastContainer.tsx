import { useEffect } from "react";
import { useUIStore } from "../stores/uiStore";

const COLOR = {
  ok: "bg-emerald-700",
  info: "bg-blue-700",
  warn: "bg-amber-700",
  err: "bg-red-700"
} as const;

export function ToastContainer() {
  const toasts = useUIStore(s => s.toasts);
  const dismiss = useUIStore(s => s.dismissToast);

  useEffect(() => {
    const timers = toasts.map(t => setTimeout(() => dismiss(t.id), 4000));
    return () => timers.forEach(clearTimeout);
  }, [toasts, dismiss]);

  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map(t => (
        <div
          key={t.id}
          className={`${COLOR[t.kind]} text-white text-sm px-3 py-2 rounded shadow`}
        >
          {t.msg}
        </div>
      ))}
    </div>
  );
}
