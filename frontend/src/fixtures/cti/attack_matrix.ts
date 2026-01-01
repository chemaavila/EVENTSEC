import type { CtiAttackData } from "../../services/cti/types";

export const attackMatrixFixture: CtiAttackData = {
  tactics: [
    {
      id: "initial-access",
      name: "Initial Access",
      detectedCount: 3,
      techniques: [
        { id: "T1566", name: "Phishing", count: 12, severity: "high", active: true },
        { id: "T1189", name: "Drive-by Compromise", count: 2, severity: "medium", active: true },
        { id: "T1190", name: "Exploit Public-Facing App", severity: "none" },
      ],
    },
    {
      id: "execution",
      name: "Execution",
      detectedCount: 5,
      techniques: [
        { id: "T1059", name: "Command and Scripting Interpreter", count: 15, severity: "high", highlighted: true },
        { id: "T1204", name: "User Execution", count: 8, severity: "medium", active: true },
        { id: "T1053", name: "Scheduled Task/Job", severity: "none" },
      ],
    },
    {
      id: "persistence",
      name: "Persistence",
      detectedCount: 1,
      techniques: [
        { id: "T1098", name: "Account Manipulation", count: 4, severity: "high", active: true },
        { id: "T1136", name: "Create Account", severity: "none" },
        { id: "T1547", name: "Boot or Logon Autostart", severity: "none" },
      ],
    },
    {
      id: "privilege-escalation",
      name: "Privilege Escalation",
      detectedCount: 0,
      techniques: [
        { id: "T1548", name: "Abuse Elevation Control Mechanism", severity: "none" },
        { id: "T1134", name: "Access Token Manipulation", severity: "none" },
      ],
    },
    {
      id: "defense-evasion",
      name: "Defense Evasion",
      detectedCount: 2,
      techniques: [
        { id: "T1027", name: "Obfuscated Files or Information", count: 6, severity: "medium", active: true },
        { id: "T1562", name: "Impair Defenses", severity: "none" },
      ],
    },
    {
      id: "credential-access",
      name: "Credential Access",
      detectedCount: 1,
      techniques: [
        { id: "T1110", name: "Brute Force", count: 9, severity: "high", active: true },
      ],
    },
    {
      id: "discovery",
      name: "Discovery",
      detectedCount: 12,
      techniques: [
        { id: "T1087", name: "Account Discovery", count: 12, severity: "low", active: true },
      ],
    },
  ],
  selected: {
    code: "T1059",
    title: "Command and Scripting Interpreter",
    confidenceLabel: "High Confidence",
    alertsCount: 15,
    description:
      "Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries. These interfaces and languages provide ways to interact with computer systems and are a common feature across many different platforms.",
    linkedIntel: [
      { id: "intel-1", title: "APT29", category: "Intrusion Set", relevance: "high" },
      {
        id: "intel-2",
        title: "Cobalt Strike",
        category: "Tool",
        note: "Detected beaconing activity associated with powershell.exe",
      },
    ],
    sightings: [
      {
        id: "sighting-1",
        timestamp: "Today, 10:42 AM",
        title: "PowerShell executed encoded command",
        host: "Host: WORKSTATION-01",
        high: true,
      },
      {
        id: "sighting-2",
        timestamp: "Yesterday, 4:15 PM",
        title: "Suspicious cmd.exe child process",
        host: "Host: SERVER-DB-02",
      },
    ],
  },
};
