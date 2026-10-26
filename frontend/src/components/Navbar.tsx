import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Film, Tv, Radio, PlaySquare, Database, Activity, Sparkles } from "lucide-react";
import { getHealth } from "../api/client";

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [engineHealthy, setEngineHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    getHealth()
      .then((data) => setEngineHealthy(data.status === "healthy"))
      .catch(() => setEngineHealthy(false));
  }, []);

  const navLinks = [
    { to: "/", label: "Home", icon: Sparkles },
    { to: "/search?type=programs", label: "Shows", icon: Tv },
    { to: "/search?type=channels", label: "Channels", icon: Radio },
    { to: "/search?type=episodes", label: "Episodes", icon: PlaySquare },
    { to: "/admin", label: "Admin & Sync", icon: Database },
  ];

  return (
    <header style={{
      borderBottom: "1px solid var(--border-subtle)",
      background: "var(--bg-glass)",
      backdropFilter: "blur(16px)",
      position: "sticky",
      top: 0,
      zIndex: 50
    }}>
      <div style={{
        maxWidth: "1400px",
        margin: "0 auto",
        padding: "0 24px",
        height: "68px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between"
      }}>
        {/* Brand Logo */}
        <Link to="/" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "40px",
            height: "40px",
            borderRadius: "10px",
            background: "linear-gradient(135deg, #e50914, #990000)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 16px rgba(229, 9, 20, 0.45)"
          }}>
            <Film size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{
              fontFamily: "var(--font-display)",
              fontSize: "1.25rem",
              fontWeight: 800,
              letterSpacing: "-0.02em",
              color: "#ffffff",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}>
              <span>Tamasha</span>
              <span style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                color: "var(--accent-red)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                border: "1px solid var(--accent-red)",
                borderRadius: "4px",
                padding: "1px 5px"
              }}>
                Explorer
              </span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "-2px" }}>
              OTT Discovery & Catalog Search
            </div>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {navLinks.map((item) => {
            const Icon = item.icon;
            const currentFull = location.pathname + location.search;
            const isActive = item.to === "/" 
              ? location.pathname === "/" 
              : currentFull === item.to || (location.pathname === "/search" && location.search.includes(item.to.split("?")[1] || "___"));

            return (
              <Link
                key={item.to}
                to={item.to}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "7px",
                  padding: "8px 14px",
                  borderRadius: "8px",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  color: isActive ? "#ffffff" : "var(--text-secondary)",
                  background: isActive ? "rgba(229, 9, 20, 0.15)" : "transparent",
                  border: isActive ? "1px solid rgba(229, 9, 20, 0.35)" : "1px solid transparent",
                  transition: "all var(--transition-fast)"
                }}
              >
                <Icon size={16} color={isActive ? "var(--accent-red)" : "currentColor"} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Engine Status Indicator Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Link
            to="/health"
            title="System Health & Meilisearch Status"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 12px",
              borderRadius: "20px",
              background: engineHealthy ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
              border: engineHealthy ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(239, 68, 68, 0.3)",
              fontSize: "0.75rem",
              fontWeight: 600,
              color: engineHealthy ? "#34d399" : "#f87171"
            }}
          >
            <Activity size={13} />
            <span style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: engineHealthy ? "#10b981" : "#ef4444"
            }} />
            <span>{engineHealthy ? "Engine Active" : "Engine Alert"}</span>
          </Link>
        </div>
      </div>
    </header>
  );
};
