// frontend/src/components/Sidebar.tsx
import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

type SidebarProps = {
  isOpen: boolean;
  onToggle: () => void;
  onNavigate?: () => void;
};

type NavItem = {
  label: string;
  path: string;
  icon: React.ReactNode;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

/* ---------- ICONOS (de svgrepo, estilo sobrio) ---------- */

const iconProps: React.SVGProps<SVGSVGElement> = {
  width: 28,
  height: 28,
  viewBox: "0 0 24 24",
  fill: "none",
  xmlns: "http://www.w3.org/2000/svg",
};

const DashboardIcon = () => (
  <svg {...iconProps}>
    <rect x="3" y="3" width="7" height="7" rx="1.5" stroke="currentColor" />
    <rect x="14" y="3" width="7" height="5" rx="1.5" stroke="currentColor" />
    <rect x="14" y="11" width="7" height="10" rx="1.5" stroke="currentColor" />
    <rect x="3" y="13" width="7" height="8" rx="1.5" stroke="currentColor" />
  </svg>
);

const SiemIcon = () => (
  <svg {...iconProps}>
    <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.4" />
    <circle cx="12" cy="12" r="3.5" stroke="currentColor" strokeWidth="1.4" />
    <path
      d="M12 4v2.5M12 17.5V20M4 12h2.5M17.5 12H20"
      stroke="currentColor"
      strokeLinecap="round"
    />
    <path
      d="M7 7l2 2M15 7l2-2M7 17l2-2M15 17l2 2"
      stroke="currentColor"
      strokeLinecap="round"
    />
    <circle cx="12" cy="12" r="1" fill="currentColor" />
  </svg>
);

const EdrIcon = () => (
  <svg {...iconProps}>
    <circle cx="12" cy="12" r="3.5" stroke="currentColor" />
    <circle cx="12" cy="12" r="7.5" stroke="currentColor" strokeDasharray="2 3" />
    <path
      d="M12 2v2M12 20v2M4 12H2M22 12h-2"
      stroke="currentColor"
      strokeLinecap="round"
    />
  </svg>
);

const IocBiocIcon = () => (
  <svg {...iconProps}>
    <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" />
    <path
      d="M8 9l3 3-3 3M13 9h3M13 12h2M13 15h3"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const AnalyticsIcon = () => (
  <svg {...iconProps}>
    <path
      d="M4 19v-6M10 19V5M16 19v-9M20 19V9"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const AdminIcon = () => (
  <svg {...iconProps}>
    <circle cx="12" cy="8" r="3" stroke="currentColor" />
    <path
      d="M5.5 19c1.25-2.5 3.75-4 6.5-4s5.25 1.5 6.5 4"
      stroke="currentColor"
      strokeLinecap="round"
    />
    <path
      d="M4 11.5c0-4.5 3.5-7.5 8-7.5s8 3 8 7.5"
      stroke="currentColor"
      strokeDasharray="2 3"
    />
  </svg>
);

const CorrelationIcon = () => (
  <svg {...iconProps}>
    <path
      d="M5 18 9 8l4 8 3-6 3 8"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle cx="9" cy="8" r="1" fill="currentColor" />
    <circle cx="13" cy="16" r="1" fill="currentColor" />
    <circle cx="18" cy="18" r="1" fill="currentColor" />
  </svg>
);

const AlertsIcon = () => (
  <svg {...iconProps}>
    <path
      d="M12 3a6 6 0 0 0-6 6v3.5L4 15v1h16v-1l-2-2.5V9a6 6 0 0 0-6-6z"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M10 19h4" stroke="currentColor" strokeLinecap="round" />
  </svg>
);

const HandoverIcon = () => (
  <svg {...iconProps}>
    <path
      d="M5 7h9l3 3h2v9H5V7z"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M9 3h7l3 3v2"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const EndpointIcon = () => (
  <svg {...iconProps}>
    <rect x="4" y="4" width="16" height="16" rx="3" stroke="currentColor" />
    <path
      d="M8 8h8M8 12h6M8 16h4"
      stroke="currentColor"
      strokeLinecap="round"
    />
    <circle cx="9" cy="8" r="0.8" fill="currentColor" />
    <circle cx="9" cy="12" r="0.8" fill="currentColor" />
    <circle cx="9" cy="16" r="0.8" fill="currentColor" />
  </svg>
);

const WorkplanIcon = () => (
  <svg {...iconProps}>
    <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" />
    <path
      d="M8 8h8M8 12h8M8 16h5"
      stroke="currentColor"
      strokeLinecap="round"
    />
    <path
      d="M6 7v3h3"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const ProfileIcon = () => (
  <svg {...iconProps}>
    <circle cx="12" cy="9" r="3" stroke="currentColor" />
    <path
      d="M6 19c1.5-2 3.5-3 6-3s4.5 1 6 3"
      stroke="currentColor"
      strokeLinecap="round"
    />
  </svg>
);

const SearchIcon = () => (
  <svg {...iconProps}>
    <circle cx="11" cy="11" r="4.5" stroke="currentColor" />
    <path d="M15 15l3 3" stroke="currentColor" strokeLinecap="round" />
  </svg>
);

const TimelineIcon = () => (
  <svg {...iconProps}>
    <path
      d="M5 6h14M5 12h14M5 18h14"
      stroke="currentColor"
      strokeLinecap="round"
    />
    <circle cx="8" cy="6" r="1" fill="currentColor" />
    <circle cx="14" cy="12" r="1" fill="currentColor" />
    <circle cx="11" cy="18" r="1" fill="currentColor" />
  </svg>
);

const ThreatIntelIcon = () => (
  <svg {...iconProps}>
    <circle cx="12" cy="12" r="7" stroke="currentColor" strokeWidth="1.5" />
    <path d="M8 12h2l2-4 2 8 2-6" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="12" cy="12" r="1.5" fill="currentColor" />
  </svg>
);

const EmailProtectionIcon = () => (
  <svg {...iconProps}>
    <path
      d="M4 6h16v12H4z"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="none"
    />
    <path
      d="M4 6l8 7 8-7"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/* ---------- NAVEGACIÓN ---------- */

const NAV_SECTIONS: NavSection[] = [
  {
    title: "Overview",
    items: [
      { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
    ],
  },
  {
    title: "Detection",
    items: [
      { label: "SIEM", path: "/siem", icon: <SiemIcon /> },
      { label: "EDR", path: "/edr", icon: <EdrIcon /> },
      { label: "IOC / BIOC", path: "/ioc-bioc", icon: <IocBiocIcon /> },
      { label: "Sandbox", path: "/sandbox", icon: <CorrelationIcon /> },
      { label: "Events explorer", path: "/events", icon: <TimelineIcon /> },
      { label: "Threat Map", path: "/threat-intel", icon: <ThreatIntelIcon /> },
      { label: "Threat Intelligence (CTI)", path: "/intelligence/dashboard", icon: <ThreatIntelIcon /> },
      { label: "Email Threat Intel", path: "/email-security/threat-intel", icon: <EmailProtectionIcon /> },
    ],
  },
  {
    title: "Rules",
    items: [
      { label: "Analytics rules", path: "/analytics-rules", icon: <AnalyticsIcon /> },
      { label: "Correlation rules", path: "/correlation-rules", icon: <CorrelationIcon /> },
    ],
  },
  {
    title: "Operations",
    items: [
      { label: "Alerts", path: "/alerts", icon: <AlertsIcon /> },
      { label: "Endpoints", path: "/endpoints", icon: <EndpointIcon /> },
      { label: "Software inventory", path: "/software-inventory", icon: <EndpointIcon /> },
      { label: "Handovers", path: "/handover", icon: <HandoverIcon /> },
      { label: "Workplans", path: "/workplans", icon: <WorkplanIcon /> },
      { label: "KQL workbench", path: "/advanced-search", icon: <SearchIcon /> },
      { label: "My profile", path: "/profile", icon: <ProfileIcon /> },
    ],
  },
  {
    title: "Connectors",
    items: [
      {
        label: "Email Security",
        path: "/email-security",
        icon: <EmailProtectionIcon />,
      },
      {
        label: "Email protection (docs)",
        path: "/email-protection",
        icon: <EmailProtectionIcon />,
      },
    ],
  },
];

/* ---------- COMPONENTE SIDEBAR ---------- */

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle, onNavigate }) => {
  const { user } = useAuth();
  const sections: NavSection[] = [...NAV_SECTIONS];

  if (user?.role === "admin") {
    sections.push({
      title: "Administration",
      items: [
        {
          label: "User management",
          path: "/admin/users",
          icon: <AdminIcon />,
        },
      ],
    });
  }

  return (
    <aside className={`sidebar ${isOpen ? "sidebar-open" : "sidebar-closed"}`}>
      <div className="sidebar-header">
        <button
          className="sidebar-burger"
          type="button"
          onClick={onToggle}
          aria-label="Toggle navigation"
        >
          <span />
          <span />
          <span />
        </button>
        <span className="sidebar-logo">EventSec</span>
      </div>

      <nav className="sidebar-nav">
        {sections.map((section) => (
          <div key={section.title} className="sidebar-section">
            <div className="sidebar-section-title">{section.title}</div>
            <div className="sidebar-section-items">
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    "sidebar-link" + (isActive ? " sidebar-link-active" : "")
                  }
                  onClick={() => {
                    if (isOpen && onNavigate) {
                      onNavigate();
                    }
                  }}
                >
                  <span className="sidebar-link-icon">{item.icon}</span>
                  <span className="sidebar-link-label">{item.label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
