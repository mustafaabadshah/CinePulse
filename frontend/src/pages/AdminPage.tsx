import React, { useState, useEffect } from "react";
import { Database, Upload, RefreshCw, CheckCircle, AlertTriangle, Key, Play, ShieldAlert, Clock } from "lucide-react";
import { triggerImport, listImports, triggerReindex } from "../api/client";
import { ImportJob } from "../types";

export const AdminPage: React.FC = () => {
  const [apiKey, setApiKey] = useState(() => sessionStorage.getItem("rr_admin_key") || "rr_admin_secret_dev_key_change_me");
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [importing, setImporting] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [dryRun, setDryRun] = useState(false);
  const [customPayload, setCustomPayload] = useState("");
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [showReindexConfirm, setShowReindexConfirm] = useState(false);

  // Save key
  useEffect(() => {
    sessionStorage.setItem("rr_admin_key", apiKey);
  }, [apiKey]);

  const loadJobs = async () => {
    setLoadingJobs(true);
    try {
      const data = await listImports(apiKey);
      setJobs(data);
    } catch (err: any) {
      console.warn("Could not load jobs with current key:", err);
    } finally {
      setLoadingJobs(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [apiKey]);

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setImporting(true);
    setNotification(null);
    try {
      let parsed = undefined;
      if (customPayload.trim()) {
        parsed = JSON.parse(customPayload.trim());
      }
      const job = await triggerImport(parsed, dryRun, apiKey);
      setNotification({
        type: "success",
        message: `Import job ${job.id.slice(0, 8)} ${dryRun ? "simulated (dry run)" : "executed"} successfully! Processed: ${job.records_processed}, Created: ${job.records_created}, Updated: ${job.records_updated}.`,
      });
      loadJobs();
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Import execution failed." });
    } finally {
      setImporting(false);
    }
  };

  const handleReindex = async () => {
    setShowReindexConfirm(false);
    setReindexing(true);
    setNotification(null);
    try {
      const res = await triggerReindex(apiKey);
      setNotification({
        type: "success",
        message: `Full reindexing completed! Indexed: ${res.reindexed_counts.researchers} researchers, ${res.reindexed_counts.publications} publications, ${res.reindexed_counts.institutions} institutions.`,
      });
      loadJobs();
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Reindexing failed." });
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "40px auto", padding: "0 24px" }}>
      {/* Page Title */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px", marginBottom: "32px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Database size={24} color="var(--accent-blue)" />
            <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", fontWeight: 700 }}>
              Ingestion & Indexing Administration
            </h1>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Manage source data ingestion, Meilisearch index synchronization, and dry-run validation.
          </p>
        </div>

        {/* API Key Input */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          background: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          padding: "6px 14px",
          borderRadius: "8px"
        }}>
          <Key size={16} color="var(--accent-amber)" />
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Admin API Key..."
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-primary)",
              fontSize: "0.85rem",
              width: "200px",
              outline: "none"
            }}
          />
        </div>
      </div>

      {/* Notifications */}
      {notification && (
        <div style={{
          padding: "16px 20px",
          borderRadius: "10px",
          marginBottom: "24px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          background: notification.type === "success" ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
          border: notification.type === "success" ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(239, 68, 68, 0.3)",
          color: notification.type === "success" ? "#34d399" : "#f87171",
          fontSize: "0.9rem"
        }}>
          {notification.type === "success" ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Operations Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))", gap: "24px", marginBottom: "36px" }}>
        {/* Ingestion Panel */}
        <div className="card-glass" style={{ padding: "28px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <Upload size={20} color="var(--accent-blue)" />
            <h3 style={{ fontSize: "1.2rem", fontWeight: 600 }}>Trigger Data Import</h3>
          </div>

          <form onSubmit={handleImport} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", lineHeight: 1.5 }}>
              Leave the custom JSON payload blank to automatically ingest the default canonical synthetic research fixture (24 records).
            </p>

            <textarea
              value={customPayload}
              onChange={(e) => setCustomPayload(e.target.value)}
              placeholder="Optional: Paste custom JSON payload (institutions, researchers, publications)..."
              rows={4}
              style={{
                width: "100%",
                background: "var(--bg-input)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "8px",
                padding: "10px 12px",
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
                fontSize: "0.82rem",
                outline: "none",
                resize: "vertical"
              }}
            />

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "0.88rem", color: "var(--text-secondary)" }}>
                <input
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  style={{ accentColor: "var(--accent-blue)" }}
                />
                <span>Dry Run Mode (Validate only without writing to DB/Meilisearch)</span>
              </label>

              <button
                type="submit"
                disabled={importing}
                className="btn-primary"
                style={{ padding: "8px 18px", fontSize: "0.88rem", opacity: importing ? 0.7 : 1 }}
              >
                {importing ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                <span>{importing ? "Ingesting..." : "Run Ingestion"}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Index Maintenance & Reindex Panel */}
        <div className="card-glass" style={{ padding: "28px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <RefreshCw size={20} color="var(--accent-purple)" />
              <h3 style={{ fontSize: "1.2rem", fontWeight: 600 }}>Meilisearch Reindexing</h3>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", lineHeight: 1.6, marginBottom: "16px" }}>
              Rebuilds Meilisearch indexes from the canonical SQLite/PostgreSQL relational records. Updates ranking rules, typo tolerance, searchable attributes, and synchronizes document documents.
            </p>
            <div style={{
              background: "rgba(99, 102, 241, 0.08)",
              border: "1px solid rgba(99, 102, 241, 0.25)",
              padding: "12px 16px",
              borderRadius: "8px",
              fontSize: "0.82rem",
              color: "#a5b4fc"
            }}>
              <strong>Idempotent:</strong> Reindexing creates missing indexes, verifies primary keys, and preserves relational consistency.
            </div>
          </div>

          <div style={{ marginTop: "24px", display: "flex", justifyContent: "flex-end" }}>
            <button
              onClick={() => setShowReindexConfirm(true)}
              disabled={reindexing}
              className="btn-secondary"
              style={{ padding: "10px 20px", color: "#c084fc", borderColor: "rgba(168, 85, 247, 0.4)" }}
            >
              <RefreshCw size={16} />
              <span>{reindexing ? "Reindexing in Progress..." : "Reindex All Records"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showReindexConfirm && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0, 0, 0, 0.7)",
          backdropFilter: "blur(6px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 100,
          padding: "20px"
        }}>
          <div className="card-glass" style={{ maxWidth: "480px", width: "100%", padding: "32px", border: "1px solid rgba(245, 158, 11, 0.4)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
              <ShieldAlert size={24} color="#f59e0b" />
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700 }}>Confirm Full Reindex</h3>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.5, marginBottom: "24px" }}>
              Are you sure you want to reindex all canonical records from relational storage into Meilisearch? Existing search indexes will be refreshed with current database records.
            </p>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
              <button onClick={() => setShowReindexConfirm(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleReindex} className="btn-primary" style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)" }}>
                Yes, Reindex Now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ingestion Jobs History Table */}
      <div className="card-glass" style={{ padding: "28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Clock size={18} color="var(--text-muted)" />
            <h3 style={{ fontSize: "1.15rem", fontWeight: 600 }}>Recent Ingestion Jobs</h3>
          </div>
          <button onClick={loadJobs} className="btn-secondary" style={{ padding: "6px 12px", fontSize: "0.8rem" }}>
            <RefreshCw size={13} />
            <span>Refresh</span>
          </button>
        </div>

        {loadingJobs ? (
          <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", padding: "20px 0" }}>Loading job history...</div>
        ) : jobs.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", padding: "20px 0", textAlign: "center" }}>
            No recent import jobs found. Click &ldquo;Run Ingestion&rdquo; above to load the fixture.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                  <th style={{ padding: "10px 12px" }}>Job ID</th>
                  <th style={{ padding: "10px 12px" }}>Status</th>
                  <th style={{ padding: "10px 12px" }}>Source</th>
                  <th style={{ padding: "10px 12px" }}>Mode</th>
                  <th style={{ padding: "10px 12px" }}>Processed</th>
                  <th style={{ padding: "10px 12px" }}>Created</th>
                  <th style={{ padding: "10px 12px" }}>Updated</th>
                  <th style={{ padding: "10px 12px" }}>Failed</th>
                  <th style={{ padding: "10px 12px" }}>Meili Tasks</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.03)" }}>
                    <td style={{ padding: "12px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                      {j.id.slice(0, 8)}...
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span style={{
                        padding: "2px 8px",
                        borderRadius: "4px",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        background: j.status === "completed" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                        color: j.status === "completed" ? "#34d399" : "#f87171"
                      }}>
                        {j.status}
                      </span>
                    </td>
                    <td style={{ padding: "12px", color: "var(--text-secondary)" }}>{j.source_name}</td>
                    <td style={{ padding: "12px", color: j.dry_run ? "#fcd34d" : "var(--text-muted)" }}>
                      {j.dry_run ? "Dry Run" : "Committed"}
                    </td>
                    <td style={{ padding: "12px", fontWeight: 500 }}>{j.records_processed}</td>
                    <td style={{ padding: "12px", color: "#34d399" }}>{j.records_created}</td>
                    <td style={{ padding: "12px", color: "#60a5fa" }}>{j.records_updated}</td>
                    <td style={{ padding: "12px", color: j.records_failed > 0 ? "#f87171" : "var(--text-muted)" }}>
                      {j.records_failed}
                    </td>
                    <td style={{ padding: "12px", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                      {j.meili_task_ids && j.meili_task_ids.length > 0 ? j.meili_task_ids.join(", ") : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
