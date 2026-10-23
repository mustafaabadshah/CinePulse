import React, { useEffect, useState } from "react";
import { Activity, Server, CheckCircle, AlertTriangle, RefreshCw, HardDrive } from "lucide-react";
import { getHealth } from "../api/client";
import { HealthStatus } from "../types";

export const HealthPage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = () => {
    setLoading(true);
    setError(null);
    getHealth()
      .then((data) => setHealth(data))
      .catch((err) => setError(err.message || "Failed to reach health endpoint."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHealth();
    // Auto-poll health every 15s while page is open
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ maxWidth: "1000px", margin: "40px auto", padding: "0 24px" }}>
      {/* Title */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px", marginBottom: "32px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Activity size={24} color="var(--accent-blue)" />
            <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", fontWeight: 700 }}>
              System Health & Diagnostics
            </h1>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Live status of FastAPI backend, relational storage, and Meilisearch search indexes.
          </p>
        </div>

        <button onClick={fetchHealth} className="btn-secondary" style={{ padding: "8px 16px" }}>
          <RefreshCw size={14} />
          <span>Refresh Status</span>
        </button>
      </div>

      {loading && !health && (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "40px 0" }}>
          Querying component health...
        </div>
      )}

      {error && (
        <div className="card-glass" style={{ padding: "32px", textAlign: "center", border: "1px solid rgba(239, 68, 68, 0.3)", marginBottom: "24px" }}>
          <AlertTriangle size={32} color="#ef4444" style={{ margin: "0 auto 10px" }} />
          <h3 style={{ color: "#f87171", marginBottom: "8px" }}>Health Check Failed</h3>
          <p style={{ color: "var(--text-secondary)" }}>{error}</p>
        </div>
      )}

      {health && (
        <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
          {/* Main Status Banner */}
          <div className="card-glass" style={{
            padding: "24px 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderLeft: health.status === "healthy" ? "4px solid #10b981" : "4px solid #f59e0b"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              {health.status === "healthy" ? (
                <CheckCircle size={32} color="#10b981" />
              ) : (
                <AlertTriangle size={32} color="#f59e0b" />
              )}
              <div>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 700 }}>
                  System Status: {health.status.toUpperCase()}
                </h3>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                  {health.status === "healthy"
                    ? "All core components are running and responsive."
                    : "One or more subsystem dependencies are degraded or offline."}
                </p>
              </div>
            </div>
          </div>

          {/* Core Subsystem Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px" }}>
            {/* Database Card */}
            <div className="card-glass" style={{ padding: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <HardDrive size={20} color="var(--accent-blue)" />
                  <h4 style={{ fontSize: "1.1rem", fontWeight: 600 }}>Relational Database</h4>
                </div>
                <span style={{
                  padding: "2px 8px",
                  borderRadius: "4px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  background: health.components.database.status === "up" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                  color: health.components.database.status === "up" ? "#34d399" : "#f87171"
                }}>
                  {health.components.database.status.toUpperCase()}
                </span>
              </div>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: 1.5 }}>
                SQLAlchemy engine & connection pool. Manages canonical entities, source provenance, and audit logs.
              </p>
            </div>

            {/* Meilisearch Engine Card */}
            <div className="card-glass" style={{ padding: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <Server size={20} color="var(--accent-purple)" />
                  <h4 style={{ fontSize: "1.1rem", fontWeight: 600 }}>Meilisearch Engine</h4>
                </div>
                <span style={{
                  padding: "2px 8px",
                  borderRadius: "4px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  background: health.components.meilisearch.status === "up" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                  color: health.components.meilisearch.status === "up" ? "#34d399" : "#f87171"
                }}>
                  {health.components.meilisearch.status.toUpperCase()}
                </span>
              </div>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: 1.5 }}>
                High-performance search engine running on LMDB storage. Typo tolerance, faceting, and sorting engine.
              </p>
            </div>
          </div>

          {/* Index Stats Grid */}
          {health.components.meilisearch.indexes && (
            <div className="card-glass" style={{ padding: "28px" }}>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 600, marginBottom: "18px" }}>
                Meilisearch Index Statistics
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
                {Object.entries(health.components.meilisearch.indexes).map(([indexUid, stats]: [string, any]) => (
                  <div key={indexUid} style={{
                    padding: "16px",
                    background: "rgba(255, 255, 255, 0.02)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "8px"
                  }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.88rem", color: "#93c5fd", marginBottom: "8px" }}>
                      {indexUid}
                    </div>
                    <div style={{ fontSize: "1.6rem", fontWeight: 700, fontFamily: "var(--font-display)" }}>
                      {stats.number_of_documents !== undefined ? stats.number_of_documents : "—"}
                      <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginLeft: "6px", fontWeight: 400 }}>docs</span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: stats.is_indexing ? "#f59e0b" : "#34d399", marginTop: "4px" }}>
                      {stats.is_indexing ? "Indexing active..." : "Idle / Ready"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
