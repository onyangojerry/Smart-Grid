import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../../features/auth/useAuth";
import { 
  Settings, LogOut, LayoutDashboard, MapPin, Cpu, 
  Activity, Zap, Terminal, PiggyBank, PlayCircle 
} from "lucide-react";

export function Sidebar() {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const match = pathname.match(/^\/sites\/([^/]+)/);
  const siteId = match?.[1] || null;

  const links = siteId
    ? [
        { to: "/sites", label: "Sites", icon: MapPin },
        { to: `/sites/${siteId}`, label: "Dashboard", icon: LayoutDashboard },
        { to: `/sites/${siteId}/devices`, label: "Devices", icon: Cpu },
        { to: `/sites/${siteId}/telemetry`, label: "Telemetry", icon: Activity },
        { to: `/sites/${siteId}/optimization`, label: "Optimization", icon: Zap },
        { to: `/sites/${siteId}/commands`, label: "Commands", icon: Terminal },
        { to: `/sites/${siteId}/savings`, label: "Savings", icon: PiggyBank },
        { to: `/sites/${siteId}/simulation`, label: "Simulation", icon: PlayCircle }
      ]
    : [{ to: "/sites", label: "Sites", icon: MapPin }];

  const [showUserMenu, setShowUserMenu] = React.useState(false);

  return (
    <aside className="sidebar">
      <div className="sidebar-nav">
        {links.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </div>
      <div className="sidebar-footer">
        <div className="sidebar-user-trigger" onClick={() => setShowUserMenu(!showUserMenu)}>
          <img
            src={`https://picsum.photos/seed/${user?.id}/32/32`}
            alt={user?.full_name || "User"}
            className="user-avatar-img"
          />
          <div className="sidebar-user-details">
            <div className="user-name">{user?.full_name || "System User"}</div>
            <div className="user-email">{user?.email}</div>
          </div>
          <span className={`chevron-icon ${showUserMenu ? "open" : ""}`}>▾</span>
          
          {showUserMenu && (
            <div className="sidebar-user-dropdown">
              <button className="sidebar-dropdown-item" onClick={() => console.log("Settings")}>
                <Settings size={16} /> Settings
              </button>
              <div className="sidebar-dropdown-divider" />
              <button className="sidebar-dropdown-item logout" onClick={logout}>
                <LogOut size={16} /> Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
