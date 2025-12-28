import type React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

interface TopbarProps {
  onToggleSidebar: () => void;
}

const Topbar: React.FC<TopbarProps> = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const userInitials = user
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "U";

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="topbar-icon-button"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
        >
          <span className="topbar-hamburger">
            <span />
            <span />
            <span />
          </span>
        </button>

        <div className="topbar-logo">
          <img src="/favicon.svg" alt="EventSec logo" width={32} height={32} />
          <div className="topbar-logo-text">
            <div className="topbar-logo-title">EventSec Enterprise</div>
            <div className="topbar-logo-subtitle">
              Unified SIEM / EDR workspace
            </div>
          </div>
        </div>
      </div>

      <div className="topbar-right">
        {user && (
          <>
            <div className="topbar-shift-pill">
              <span className="pill-dot" />
              {user.team || "Team"} • {user.role}
            </div>

            <div className="topbar-user">
              <div className="topbar-user-avatar">{userInitials}</div>
              <div className="topbar-user-text">
                <div className="topbar-user-name">{user.full_name}</div>
                <div className="topbar-user-role">{user.role}</div>
              </div>
            </div>

            <button
              type="button"
              className="btn btn-sm btn-ghost"
              onClick={handleLogout}
              style={{ marginLeft: "1rem" }}
            >
              Logout
            </button>
          </>
        )}
      </div>
    </header>
  );
};

export default Topbar;
