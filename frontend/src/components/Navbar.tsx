import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Search, Activity, BarChart3, Database, Sparkles } from "lucide-react";
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
    { to: "/search", label: "Search", icon: Search },
    { to: "/analytics", label: "Analytics", icon: BarChart3 },
    { to: "/admin", label: "Admin & Ingest", icon: Database },
    { to: "/health", label: "System Health", icon: Activity },
  ];

  return (
    <header style={{
      borderBottom: "1px solid var(--border-subtle)",
      background: "var(--bg-glass)",
      backdropFilter: "blur(12px)",
      position: "sticky",
      top: 0,
      zIndex: 50
    }}>
      <div style={{
        maxWidth: "1280px",
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
            background: "linear-gradient(135deg, #3b82f6, #6366f1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 14px rgba(59, 130, 246, 0.4)"
          }}>
            <Search size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{
              fontFamily: "var(--font-display)",
              fontSize: "1.25rem",
              fontWeight: 700,
              letterSpacing: "-0.02em",
              background: "linear-gradient(90deg, #ffffff, #93c5fd)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent"
            }}>
              ResearchRadar
            </div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "-2px" }}>
              Meilisearch Discovery Platform
            </div>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {navLinks.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to || (item.to !== "/" && location.pathname.startsWith(item.to));
            return (
              <Link
                key={item.to}
                to={item.to}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "8px 14px",
                  borderRadius: "8px",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: isActive ? "#ffffff" : "var(--text-secondary)",
                  background: isActive ? "rgba(59, 130, 246, 0.15)" : "transparent",
                  border: isActive ? "1px solid rgba(59, 130, 246, 0.3)" : "1px solid transparent",
                  transition: "all var(--transition-fast)"
                }}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Engine Status Indicator Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Link
            to="/health"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 12px",
              borderRadius: "20px",
              background: engineHealthy ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
              border: engineHealthy ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(239, 68, 68, 0.3)",
              fontSize: "0.75rem",
              fontWeight: 500,
              color: engineHealthy ? "#34d399" : "#f87171"
            }}
          >
            <span style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: engineHealthy ? "#10b981" : "#ef4444",
              boxShadow: engineHealthy ? "0 0 8px #10b981" : "0 0 8px #ef4444"
            }} />
            <span>{engineHealthy === null ? "Connecting..." : engineHealthy ? "Meilisearch Online" : "Service Offline"}</span>
          </Link>
        </div>
      </div>
    </header>
  );
};
