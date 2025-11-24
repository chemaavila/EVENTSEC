const CorrelationRulesPage = () => {
  const rules = [
    {
      id: "CR-001",
      name: "Phishing alert + risky sign-in",
      status: "Enabled",
      severity: "high",
    },
    {
      id: "CR-002",
      name: "EDR alert + outbound C2 traffic",
      status: "Enabled",
      severity: "critical",
    },
  ] as const;

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Correlation rules</div>
          <div className="page-subtitle">
            High-level rules combining multiple detections into a single alert.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Rules</div>
            <div className="card-subtitle">
              Static rules representing how events from different tools are merged.
            </div>
          </div>
        </div>

        <div className="stack-vertical">
          {rules.map((rule) => (
            <div key={rule.id} className="alert-row">
              <div className="alert-row-main">
                <div className="alert-row-title">
                  {rule.id}
                  {" "}
                  —{" "}
                  {rule.name}
                </div>
                <div className="alert-row-meta">
                  <span className="tag">Correlation</span>
                  <span className="tag">Multi-signal</span>
                </div>
              </div>
              <div className="stack-horizontal">
                <span
                  className={[
                    "severity-pill",
                    `severity-${rule.severity}`,
                  ].join(" ")}
                >
                  {rule.severity.toUpperCase()}
                </span>
                <span className="badge">{rule.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CorrelationRulesPage;
