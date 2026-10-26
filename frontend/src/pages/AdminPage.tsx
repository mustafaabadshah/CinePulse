import React, { useState, useEffect } from "react";
import {
  Database,
  Upload,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Key,
  Play,
  ShieldAlert,
  Clock,
  FileSpreadsheet,
  Layers,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import {
  triggerImport,
  listImports,
  triggerReindex,
  getSourceFiles,
  getIndexStatus,
} from "../api/client";
import { ImportJob, IndexStatusSummary, SourceFilesStatus } from "../types";

export const AdminPage: React.FC = () => {
  const [apiKey, setApiKey] = useState(
    () => sessionStorage.getItem("rr_admin_key") || "rr_admin_secret_dev_key_change_me"
  );
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [importing, setImporting] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [sourceFiles, setSourceFiles] = useState<SourceFilesStatus | null>(null);
  const [indexStatus, setIndexStatus] = useState<IndexStatusSummary | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [showReindexConfirm, setShowReindexConfirm] = useState(false);
  const [showImportConfirm, setShowImportConfirm] = useState(false);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  // Save key
  useEffect(() => {
    sessionStorage.setItem("rr_admin_key", apiKey);
  }, [apiKey]);

  const loadData = async () => {
    setLoadingJobs(true);
    try {
      const [jobsData, filesData, idxData] = await Promise.all([
        listImports(apiKey).catch(() => []),
        getSourceFiles(apiKey).catch(() => null),
        getIndexStatus(apiKey).catch(() => null),
      ]);
      setJobs(jobsData);
      setSourceFiles(filesData);
      setIndexStatus(idxData);
    } catch (err: any) {
      console.warn("Could not load admin data with current key:", err);
    } finally {
      setLoadingJobs(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [apiKey]);

  const handleCsvImport = async (dryRun: boolean) => {
    setShowImportConfirm(false);
    setImporting(true);
    setNotification(null);
    try {
      const job = await triggerImport(null, dryRun, "csv", apiKey);
      setNotification({
        type: "success",
        message: `CSV ${dryRun ? "validation simulation (dry run)" : "import"} ${job.status === "completed" || job.status === "dry_run_completed" ? "completed successfully" : "finished with status: " + job.status}! Processed: ${job.records_processed}, Created: ${job.records_created}, Updated: ${job.records_updated}, Failed: ${job.records_failed}.`,
      });
      loadData();
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "CSV Import execution failed." });
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
        message: `Full reindexing completed! Synchronized: ${res.reindexed_counts.episodes || 0} episodes, ${res.reindexed_counts.programs || 0} programs, ${res.reindexed_counts.researchers || 0} researchers, ${res.reindexed_counts.publications || 0} publications, ${res.reindexed_counts.institutions || 0} institutions.`,
      });
      loadData();
    } catch (err: any) {
      setNotification({ type: "error", message: err.message || "Reindexing failed." });
    } finally {
      setReindexing(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(2)} MB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  return (
    <div style={{ maxWidth: "1160px", margin: "40px auto", padding: "0 24px" }}>
      {/* Page Title & Key */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
          marginBottom: "32px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Database size={24} color="var(--accent-blue)" />
            <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", fontWeight: 700 }}>
              Ingestion & Indexing Administration
            </h1>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Manage CSV production data pipelines, verify schema consistency, and monitor Meilisearch indexes.
          </p>
        </div>

        {/* API Key Input */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            padding: "6px 14px",
            borderRadius: "8px",
          }}
        >
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
              width: "220px",
              outline: "none",
            }}
          />
        </div>
      </div>

      {/* Notifications */}
      {notification && (
        <div
          style={{
            padding: "16px 20px",
            borderRadius: "10px",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            background: notification.type === "success" ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
            border: notification.type === "success" ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(239, 68, 68, 0.3)",
            color: notification.type === "success" ? "#34d399" : "#f87171",
            fontSize: "0.9rem",
          }}
        >
          {notification.type === "success" ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Two Main Admin Panels */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(500px, 1fr))", gap: "24px", marginBottom: "36px" }}>
        {/* Panel 1: CSV Source Files & Ingestion */}
        <div className="card-glass" style={{ padding: "28px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <FileSpreadsheet size={22} color="var(--accent-blue)" />
            <h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>Production CSV Ingestion Pipeline</h2>
          </div>

          <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", lineHeight: 1.5, margin: 0 }}>
            Inspects and ingests the canonical CSV files (<code>prod_enrichment.csv</code> and <code>episodes_prod.csv</code>) into the relational database and synchronizes them into Meilisearch.
          </p>

          {/* Files Status */}
          {sourceFiles && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", fontWeight: 600 }}>
                Configured Data Files ({sourceFiles.data_dir})
              </div>
              {Object.entries(sourceFiles.files).map(([key, f]) => (
                <div
                  key={key}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    fontSize: "0.85rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    {f.exists && f.readable ? (
                      <CheckCircle size={15} color="#34d399" />
                    ) : (
                      <AlertTriangle size={15} color="#f87171" />
                    )}
                    <span style={{ fontWeight: 500 }}>{f.filename}</span>
                  </div>
                  <div style={{ display: "flex", gap: "12px", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                    <span>{f.exists ? formatBytes(f.size_bytes) : "Missing"}</span>
                    {f.modified_at && <span>Mod: {new Date(f.modified_at).toLocaleDateString()}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: "flex", gap: "12px", marginTop: "auto", flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={() => handleCsvImport(true)}
              disabled={importing}
              className="btn-secondary"
              style={{ padding: "8px 16px", fontSize: "0.88rem" }}
            >
              {importing ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
              <span>Execute Dry Run (Safe)</span>
            </button>

            <button
              type="button"
              onClick={() => setShowImportConfirm(true)}
              disabled={importing}
              className="btn-primary"
              style={{ padding: "8px 18px", fontSize: "0.88rem" }}
            >
              <Upload size={14} />
              <span>{importing ? "Importing & Indexing..." : "Run Production Import"}</span>
            </button>
          </div>
        </div>

        {/* Panel 2: Meilisearch Index Synchronization */}
        <div className="card-glass" style={{ padding: "28px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Layers size={22} color="var(--accent-purple)" />
              <h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>Meilisearch Index Synchronization</h2>
            </div>
            {indexStatus && (
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "0.78rem",
                  padding: "3px 8px",
                  borderRadius: "9999px",
                  background: indexStatus.meilisearch_reachable ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                  color: indexStatus.meilisearch_reachable ? "#34d399" : "#f87171",
                }}
              >
                <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: indexStatus.meilisearch_reachable ? "#34d399" : "#f87171" }} />
                <span>{indexStatus.meilisearch_reachable ? "Connected (127.0.0.1:7700)" : "Disconnected"}</span>
              </span>
            )}
          </div>

          {/* Index Counts Table */}
          {indexStatus && (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 100px 100px 80px", padding: "4px 10px", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", fontWeight: 600 }}>
                <span>Index UID</span>
                <span style={{ textAlign: "right" }}>DB Records</span>
                <span style={{ textAlign: "right" }}>Indexed</span>
                <span style={{ textAlign: "right" }}>Status</span>
              </div>
              {Object.entries(indexStatus.indexes).map(([name, info]) => (
                <div
                  key={name}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 100px 100px 80px",
                    alignItems: "center",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    background: "rgba(255, 255, 255, 0.02)",
                    border: "1px solid var(--border-subtle)",
                    fontSize: "0.85rem",
                  }}
                >
                  <span style={{ fontWeight: 500, color: "var(--text-primary)" }}>{name}</span>
                  <span style={{ textAlign: "right", color: "var(--text-secondary)" }}>{info.database_count.toLocaleString()}</span>
                  <span style={{ textAlign: "right", color: "#60a5fa" }}>{info.indexed_count.toLocaleString()}</span>
                  <span style={{ textAlign: "right" }}>
                    <span
                      style={{
                        padding: "1px 6px",
                        borderRadius: "4px",
                        fontSize: "0.72rem",
                        fontWeight: 600,
                        background: info.is_synchronized ? "rgba(16, 185, 129, 0.15)" : "rgba(234, 179, 8, 0.15)",
                        color: info.is_synchronized ? "#34d399" : "#facc15",
                      }}
                    >
                      {info.is_synchronized ? "Synced" : "Mismatch"}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Operational Metrics */}
          {indexStatus && (
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", color: "var(--text-muted)", flexWrap: "wrap", gap: "8px" }}>
              <span>Pending Tasks: <strong style={{ color: "var(--text-primary)" }}>{indexStatus.pending_tasks_count}</strong></span>
              <span>Failed Tasks: <strong style={{ color: indexStatus.failed_tasks_count > 0 ? "#f87171" : "var(--text-primary)" }}>{indexStatus.failed_tasks_count}</strong></span>
              {indexStatus.last_sync_time && <span>Last Sync: {new Date(indexStatus.last_sync_time).toLocaleTimeString()}</span>}
            </div>
          )}

          {/* Reindex Button */}
          <div style={{ marginTop: "auto", display: "flex", justifyContent: "flex-end" }}>
            <button
              type="button"
              onClick={() => setShowReindexConfirm(true)}
              disabled={reindexing}
              className="btn-secondary"
              style={{ padding: "8px 18px", fontSize: "0.88rem", color: "#c084fc", borderColor: "rgba(168, 85, 247, 0.4)" }}
            >
              <RefreshCw size={14} className={reindexing ? "animate-spin" : ""} />
              <span>{reindexing ? "Rebuilding Indexes..." : "Rebuild All Indexes from DB"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation Modals */}
      {showImportConfirm && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "20px",
          }}
        >
          <div className="card-glass" style={{ maxWidth: "480px", width: "100%", padding: "32px", border: "1px solid rgba(59, 130, 246, 0.4)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
              <Upload size={24} color="#60a5fa" />
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700 }}>Confirm Production CSV Import</h3>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.5, marginBottom: "24px" }}>
              This will ingest records from <code>prod_enrichment.csv</code> and <code>episodes_prod.csv</code> into the relational database and upsert them into Meilisearch. Existing database records will be conflict-safely preserved.
            </p>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
              <button onClick={() => setShowImportConfirm(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={() => handleCsvImport(false)} className="btn-primary">
                Proceed with Import
              </button>
            </div>
          </div>
        </div>
      )}

      {showReindexConfirm && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "20px",
          }}
        >
          <div className="card-glass" style={{ maxWidth: "480px", width: "100%", padding: "32px", border: "1px solid rgba(245, 158, 11, 0.4)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
              <ShieldAlert size={24} color="#f59e0b" />
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700 }}>Confirm Full Search Rebuild</h3>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.5, marginBottom: "24px" }}>
              Are you sure you want to rebuild all Meilisearch indexes from the canonical database? All 5 indexes (episodes, programs, researchers, publications, institutions) will be re-synchronized.
            </p>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
              <button onClick={() => setShowReindexConfirm(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleReindex} className="btn-primary" style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)" }}>
                Yes, Rebuild Now
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
            <h3 style={{ fontSize: "1.15rem", fontWeight: 600 }}>Recent Ingestion Jobs & Reports</h3>
          </div>
          <button onClick={loadData} className="btn-secondary" style={{ padding: "6px 12px", fontSize: "0.8rem" }}>
            <RefreshCw size={13} />
            <span>Refresh</span>
          </button>
        </div>

        {loadingJobs ? (
          <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", padding: "20px 0" }}>Loading job history...</div>
        ) : jobs.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", padding: "20px 0", textAlign: "center" }}>
            No recent import jobs found. Click &ldquo;Execute Dry Run&rdquo; or &ldquo;Run Production Import&rdquo; above.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                  <th style={{ padding: "10px 12px" }}></th>
                  <th style={{ padding: "10px 12px" }}>Job ID</th>
                  <th style={{ padding: "10px 12px" }}>Status</th>
                  <th style={{ padding: "10px 12px" }}>Source</th>
                  <th style={{ padding: "10px 12px" }}>Mode</th>
                  <th style={{ padding: "10px 12px" }}>Processed</th>
                  <th style={{ padding: "10px 12px" }}>Created</th>
                  <th style={{ padding: "10px 12px" }}>Updated</th>
                  <th style={{ padding: "10px 12px" }}>Failed</th>
                  <th style={{ padding: "10px 12px" }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => {
                  const isExpanded = expandedJobId === j.id;
                  const isDry = j.dry_run;

                  return (
                    <React.Fragment key={j.id}>
                      <tr
                        onClick={() => setExpandedJobId(isExpanded ? null : j.id)}
                        style={{
                          borderBottom: isExpanded ? "none" : "1px solid rgba(255, 255, 255, 0.03)",
                          cursor: "pointer",
                          background: isExpanded ? "rgba(255, 255, 255, 0.03)" : "transparent",
                        }}
                      >
                        <td style={{ padding: "12px 6px 12px 12px", width: "24px" }}>
                          {isExpanded ? <ChevronDown size={14} color="#60a5fa" /> : <ChevronRight size={14} color="var(--text-muted)" />}
                        </td>
                        <td style={{ padding: "12px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                          {j.id.slice(0, 8)}...
                        </td>
                        <td style={{ padding: "12px" }}>
                          <span
                            style={{
                              padding: "2px 8px",
                              borderRadius: "4px",
                              fontSize: "0.75rem",
                              fontWeight: 600,
                              background:
                                j.status === "completed" || j.status === "dry_run_completed"
                                  ? "rgba(16, 185, 129, 0.15)"
                                  : "rgba(239, 68, 68, 0.15)",
                              color:
                                j.status === "completed" || j.status === "dry_run_completed"
                                  ? "#34d399"
                                  : "#f87171",
                            }}
                          >
                            {j.status}
                          </span>
                        </td>
                        <td style={{ padding: "12px", color: "var(--text-secondary)" }}>{j.source_name}</td>
                        <td style={{ padding: "12px", color: isDry ? "#fcd34d" : "var(--text-muted)" }}>
                          {isDry ? "Dry Run" : "Committed"}
                        </td>
                        <td style={{ padding: "12px", fontWeight: 500 }}>{j.records_processed.toLocaleString()}</td>
                        <td style={{ padding: "12px", color: "#34d399" }}>{j.records_created.toLocaleString()}</td>
                        <td style={{ padding: "12px", color: "#60a5fa" }}>{j.records_updated.toLocaleString()}</td>
                        <td style={{ padding: "12px", color: j.records_failed > 0 ? "#f87171" : "var(--text-muted)" }}>
                          {j.records_failed}
                        </td>
                        <td style={{ padding: "12px", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                          {new Date(j.started_at).toLocaleTimeString()}
                        </td>
                      </tr>

                      {/* Expanded Details Row */}
                      {isExpanded && (
                        <tr style={{ borderBottom: "1px solid var(--border-subtle)", background: "rgba(0, 0, 0, 0.2)" }}>
                          <td colSpan={10} style={{ padding: "16px 20px" }}>
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                                Detailed Report & Error Logs (Job {j.id}):
                              </div>
                              <pre
                                style={{
                                  background: "rgba(0, 0, 0, 0.4)",
                                  padding: "12px",
                                  borderRadius: "6px",
                                  fontSize: "0.78rem",
                                  color: "#a5b4fc",
                                  overflowX: "auto",
                                  maxHeight: "220px",
                                }}
                              >
                                {JSON.stringify(j.errors, null, 2)}
                              </pre>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
