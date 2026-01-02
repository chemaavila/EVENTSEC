type CtiAdapterFallbackProps = {
  onSwitchToMock?: () => void;
};

const CtiAdapterFallback: React.FC<CtiAdapterFallbackProps> = ({ onSwitchToMock }) => (
  <div className="cti-shell">
    <div className="card" style={{ margin: "2rem auto", maxWidth: 680 }}>
      <div className="card-title">CTI API adapter not implemented</div>
      <div className="card-subtitle">
        The CTI backend adapter is not configured for this environment. You can switch to mock
        data to explore the UI.
      </div>
      {onSwitchToMock && (
        <div className="stack-horizontal" style={{ marginTop: "1.5rem" }}>
          <button type="button" className="btn" onClick={onSwitchToMock}>
            Switch to Mock
          </button>
        </div>
      )}
    </div>
  </div>
);

export default CtiAdapterFallback;
