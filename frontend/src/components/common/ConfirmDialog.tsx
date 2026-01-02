import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

type ConfirmTone = "default" | "danger";

type ConfirmOptions = {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ConfirmTone;
};

type ConfirmContextValue = {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
};

const ConfirmContext = createContext<ConfirmContextValue | null>(null);

export const ConfirmProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [current, setCurrent] = useState<ConfirmOptions | null>(null);
  const resolverRef = useRef<(value: boolean) => void>();
  const dialogRef = useRef<HTMLDivElement | null>(null);

  const confirm = useCallback((options: ConfirmOptions) => {
    setCurrent(options);
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
    });
  }, []);

  const handleClose = useCallback((value: boolean) => {
    resolverRef.current?.(value);
    resolverRef.current = undefined;
    setCurrent(null);
  }, []);

  const value = useMemo(() => ({ confirm }), [confirm]);

  useEffect(() => {
    if (!current || !dialogRef.current) return;
    const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
    );
    focusable[0]?.focus();
  }, [current]);

  return (
    <ConfirmContext.Provider value={value}>
      {children}
      {current && (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={() => handleClose(false)}
        >
          <div
            className="modal-content confirm-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirm-title"
            aria-describedby="confirm-message"
            ref={dialogRef}
            onClick={(event) => event.stopPropagation()}
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                handleClose(false);
              }
              if (event.key === "Tab" && dialogRef.current) {
                const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
                  "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
                );
                const elements = Array.from(focusable).filter((el) => !el.hasAttribute("disabled"));
                if (elements.length === 0) return;
                const first = elements[0];
                const last = elements[elements.length - 1];
                if (event.shiftKey && document.activeElement === first) {
                  event.preventDefault();
                  last.focus();
                } else if (!event.shiftKey && document.activeElement === last) {
                  event.preventDefault();
                  first.focus();
                }
              }
            }}
          >
            <div className="modal-header">
              <div>
                <div className="modal-title" id="confirm-title">
                  {current.title}
                </div>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => handleClose(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <p id="confirm-message">{current.message}</p>
              <div className="confirm-actions">
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => handleClose(false)}
                >
                  {current.cancelLabel ?? "Cancel"}
                </button>
                <button
                  type="button"
                  className={`btn ${current.tone === "danger" ? "btn-danger" : ""}`}
                  onClick={() => handleClose(true)}
                >
                  {current.confirmLabel ?? "Confirm"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
};

export const useConfirm = () => {
  const ctx = useContext(ConfirmContext);
  if (!ctx) {
    throw new Error("useConfirm must be used within ConfirmProvider");
  }
  return ctx;
};
