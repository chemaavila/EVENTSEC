type EmptyStateProps = {
  title?: string;
  message?: string;
  action?: React.ReactNode;
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "Nothing to show",
  message,
  action,
}) => (
  <div className="state state-empty" role="status" aria-live="polite">
    <div className="state-title">{title}</div>
    {message && <div className="state-text">{message}</div>}
    {action && <div className="state-action">{action}</div>}
  </div>
);
