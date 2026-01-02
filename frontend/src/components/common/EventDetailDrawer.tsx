import { useEffect, useMemo, useRef } from "react";

type DetailField = {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
};

type EventDetailDrawerProps = {
  title: string;
  subtitle?: string;
  fields: DetailField[];
  rawJson: unknown;
  isOpen: boolean;
  onClose: () => void;
};

export const EventDetailDrawer: React.FC<EventDetailDrawerProps> = ({
  title,
  subtitle,
  fields,
  rawJson,
  isOpen,
  onClose,
}) => {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const jsonText = useMemo(() => JSON.stringify(rawJson ?? {}, null, 2), [rawJson]);

  useEffect(() => {
    if (!isOpen || !panelRef.current) return;
    const focusable = panelRef.current.querySelectorAll<HTMLElement>(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
    );
    focusable[0]?.focus();
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="drawer-backdrop" role="presentation" onClick={onClose}>
      <div
        className="drawer-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="event-drawer-title"
        aria-describedby="event-drawer-subtitle"
        ref={panelRef}
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            onClose();
          }
          if (event.key === "Tab" && panelRef.current) {
            const focusable = panelRef.current.querySelectorAll<HTMLElement>(
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
        <div className="drawer-header">
          <div>
            <div className="drawer-title" id="event-drawer-title">
              {title}
            </div>
            {subtitle && (
              <div className="drawer-subtitle" id="event-drawer-subtitle">
                {subtitle}
              </div>
            )}
          </div>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="drawer-body">
          <div className="drawer-fields">
            {fields.map((field) => (
              <div key={field.label} className="drawer-field">
                <div className="drawer-field-label">{field.label}</div>
                <div className={`drawer-field-value ${field.mono ? "mono" : ""}`}>
                  {field.value}
                </div>
              </div>
            ))}
          </div>

          <div className="drawer-json">
            <div className="drawer-json-header">
              <div className="drawer-json-title">Raw payload</div>
              <div className="stack-horizontal">
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => navigator.clipboard.writeText(jsonText)}
                >
                  Copy JSON
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => {
                    const blob = new Blob([jsonText], { type: "application/json" });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = "event.json";
                    link.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  Download JSON
                </button>
              </div>
            </div>
            <pre className="drawer-json-body">{jsonText}</pre>
          </div>
        </div>
      </div>
    </div>
  );
};
