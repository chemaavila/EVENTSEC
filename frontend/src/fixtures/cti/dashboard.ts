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
      iconBackground: "var(--alpha-127-29-29-0_3)",
      iconColor: "var(--palette-ef4444)",
      name: "Win32/Emotet",
      source: "CrowdStrike",
      confidence: { score: 90, barColor: "var(--palette-ef4444)" },
      tags: [
        {
          label: "Malware",
          textColor: "var(--palette-137fec)",
          background: "var(--alpha-19-127-236-0_2)",
          borderColor: "var(--alpha-19-127-236-0_2)",
        },
        {
          label: "Critical",
          textColor: "var(--palette-fb923c)",
          background: "var(--alpha-154-52-18-0_2)",
          borderColor: "var(--alpha-249-115-22-0_2)",
        },
      ],
      updatedAt: "2 mins ago",
    },
    {
      id: "intel-2",
      icon: "dns",
      iconBackground: "var(--alpha-30-64-175-0_3)",
      iconColor: "var(--palette-3b82f6)",
      name: "192.168.1.55",
      source: "AlienVault",
      confidence: { score: 65, barColor: "var(--palette-facc15)" },
      tags: [
        {
          label: "C2",
          textColor: "var(--palette-c084fc)",
          background: "var(--alpha-88-28-135-0_2)",
          borderColor: "var(--alpha-168-85-247-0_2)",
        },
      ],
      updatedAt: "15 mins ago",
    },
    {
      id: "intel-3",
      icon: "person",
      iconBackground: "var(--alpha-20-83-45-0_3)",
      iconColor: "var(--palette-22c55e)",
      name: "APT29 (Cozy Bear)",
      source: "MITRE",
      confidence: { score: 95, barColor: "var(--palette-dc2626)" },
      tags: [
        {
          label: "Actor",
          textColor: "var(--palette-d1d5db)",
          background: "var(--palette-374151)",
          borderColor: "var(--palette-4b5563)",
        },
        {
          label: "Espionage",
          textColor: "var(--palette-f87171)",
          background: "var(--alpha-127-29-29-0_2)",
          borderColor: "var(--alpha-239-68-68-0_2)",
        },
      ],
      updatedAt: "1 hour ago",
    },
    {
      id: "intel-4",
      icon: "link",
      iconBackground: "var(--alpha-55-65-81-0_5)",
      iconColor: "var(--palette-d1d5db)",
      name: "login-secure-bank.com",
      source: "PhishTank",
      confidence: { score: 78, barColor: "var(--palette-f97316)" },
      tags: [
        {
          label: "Phishing",
          textColor: "var(--palette-facc15)",
          background: "var(--alpha-120-53-15-0_2)",
          borderColor: "var(--alpha-234-179-8-0_2)",
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
      iconBackground: "var(--alpha-59-130-246-0_12)",
      iconColor: "var(--palette-3b82f6)",
      message:
        "System automatically merged Entity \u00238921 into Case \u0023405 based on correlation rules.",
      timestamp: "Just now",
    },
    {
      id: "event-2",
      icon: "smart_toy",
      iconBackground: "var(--alpha-168-85-247-0_12)",
      iconColor: "var(--palette-a855f7)",
      message:
        "Analyst X ran playbook \"Phishing Triage\" on Alert \u00232234.",
      timestamp: "5m ago",
    },
    {
      id: "event-3",
      icon: "cloud_download",
      iconBackground: "var(--alpha-34-197-94-0_12)",
      iconColor: "var(--palette-22c55e)",
      message:
        "Imported 350 new indicators from Mandiant Threat Intel Feed.",
      timestamp: "12m ago",
    },
  ],
};
