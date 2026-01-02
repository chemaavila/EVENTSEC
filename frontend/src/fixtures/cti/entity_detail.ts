import type { CtiEntityDetail } from "../../services/cti/types";

export const entityDetailFixture: CtiEntityDetail = {
  id: "192.168.1.105",
  typeLabel: "IPv4 Address",
  statusText: "Active in last 24h",
  firstSeenLabel: "First seen: Oct 12, 2023",
  description:
    "This IP address has been identified as a Command and Control (C2) node associated with the APT29 threat group. It has been observed scanning internal subnets for vulnerabilities in the SMB protocol. Initially detected via firewall logs indicating outbound traffic on non-standard ports.",
  externalReferences: [
    "AlienVault OTX Pulse: APT29 Infrastructure",
    "VirusTotal Report: 192.168.1.105",
  ],
  technicalDetails: {
    asn: "AS12345 (ISP Name)",
    country: "Russia",
    countryCode: "(RU)",
    firstSeen: "2023-10-12 14:32:00 UTC",
    lastSeen: "2023-10-29 09:15:22 UTC",
    reverseDns: "host-105.subnet-1.evil-isp.ru",
  },
  timeline: [
    {
      id: "timeline-1",
      title: "Entity Created",
      timestamp: "Oct 12, 2023 14:30",
      description: "Ingested automatically via MISP Feeds.",
      dotColor: "var(--palette-137fec)",
    },
    {
      id: "timeline-2",
      title: "Sighting Reported",
      timestamp: "Oct 15, 2023 09:12",
      description: "Detected by Firewall-01 blocked connection on port 445.",
      dotColor: "var(--palette-ef4444)",
    },
    {
      id: "timeline-3",
      title: "Enrichment Updated",
      timestamp: "Oct 28, 2023 11:00",
      description: "VirusTotal score increased to 15/60.",
      dotColor: "var(--palette-fbbf24)",
    },
  ],
  linkedEntities: [
    {
      id: "entity-1",
      icon: "bug_report",
      iconColor: "var(--palette-f87171)",
      title: "Emotet",
      subtitle: "Malware Family",
    },
    {
      id: "entity-2",
      icon: "language",
      iconColor: "var(--palette-c084fc)",
      title: "bad-domain.com",
      subtitle: "Domain Name",
    },
    {
      id: "entity-3",
      icon: "person",
      iconColor: "var(--palette-60a5fa)",
      title: "admin@bad-domain.com",
      subtitle: "Email Address",
    },
  ],
  mitreTechniques: ["T1046", "T1588.002", "T1071"],
  mitreDescription:
    "T1046: Network Service Scanning. Adversaries may attempt to get a listing of services running on remote hosts.",
  linkedCases: [
    {
      id: "\u0023402",
      severity: "Critical",
      severityColor: "var(--alpha-239-68-68-0_2)",
      summary: "Q3 Data Breach Investigation - Marketing Subnet",
      updatedAt: "Updated 2h ago",
      showClock: true,
    },
    {
      id: "\u0023389",
      severity: "Closed",
      severityColor: "var(--alpha-34-197-94-0_2)",
      summary: "Suspicious login attempts from RU",
    },
  ],
  locationLabel: "Moscow, Russia",
};
