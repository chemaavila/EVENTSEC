import type { CtiCasesData } from "../../services/cti/types";

export const casesFixture: CtiCasesData = {
  cases: [
    {
      id: "#CS-2023-8492",
      title: "Suspicious PowerShell Activity on SRV-01",
      status: "In Progress",
      statusStyle: "in-progress",
      severity: "Critical",
      severityColor: "var(--palette-ef4444)",
      assignee: "Jane D.",
      assigneeAvatar:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuDdCqvcDi_YZHvNVu-avu_mh_y28LVQl381auDWvtpgKgFJHjMNEk0ARStpZ3nWMeHtPSaJ8RKcSeQVSZD59Uv0QVPQDVtlJMWkiHxXxJ1husWauQPALi21GnE8TozjmnKv0rMFZkeHjvr1xqJADhI_0iDkE6m-S5RAzf4Wo_4m12iX5XGCxIlDzzK9PbICHHZ7En5Ki7w2-W4SBPQy0I4qOtOc-Lth7VsCh0bWODlD1HOolgit7EeA-xkTz_3Ip7QYAxfGgEFjYi88",
      entities: 12,
      lastUpdated: "2 mins ago",
      selected: true,
    },
    {
      id: "#CS-2023-8491",
      title: "Failed Login Anomaly: Multiple Users",
      status: "Open",
      statusStyle: "open",
      severity: "High",
      severityColor: "var(--palette-f97316)",
      assignee: "Unassigned",
      assigneeInitials: "UN",
      entities: 4,
      lastUpdated: "15 mins ago",
    },
    {
      id: "#CS-2023-8490",
      title: "Data Exfiltration Attempt via DNS",
      status: "Closed",
      statusStyle: "closed",
      severity: "Medium",
      severityColor: "var(--palette-eab308)",
      assignee: "Mike R.",
      assigneeAvatar:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuBRKvm1XkZr7T4R3eCtRhzU0G_L_kwdJzm3gNNEVWF_h0nck0pHXLNNWQpDtv-ruxHcyeNqOWH9gV2fQoUwnoSjF6_mYzmnHucYyg5n6LYXLeS65sb6lUEMDe4j1yI8ppjJAiVy2mpGlTOiIJDonpfFgJ-ot6QRsx02fb07LX-FiAU87o1C6-Vw7Jo1-kCECvopmqeDeC6CXnaJg8PNS8JYk7lZKzIlY9sOgx0ZNwMmxDj1Xj3l-MmyVNedu0avLszxdF3HiEM_LNHs",
      entities: 1,
      lastUpdated: "4 hrs ago",
    },
    {
      id: "#CS-2023-8488",
      title: "Phishing Email Campaign - Reported by User",
      status: "Open",
      statusStyle: "open",
      severity: "Low",
      severityColor: "var(--palette-2dd4bf)",
      assignee: "Sarah K.",
      assigneeAvatar:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuAo2gKn5hQYl2OISkYWyxBVVFG7e1wwtysMaphuHjwVUean0CCxk4nC1LXqvXIMSIl6ZJOyo8i9EHoEFqeQiUuDItqbvGzLPgsEbltduMAxb3Ttsd4hmuzCsNyCmNkH0ojJHC0olMZ4kc7M47g-7vWAOXzKPLVaZnXPcrhF8PQr_QvNIKO4OLyJzGJg81FAckhmrcP8UVmBYdgKsTzhVzGDJD7tlF99OrP7hjxjga9kckmNMCpbDOs02d2WxmRvbXuYwtqMjazo9iQl",
      entities: 7,
      lastUpdated: "1 day ago",
    },
  ],
  detail: {
    id: "#CS-2023-8492",
    severity: "CRITICAL",
    title: "Suspicious PowerShell Activity on SRV-01",
    checklistProgress: "1/4 Completed",
    checklist: [
      {
        id: "task-1",
        text: "Isolate Host SRV-01",
        completed: true,
        note: "Completed by Jane D. at 10:42 AM",
      },
      { id: "task-2", text: "Verify User Permissions", completed: false },
      { id: "task-3", text: "Scan for Malicious Artifacts", completed: false },
      { id: "task-4", text: "Reset Compromised Credentials", completed: false },
    ],
    timeline: [
      {
        id: "note-1",
        author: "Jane Doe",
        time: "2 mins ago",
        content:
          "Preliminary scan shows correlation with APT29 indicators. Recommendation to escalate severity.",
        highlight: true,
      },
      {
        id: "note-2",
        author: "System",
        time: "10 mins ago",
        content: "Status changed from Open to In Progress.",
        system: true,
      },
      {
        id: "note-3",
        author: "SIEM Alert",
        time: "1 hour ago",
        content:
          "Case automatically created from correlation rule: PS_Suspicious_Download",
        critical: true,
      },
    ],
  },
};
