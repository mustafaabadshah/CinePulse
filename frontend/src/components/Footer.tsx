import React from "react";
import { Shield, ExternalLink } from "lucide-react";

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
        maxWidth: "1280px",
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
              marginBottom: "6px"
            }}>
              ResearchRadar
            </div>
            <p style={{ maxWidth: "450px", lineHeight: "1.6" }}>
              High-performance academic discovery engine powered by open-source Meilisearch.
              Search across publications, faculty, institutions, and emerging technical domains.
            </p>
          </div>

          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.25)",
            padding: "12px 18px",
            borderRadius: "10px",
            maxWidth: "460px"
          }}>
            <Shield size={20} color="#f59e0b" style={{ flexShrink: 0 }} />
            <div style={{ color: "#fbbf24", fontSize: "0.8rem", lineHeight: "1.4" }}>
              <strong>Synthetic Data Notice:</strong> Sample demonstration records are explicitly marked synthetic. No real professors' emails are harvested or fabricated without verified source provenance.
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
            &copy; 2026 ResearchRadar. Open Source Discovery Engine.
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
            <a
              href="https://github.com/meilisearch/meilisearch"
              target="_blank"
              rel="noreferrer"
              style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-secondary)" }}
            >
              <span>Meilisearch Engine</span>
              <ExternalLink size={13} />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
