import React, { useEffect, useState } from "react";
import { BarChart3, Clock, AlertCircle, TrendingUp, Search, Shield, RefreshCw } from "lucide-react";
import { getSearchAnalytics } from "../api/client";
import { SearchAnalyticsSummary } from "../types";

export const AnalyticsPage: React.FC = () => {
  const [apiKey] = useState(() => sessionStorage.getItem("rr_admin_key") || "rr_admin_secret_dev_key_change_me");
  const [analytics, setAnalytics] = useState<SearchAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSearchAnalytics(apiKey);
      setAnalytics(data);
    } catch (err: any) {
      setError(err.message || "Could not retrieve search analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [apiKey]);

  return (
    <div style={{ maxWidth: "1180px", margin: "40px auto", padding: "0 24px" }}>
      {/* Title */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px", marginBottom: "32px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <BarChart3 size={24} color="var(--accent-blue)" />
            <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", fontWeight: 700 }}>
              Search Analytics & Observability
            </h1>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Privacy-conscious search relevance performance metrics, zero-result analysis, and query latency distribution.
          </p>
        </div>

        <button onClick={fetchAnalytics} className="btn-secondary" style={{ padding: "8px 16px" }}>
          <RefreshCw size={14} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Privacy Notice Banner */}
      <div style={{
        padding: "14px 20px",
        background: "rgba(59, 130, 246, 0.08)",
        border: "1px solid rgba(59, 130, 246, 0.2)",
        borderRadius: "10px",
        fontSize: "0.82rem",
        color: "#93c5fd",
        display: "flex",
        alignItems: "center",
        gap: "10px",
        marginBottom: "32px"
      }}>
        <Shield size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>Privacy-Preserving Telemetry:</strong> All queries are recorded pseudonymously without IP addresses, user accounts, cookies, or personal identifiers.
        </div>
      </div>

      {loading && (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "40px 0" }}>
          Aggregating telemetry...
        </div>
      )}

      {error && (
        <div className="card-glass" style={{ padding: "32px", textAlign: "center", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
          <AlertCircle size={32} color="#ef4444" style={{ margin: "0 auto 10px" }} />
          <h3 style={{ color: "#f87171", marginBottom: "8px" }}>Analytics Request Failed</h3>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>{error}</p>
          <button onClick={fetchAnalytics} className="btn-secondary">Retry</button>
        </div>
      )}

      {!loading && !error && analytics && (
        <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
          {/* Top KPI Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px" }}>
            <div className="card-glass" style={{ padding: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "8px" }}>
                <Search size={16} />
                <span>Total Searches</span>
              </div>
              <div style={{ fontSize: "2rem", fontWeight: 700, fontFamily: "var(--font-display)" }}>
                {analytics.total_searches}
              </div>
            </div>

            <div className="card-glass" style={{ padding: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "8px" }}>
                <AlertCircle size={16} color="#f59e0b" />
                <span>Zero-Result Queries</span>
              </div>
              <div style={{ fontSize: "2rem", fontWeight: 700, fontFamily: "var(--font-display)", color: analytics.zero_result_rate > 20 ? "#f87171" : "var(--text-primary)" }}>
                {analytics.zero_result_searches} <span style={{ fontSize: "1rem", color: "var(--text-muted)" }}>({analytics.zero_result_rate}%)</span>
              </div>
            </div>

            <div className="card-glass" style={{ padding: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "8px" }}>
                <Clock size={16} color="#34d399" />
                <span>Average Latency</span>
              </div>
              <div style={{ fontSize: "2rem", fontWeight: 700, fontFamily: "var(--font-display)", color: "#34d399" }}>
                {analytics.average_latency_ms} <span style={{ fontSize: "1rem" }}>ms</span>
              </div>
            </div>

            <div className="card-glass" style={{ padding: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "8px" }}>
                <TrendingUp size={16} color="var(--accent-purple)" />
                <span>p95 Search Latency</span>
              </div>
              <div style={{ fontSize: "2rem", fontWeight: 700, fontFamily: "var(--font-display)", color: "#c084fc" }}>
                {analytics.p95_latency_ms} <span style={{ fontSize: "1rem" }}>ms</span>
              </div>
            </div>
          </div>

          {/* Top Queries Table & Distribution */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "24px" }}>
            <div className="card-glass" style={{ padding: "28px" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "16px" }}>Top Search Queries</h3>
              {analytics.top_queries.length === 0 ? (
                <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No search queries recorded yet.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {analytics.top_queries.map((tq, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "rgba(255, 255, 255, 0.02)", borderRadius: "6px" }}>
                      <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.88rem", color: "#93c5fd" }}>
                        &ldquo;{tq.query}&rdquo;
                      </span>
                      <span style={{
                        background: "rgba(59, 130, 246, 0.15)",
                        color: "#93c5fd",
                        fontSize: "0.78rem",
                        padding: "2px 8px",
                        borderRadius: "10px",
                        fontWeight: 600
                      }}>
                        {tq.count} searches
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Searches Stream */}
            <div className="card-glass" style={{ padding: "28px" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "16px" }}>Recent Search Stream</h3>
              {analytics.recent_searches.length === 0 ? (
                <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No recent searches recorded.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "300px", overflowY: "auto" }}>
                  {analytics.recent_searches.slice(0, 10).map((rs) => (
                    <div key={rs.id} style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      fontSize: "0.82rem",
                      padding: "8px 10px",
                      borderBottom: "1px solid rgba(255, 255, 255, 0.03)"
                    }}>
                      <div>
                        <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{rs.query_text}</span>
                        <span style={{ color: "var(--text-muted)", marginLeft: "8px" }}>[{rs.index_name}]</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span style={{ color: rs.zero_result ? "#f87171" : "#34d399" }}>
                          {rs.results_count} hits
                        </span>
                        <span style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                          {rs.latency_ms}ms
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
