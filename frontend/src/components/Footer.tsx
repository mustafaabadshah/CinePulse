import React from "react";
import { ExternalLink, Database, Film } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer style={{
      borderTop: "1px solid var(--border-subtle)",
      background: "var(--bg-secondary)",
      padding: "40px 24px 30px",
      marginTop: "60px",
      color: "var(--text-muted)",
      fontSize: "0.85rem"
    }}>
      <div style={{
        maxWidth: "1400px",
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "24px"
      }}>
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "20px"
        }}>
          <div>
            <div style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "1.1rem",
              color: "var(--text-primary)",
              marginBottom: "6px",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}>
              <Film size={18} color="var(--accent-red)" />
              <span>Tamasha Catalog Explorer</span>
            </div>
            <p style={{ maxWidth: "480px", lineHeight: "1.6" }}>
              High-performance OTT media discovery platform powered by Meilisearch and canonical SQLite storage.
              Search across programs, live channels, full episodes, genres, and cast metadata.
            </p>
          </div>

          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            background: "rgba(229, 9, 20, 0.08)",
            border: "1px solid rgba(229, 9, 20, 0.25)",
            padding: "12px 18px",
            borderRadius: "10px",
            maxWidth: "480px"
          }}>
            <Database size={20} color="var(--accent-red)" style={{ flexShrink: 0 }} />
            <div style={{ color: "#fca5a5", fontSize: "0.8rem", lineHeight: "1.4" }}>
              <strong>Verified Canonical Catalog:</strong> Populated exclusively from verified production exports (634 programs/channels and 6,547 video episodes). Preserves orphan episodes with accurate parent resolution.
            </div>
          </div>
        </div>

        <div style={{
          borderTop: "1px solid rgba(255, 255, 255, 0.05)",
          paddingTop: "20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px"
        }}>
          <div>
            &copy; 2026 Tamasha Catalog Explorer. Media Discovery Powered by Meilisearch.
          </div>
          <div style={{ display: "flex", gap: "20px" }}>
            <a
              href="https://www.meilisearch.com/docs"
              target="_blank"
              rel="noreferrer"
              style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-secondary)" }}
            >
              <span>Meilisearch Docs</span>
              <ExternalLink size={13} />
            </a>
            <span style={{ color: "var(--text-muted)" }}>SQLite &bull; FastAPI &bull; React</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
