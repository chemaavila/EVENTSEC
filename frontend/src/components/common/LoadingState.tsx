type LoadingStateProps = {
  message?: string;
};

export const LoadingState: React.FC<LoadingStateProps> = ({ message = "Loading…" }) => (
  <div className="state state-loading" role="status" aria-live="polite">
    <div className="state-spinner" aria-hidden="true" />
    <div className="state-text">{message}</div>
  </div>
);
