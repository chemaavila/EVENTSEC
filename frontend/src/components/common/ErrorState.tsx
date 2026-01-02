type ErrorStateProps = {
  title?: string;
  message: string;
  details?: string;
  onRetry?: () => void;
};

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Something went wrong",
  message,
  details,
  onRetry,
}) => (
  <div className="state state-error" role="alert">
    <div className="state-title">{title}</div>
    <div className="state-text">{message}</div>
    {details && (
      <details className="state-details">
        <summary>Details</summary>
        <pre>{details}</pre>
      </details>
    )}
    {onRetry && (
      <div className="state-action">
        <button type="button" className="btn btn-ghost btn-sm" onClick={onRetry}>
          Retry
        </button>
      </div>
    )}
  </div>
);
