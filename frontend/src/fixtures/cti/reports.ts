import type { CtiReportsData } from "../../services/cti/types";

export const reportsFixture: CtiReportsData = {
  reports: [
    {
      id: "rpt-1",
      source: "AlienVault OTX",
      sourceIcon: "public",
      title: "APT29 Phishing Campaign Analysis",
      summary: "New indicators related to NOBELIUM activity.",
      markers: [
        { label: "Critical", color: "var(--alpha-239-68-68-0_2)", textColor: "var(--palette-ef4444)" },
        { label: "Phishing", color: "var(--alpha-59-130-246-0_2)", textColor: "var(--palette-60a5fa)" },
      ],
      createdAt: "Oct 24, 14:30",
      objects: 42,
      selected: true,
    },
    {
      id: "rpt-2",
      source: "CrowdStrike",
      sourceIcon: "security",
      title: "Cobalt Strike Beacon Configs",
      summary: "Latest beacon configurations extracted from memory.",
      markers: [
        { label: "High", color: "var(--alpha-251-146-60-0_2)", textColor: "var(--palette-fb923c)" },
        { label: "Malware", color: "var(--alpha-31-41-55-0_6)", textColor: "var(--palette-9ca3af)" },
      ],
      createdAt: "Oct 23, 09:15",
      objects: 18,
    },
    {
      id: "rpt-3",
      source: "Abuse.ch",
      sourceIcon: "mail",
      title: "URLhaus Recent Payloads",
      summary: "Daily dump of malware distribution sites.",
      markers: [{ label: "Medium", color: "var(--alpha-250-204-21-0_2)", textColor: "var(--palette-facc15)" }],
      createdAt: "Oct 23, 08:00",
      objects: 156,
    },
    {
      id: "rpt-4",
      source: "MISP Feed",
      sourceIcon: "api",
      title: "Lazarus Group Operations",
      summary: "Indicators associated with Lazarus financial theft.",
      markers: [
        { label: "Critical", color: "var(--alpha-239-68-68-0_2)", textColor: "var(--palette-ef4444)" },
        { label: "APT", color: "var(--alpha-168-85-247-0_2)", textColor: "var(--palette-c084fc)" },
      ],
      createdAt: "Oct 22, 16:45",
      objects: 8,
    },
    {
      id: "rpt-5",
      source: "Manual Import",
      sourceIcon: "description",
      title: "Internal Incident \u00234922 IOCs",
      summary: "Uploaded by analyst J.Doe from incident response.",
      markers: [{ label: "Internal", color: "var(--alpha-59-130-246-0_2)", textColor: "var(--palette-60a5fa)" }],
      createdAt: "Oct 21, 11:20",
      objects: 5,
    },
  ],
  detail: {
    id: "RPT-2023-8942",
    title: "APT29 Phishing Campaign Analysis",
    summary:
      "This report details a recent spear-phishing campaign attributed to APT29 (Nobelium). The campaign utilizes a new variant of the Duke malware family delivered via compromised diplomatic email accounts. The primary vector involves PDF attachments containing malicious JavaScript.",
    observablesCount: 42,
    observables: [
      { id: "obs-1", icon: "language", color: "var(--palette-c084fc)", value: "malicious-domain.com", type: "Domain Name" },
      { id: "obs-2", icon: "lan", color: "var(--palette-60a5fa)", value: "192.168.1.45", type: "IPv4 Address" },
      { id: "obs-3", icon: "fingerprint", color: "var(--palette-fb923c)", value: "a1b2c3d4e5...", type: "SHA-256" },
    ],
    relationships: [
      { id: "rel-1", icon: "groups", color: "var(--palette-ef4444)", label: "Threat Actor", value: "APT29" },
      { id: "rel-2", icon: "bug_report", color: "var(--palette-60a5fa)", label: "Malware", value: "Duke Family" },
    ],
    ingested: "Ingested via API",
    updated: "Updated 2m ago",
  },
};
