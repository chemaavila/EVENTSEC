import { useEffect, useMemo, useState } from "react";
import {
  getRuleLibraryEntry,
  listRuleLibrary,
  updateRuleLibraryEntry,
  type RuleEntry,
} from "../services/api";
import { useToast } from "../components/common/ToastProvider";
import { LoadingState } from "../components/common/LoadingState";
import { ErrorState } from "../components/common/ErrorState";

const RuleLibraryPage = () => {
  const [activeTab, setActiveTab] = useState<"analytic" | "correlation">("analytic");
  const [rules, setRules] = useState<RuleEntry[]>([]);
  const [selectedRule, setSelectedRule] = useState<RuleEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const { pushToast } = useToast();

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await listRuleLibrary({ type: activeTab, search });
      setRules(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load rules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules().catch((err) => console.error(err));
  }, [activeTab, search]);

  const handleSelectRule = async (ruleId: number) => {
    try {
      const entry = await getRuleLibraryEntry(ruleId, activeTab);
      setSelectedRule(entry);
    } catch (err) {
      pushToast({
        title: "Failed to load rule",
        message: "Please try again.",
        details: err instanceof Error ? err.message : "Unknown error",
        variant: "error",
      });
    }
  };

  const handleToggleEnabled = async (rule: RuleEntry) => {
    try {
      const updated = await updateRuleLibraryEntry(rule.id, activeTab, {
        enabled: !rule.enabled,
      });
      setRules((prev) => prev.map((entry) => (entry.id === rule.id ? updated : entry)));
      if (selectedRule?.id === rule.id) {
        setSelectedRule(updated);
      }
    } catch (err) {
      pushToast({
        title: "Failed to update rule",
        message: "Please try again.",
        details: err instanceof Error ? err.message : "Unknown error",
        variant: "error",
      });
    }
  };

  const filteredRules = useMemo(() => {
    if (!search.trim()) return rules;
    const term = search.trim().toLowerCase();
    return rules.filter((rule) => rule.title.toLowerCase().includes(term));
  }, [rules, search]);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Rule library</div>
          <div className="page-subtitle">
            Manage analytic and correlation rules seeded into EventSec.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="stack-horizontal" style={{ gap: "0.75rem" }}>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === "analytic" ? "" : "btn-ghost"}`}
            onClick={() => setActiveTab("analytic")}
          >
            Analytic rules
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === "correlation" ? "" : "btn-ghost"}`}
            onClick={() => setActiveTab("correlation")}
          >
            Correlation rules
          </button>
          <input
            className="field-control"
            placeholder="Search rules"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </div>

      {error && (
        <ErrorState
          message="Failed to load rules."
          details={error}
          onRetry={() => loadRules()}
        />
      )}

      <div className="grid-2">
        <div className="card">
          {loading ? (
            <LoadingState message="Loading rules…" />
          ) : filteredRules.length === 0 ? (
            <div className="muted">No rules available.</div>
          ) : (
            <div className="stack-vertical">
              {filteredRules.map((rule) => (
                <div key={rule.id} className="card sandbox-mini">
                  <div className="stack-horizontal" style={{ justifyContent: "space-between" }}>
                    <div>
                      <div className="card-title">{rule.title}</div>
                      <div className="muted small">{rule.description}</div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => handleToggleEnabled(rule)}
                    >
                      {rule.enabled ? "Disable" : "Enable"}
                    </button>
                  </div>
                  <div className="stack-horizontal" style={{ justifyContent: "space-between" }}>
                    <div className="muted small">Severity: {rule.severity}</div>
                    <button
                      type="button"
                      className="btn btn-sm"
                      onClick={() => handleSelectRule(rule.id)}
                    >
                      View
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          {selectedRule ? (
            <div className="stack-vertical">
              <div className="card-title">{selectedRule.title}</div>
              <div className="muted">{selectedRule.description}</div>
              <div className="muted">Severity: {selectedRule.severity}</div>
              {selectedRule.category && (
                <div className="muted">Category: {selectedRule.category}</div>
              )}
              {selectedRule.tags.length > 0 && (
                <div className="stack-horizontal" style={{ gap: "0.4rem", flexWrap: "wrap" }}>
                  {selectedRule.tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              <button
                type="button"
                className="btn btn-ghost"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(
                      JSON.stringify(selectedRule, null, 2)
                    );
                    pushToast({
                      title: "Rule copied",
                      message: "Rule JSON copied to clipboard.",
                      variant: "success",
                    });
                  } catch (err) {
                    pushToast({
                      title: "Copy failed",
                      message: "Unable to copy rule JSON.",
                      details: err instanceof Error ? err.message : "Unknown error",
                      variant: "error",
                    });
                  }
                }}
              >
                Copy JSON
              </button>
              <pre className="code-block" style={{ whiteSpace: "pre-wrap" }}>
                {JSON.stringify(selectedRule, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="muted">Select a rule to see the full definition.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RuleLibraryPage;
