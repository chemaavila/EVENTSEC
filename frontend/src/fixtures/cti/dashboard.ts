import type { CtiDashboardData } from "../../services/cti/types";

export const dashboardFixture: CtiDashboardData = {
  kpis: [
    {
      id: "total-entities",
      label: "Total Entities",
      value: "14,500",
      icon: "hub",
      trend: { direction: "up", label: "+5% vs yesterday" },
    },
    {
      id: "indicators",
      label: "Indicators",
      value: "2,301",
      icon: "fingerprint",
      trend: { direction: "up", label: "+12% vs yesterday" },
    },
    {
      id: "sightings",
      label: "Sightings (24h)",
      value: "54",
      icon: "visibility",
      trend: { direction: "down", label: "-2% vs yesterday" },
    },
    {
      id: "high-confidence",
      label: "High Confidence",
      value: "120",
      icon: "verified",
      trend: { direction: "up", label: "+1% vs yesterday" },
    },
    {
      id: "active-cases",
      label: "Active Cases",
      value: "3",
      icon: "folder_open",
      trend: { direction: "flat", label: "No change" },
    },
  ],
  recentIntel: [
    {
      id: "intel-1",
      icon: "bug_report",
      iconBackground: "rgba(127, 29, 29, 0.3)",
      iconColor: "#ef4444",
      name: "Win32/Emotet",
      source: "CrowdStrike",
      confidence: { score: 90, barColor: "#ef4444" },
      tags: [
        {
          label: "Malware",
          textColor: "#137fec",
          background: "rgba(19, 127, 236, 0.2)",
          borderColor: "rgba(19, 127, 236, 0.2)",
        },
        {
          label: "Critical",
          textColor: "#fb923c",
          background: "rgba(154, 52, 18, 0.2)",
          borderColor: "rgba(249, 115, 22, 0.2)",
        },
      ],
      updatedAt: "2 mins ago",
    },
    {
      id: "intel-2",
      icon: "dns",
      iconBackground: "rgba(30, 64, 175, 0.3)",
      iconColor: "#3b82f6",
      name: "192.168.1.55",
      source: "AlienVault",
      confidence: { score: 65, barColor: "#facc15" },
      tags: [
        {
          label: "C2",
          textColor: "#c084fc",
          background: "rgba(88, 28, 135, 0.2)",
          borderColor: "rgba(168, 85, 247, 0.2)",
        },
      ],
      updatedAt: "15 mins ago",
    },
    {
      id: "intel-3",
      icon: "person",
      iconBackground: "rgba(20, 83, 45, 0.3)",
      iconColor: "#22c55e",
      name: "APT29 (Cozy Bear)",
      source: "MITRE",
      confidence: { score: 95, barColor: "#dc2626" },
      tags: [
        {
          label: "Actor",
          textColor: "#d1d5db",
          background: "#374151",
          borderColor: "#4b5563",
        },
        {
          label: "Espionage",
          textColor: "#f87171",
          background: "rgba(127, 29, 29, 0.2)",
          borderColor: "rgba(239, 68, 68, 0.2)",
        },
      ],
      updatedAt: "1 hour ago",
    },
    {
      id: "intel-4",
      icon: "link",
      iconBackground: "rgba(55, 65, 81, 0.5)",
      iconColor: "#d1d5db",
      name: "login-secure-bank.com",
      source: "PhishTank",
      confidence: { score: 78, barColor: "#f97316" },
      tags: [
        {
          label: "Phishing",
          textColor: "#facc15",
          background: "rgba(120, 53, 15, 0.2)",
          borderColor: "rgba(234, 179, 8, 0.2)",
        },
      ],
      updatedAt: "2 hours ago",
    },
  ],
  topTechniques: [
    { id: "t1059", label: "T1059 - Command & Scripting", count: 124, intensity: 0.85 },
    { id: "t1566", label: "T1566 - Phishing", count: 98, intensity: 0.7 },
    { id: "t1110", label: "T1110 - Brute Force", count: 65, intensity: 0.5 },
    { id: "t1003", label: "T1003 - OS Credential Dumping", count: 42, intensity: 0.35 },
    { id: "t1021", label: "T1021 - Remote Services", count: 28, intensity: 0.2 },
  ],
  streamEvents: [
    {
      id: "event-1",
      icon: "add_link",
      iconBackground: "rgba(59, 130, 246, 0.12)",
      iconColor: "#3b82f6",
      message:
        "System automatically merged Entity #8921 into Case #405 based on correlation rules.",
      timestamp: "Just now",
    },
    {
      id: "event-2",
      icon: "smart_toy",
      iconBackground: "rgba(168, 85, 247, 0.12)",
      iconColor: "#a855f7",
      message:
        "Analyst X ran playbook \"Phishing Triage\" on Alert #2234.",
      timestamp: "5m ago",
    },
    {
      id: "event-3",
      icon: "cloud_download",
      iconBackground: "rgba(34, 197, 94, 0.12)",
      iconColor: "#22c55e",
      message:
        "Imported 350 new indicators from Mandiant Threat Intel Feed.",
      timestamp: "12m ago",
    },
  ],
};
