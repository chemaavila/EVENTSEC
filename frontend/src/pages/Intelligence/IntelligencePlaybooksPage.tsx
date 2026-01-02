import { useEffect, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiPlaybooksData } from "../../services/cti";
import "../../components/cti/cti.css";

const IntelligencePlaybooksPage = () => {
  const [data, setData] = useState<CtiPlaybooksData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  useEffect(() => {
    let mounted = true;
    ctiAdapter
      .getPlaybooks()
      .then((response) => {
        if (mounted) setData(response);
      })
      .catch((err) => {
        console.error(err);
        if (mounted && err instanceof CtiNotImplementedError) {
          setAdapterUnavailable(true);
          return;
        }
        if (mounted) setError("Unable to load playbooks.");
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (adapterUnavailable) {
    return (
      <CtiAdapterFallback
        onSwitchToMock={() => {
          window.localStorage.setItem("cti_use_mock", "true");
          window.location.reload();
        }}
      />
    );
  }

  if (!data) {
    return (
      <div className="cti-playbooks-shell">
        <div className="cti-placeholder">
          <h1>Playbooks</h1>
          <p>{error ?? "Loading playbooks..."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cti-playbooks-shell">
      <header className="cti-playbooks-topbar">
        <div className="cti-playbooks-topbar-left">
          <div className="cti-playbooks-brand">
            <div className="cti-playbooks-brand-icon">
              <svg viewBox="0 0 48 48" aria-hidden="true">
                <path
                  clipRule="evenodd"
                  d="M39.475 21.6262C40.358 21.4363 40.6863 21.5589 40.7581 21.5934C40.7876 21.655 40.8547 21.857 40.8082 22.3336C40.7408 23.0255 40.4502 24.0046 39.8572 25.2301C38.6799 27.6631 36.5085 30.6631 33.5858 33.5858C30.6631 36.5085 27.6632 38.6799 25.2301 39.8572C24.0046 40.4502 23.0255 40.7407 22.3336 40.8082C21.8571 40.8547 21.6551 40.7875 21.5934 40.7581C21.5589 40.6863 21.4363 40.358 21.6262 39.475C21.8562 38.4054 22.4689 36.9657 23.5038 35.2817C24.7575 33.2417 26.5497 30.9744 28.7621 28.762C30.9744 26.5497 33.2417 24.7574 35.2817 23.5037C36.9657 22.4689 38.4054 21.8562 39.475 21.6262ZM4.41189 29.2403L18.7597 43.5881C19.8813 44.7097 21.4027 44.9179 22.7217 44.7893C24.0585 44.659 25.5148 44.1631 26.9723 43.4579C29.9052 42.0387 33.2618 39.5667 36.4142 36.4142C39.5667 33.2618 42.0387 29.9052 43.4579 26.9723C44.1631 25.5148 44.659 24.0585 44.7893 22.7217C44.9179 21.4027 44.7097 19.8813 43.5881 18.7597L29.2403 4.41187C27.8527 3.02428 25.8765 3.02573 24.2861 3.36776C22.6081 3.72863 20.7334 4.58419 18.8396 5.74801C16.4978 7.18716 13.9881 9.18353 11.5858 11.5858C9.18354 13.988 7.18717 16.4978 5.74802 18.8396C4.58421 20.7334 3.72865 22.6081 3.36778 24.2861C3.02574 25.8765 3.02429 27.8527 4.41189 29.2403Z"
                  fill="currentColor"
                  fillRule="evenodd"
                />
              </svg>
            </div>
            <h1>Sentinela XDR</h1>
          </div>
          <div className="cti-playbooks-divider" />
          <nav className="cti-playbooks-nav">
            {[
              { label: "Dashboard", active: false },
              { label: "Threat Intel", active: false },
              { label: "Playbooks", active: true },
              { label: "Incidents", active: false },
            ].map((item) => (
              <a key={item.label} className={item.active ? "active" : ""} href="#">
                {item.label}
              </a>
            ))}
          </nav>
        </div>
        <div className="cti-playbooks-topbar-right">
          <div className="cti-playbooks-search">
            <span className="material-symbols-outlined">search</span>
            <input placeholder="Search playbooks..." />
          </div>
          <button type="button">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <div className="cti-playbooks-avatar" />
        </div>
      </header>

      <div className="cti-playbooks-body">
        <aside className="cti-playbooks-sidebar">
          <div className="cti-playbooks-sidebar-items">
            {[
              { icon: "library_books", label: "Library", active: true },
              { icon: "history", label: "Run History" },
              { icon: "api", label: "Connectors" },
              { icon: "settings", label: "Settings" },
            ].map((item) => (
              <div key={item.label} className={item.active ? "cti-playbooks-sidebar-item active" : "cti-playbooks-sidebar-item"}>
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="label">{item.label}</span>
              </div>
            ))}
          </div>
          <div className="cti-playbooks-quota">
            <div className="cti-playbooks-quota-header">
              <span>Quota Usage</span>
              <strong>{data.quotaUsage}%</strong>
            </div>
            <div className="cti-playbooks-quota-bar">
              <span style={{ width: `${data.quotaUsage}%` }} />
            </div>
            <p>{data.quotaLabel}</p>
          </div>
        </aside>

        <main className="cti-playbooks-main">
          <div className="cti-playbooks-header">
            <div>
              <div className="cti-playbooks-title">
                <h2>{data.title}</h2>
                <span>{data.status}</span>
              </div>
              <p>{data.description}</p>
            </div>
            <div className="cti-playbooks-header-actions">
              <button type="button">
                <span className="material-symbols-outlined">play_arrow</span>
                Test Run
              </button>
              <button className="primary" type="button">
                <span className="material-symbols-outlined">save</span>
                Save Changes
              </button>
            </div>
          </div>

          <div className="cti-playbooks-workspace">
            <div className="cti-playbooks-canvas">
              <div className="cti-playbooks-toolbar">
                {["near_me", "add_box", "fit_screen", "undo"].map((icon) => (
                  <button key={icon} type="button">
                    <span className="material-symbols-outlined">{icon}</span>
                  </button>
                ))}
              </div>
              <div className="cti-playbooks-flow">
                {data.steps.map((step) => (
                  <div key={step.id} className="cti-playbooks-node">
                    <div className="cti-playbooks-node-header">
                      <div className="badge" style={{ color: step.accent }}>
                        <span className="material-symbols-outlined">{step.icon}</span>
                        {step.label}
                      </div>
                      <span className="material-symbols-outlined">more_horiz</span>
                    </div>
                    <h4>{step.title}</h4>
                    <p>{step.subtitle}</p>
                  </div>
                ))}

                <div className="cti-playbooks-branches">
                  {data.branches.map((branch) => (
                    <div key={branch.id} className="cti-playbooks-branch" style={{ borderColor: branch.accent }}>
                      <div className="pill" style={{ background: branch.accent }}>
                        {branch.label}
                      </div>
                      <div className="cti-playbooks-node-header">
                        <div className="badge" style={{ color: branch.accent }}>
                          <span className="material-symbols-outlined">{branch.icon}</span>
                          Action
                        </div>
                      </div>
                      <h4>{branch.title}</h4>
                      <p>{branch.subtitle}</p>
                    </div>
                  ))}
                </div>

                <div className="cti-playbooks-add">
                  <button type="button">
                    <span className="material-symbols-outlined">add</span>
                  </button>
                  <span>Add Step</span>
                </div>
              </div>
            </div>

            <aside className="cti-playbooks-library">
              <div className="cti-playbooks-library-tabs">
                <button className="active" type="button">
                  Components
                </button>
                <button type="button">Properties</button>
              </div>
              <div className="cti-playbooks-library-body">
                <h5>Logic &amp; Flow</h5>
                <div className="cti-playbooks-library-grid">
                  {data.components.logic.map((item) => (
                    <div key={item.id} className="cti-playbooks-library-card">
                      <span className="material-symbols-outlined">{item.icon}</span>
                      <span>{item.title}</span>
                    </div>
                  ))}
                </div>
                <h5>Actions</h5>
                <div className="cti-playbooks-library-grid">
                  {data.components.actions.map((item) => (
                    <div key={item.id} className="cti-playbooks-library-card">
                      <span className="material-symbols-outlined" style={{ color: item.color }}>
                        {item.icon}
                      </span>
                      <div>
                        <span>{item.title}</span>
                        <small>{item.subtitle}</small>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </div>

          <div className="cti-playbooks-logs">
            <div className="cti-playbooks-logs-header">
              <div>
                <span className="material-symbols-outlined">terminal</span>
                Execution Logs
                <span className="badge">Live</span>
              </div>
              <div>
                <button type="button">
                  <span className="material-symbols-outlined">open_in_full</span>
                </button>
                <button type="button">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>
            </div>
            <div className="cti-playbooks-logs-body">
              <div className="cti-playbooks-log-list">
                <table>
                  <tbody>
                    {data.executions.map((exec) => (
                      <tr key={exec.id} className={exec.active ? "active" : undefined}>
                        <td>
                          <div className="cti-playbooks-log-id">
                            <span className="dot" style={{ background: exec.color }} />
                            <div>
                              <span>{exec.id}</span>
                              <small>{exec.time}</small>
                            </div>
                          </div>
                        </td>
                        <td style={{ textAlign: "right", color: exec.color }}>{exec.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="cti-playbooks-console">
                {data.logLines.map((line, index) => (
                  <p key={`${line.time}-${index}`}>
                    <span className="time">{line.time}</span>
                    <span className={`level ${line.level.toLowerCase()}`}>[{line.level}]</span>
                    {line.message}
                  </p>
                ))}
                <div className="cti-playbooks-exception">{data.exception}</div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default IntelligencePlaybooksPage;
