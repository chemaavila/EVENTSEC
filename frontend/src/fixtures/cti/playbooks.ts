import type { CtiPlaybooksData } from "../../services/cti/types";

export const playbooksFixture: CtiPlaybooksData = {
  title: "Phishing Response",
  status: "Active",
  description: "Automated triage and containment for suspicious emails reported by users.",
  quotaUsage: 84,
  quotaLabel: "2,100 / 2,500 executions",
  steps: [
    {
      id: "trigger",
      label: "Trigger",
      title: "Suspicious Email Reported",
      subtitle: "Source: Outlook Integration",
      icon: "bolt",
      accent: "var(--data-viz1)",
    },
    {
      id: "filter",
      label: "Filter",
      title: "Check Sender Domain",
      subtitle: "Exclude internal domains",
      icon: "filter_alt",
      accent: "var(--text-muted)",
    },
    {
      id: "enrich",
      label: "Enrich",
      title: "Analyze URL Reputation",
      subtitle: "VirusTotal API",
      icon: "travel_explore",
      accent: "var(--data-viz7)",
    },
  ],
  branches: [
    {
      id: "branch-malicious",
      label: "Malicious",
      title: "Block Sender",
      subtitle: "Update Firewall Policy",
      icon: "gavel",
      accent: "var(--data-viz8)",
    },
    {
      id: "branch-safe",
      label: "Safe",
      title: "Close Ticket",
      subtitle: "Notify User: False Positive",
      icon: "check_circle",
      accent: "var(--status-success-text)",
    },
  ],
  components: {
    logic: [
      { id: "filter", title: "Filter", icon: "filter_alt" },
      { id: "branch", title: "Branch", icon: "call_split" },
      { id: "delay", title: "Delay", icon: "schedule" },
    ],
    actions: [
      { id: "enrich", title: "Enrich Data", subtitle: "VT, AlienVault, etc.", icon: "travel_explore", color: "var(--data-viz7)" },
      { id: "notify", title: "Notify", subtitle: "Email, Slack, Teams", icon: "notification_important", color: "var(--data-viz8)" },
      { id: "case", title: "Case Management", subtitle: "Jira, ServiceNow", icon: "confirmation_number", color: "var(--data-viz2)" },
    ],
  },
  executions: [
    { id: "#EXEC-8921", time: "Just now", status: "Failed", color: "var(--status-danger-text)", active: true },
    { id: "#EXEC-8920", time: "15 mins ago", status: "Success", color: "var(--status-success-text)" },
    { id: "#EXEC-8919", time: "1 hour ago", status: "Success", color: "var(--status-success-text)" },
  ],
  logLines: [
    { time: "10:42:01.234", level: "INFO", message: "Playbook execution started. ID: 8921" },
    { time: "10:42:01.256", level: "INFO", message: "Trigger received: Email Event (Outlook)" },
    { time: "10:42:01.412", level: "INFO", message: "Step 'Check Sender Domain' executed. Result: External" },
    { time: "10:42:02.105", level: "INFO", message: "Step 'Analyze URL Reputation' started. Target: http://malicious-site.xyz" },
    { time: "10:42:05.678", level: "ERROR", message: "Connection timed out to VirusTotal API." },
    { time: "10:42:05.680", level: "FATAL", message: "Playbook terminated unexpectedly at Step 2." },
  ],
  exception:
    "Exception: requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='www.virustotal.com', port=443): Max retries exceeded",
};
