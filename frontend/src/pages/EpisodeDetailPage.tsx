import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Play,
  Tv,
  Clock,
  Eye,
  ArrowLeft,
  Globe,
  Tag,
  Film,
  Users,
  CheckCircle,
  ExternalLink,
} from "lucide-react";
import { getEpisode } from "../api/client";
import { Episode } from "../types";

export const EpisodeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    getEpisode(id)
      .then((data) => setEpisode(data))
      .catch((err) => setError(err.message || "Failed to load episode details."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div style={{ maxWidth: "1000px", margin: "40px auto", padding: "0 24px" }}>
        <div className="card-glass" style={{ padding: "40px", textAlign: "center" }}>
          <div className="animate-pulse" style={{ color: "var(--text-secondary)" }}>
            Loading episode details...
          </div>
        </div>
      </div>
    );
  }

  if (error || !episode) {
    return (
      <div style={{ maxWidth: "1000px", margin: "40px auto", padding: "0 24px" }}>
        <div className="card-glass" style={{ padding: "40px", textAlign: "center", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
          <h2 style={{ color: "#f87171", marginBottom: "12px" }}>Episode Not Found</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "20px" }}>{error || "The requested episode does not exist."}</p>
          <Link to="/search?type=episodes" className="btn-secondary">
            <ArrowLeft size={16} />
            <span>Back to Episodes Search</span>
          </Link>
        </div>
      </div>
    );
  }

  const formatViews = (views: number) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(2)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toLocaleString();
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "32px 24px" }}>
      {/* Back button */}
      <div style={{ marginBottom: "20px" }}>
        <Link
          to="/search?type=episodes"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            color: "var(--text-muted)",
            fontSize: "0.9rem",
            textDecoration: "none",
            transition: "color var(--transition-fast)",
          }}
        >
          <ArrowLeft size={16} />
          <span>Back to Search</span>
        </Link>
      </div>

      {/* Main Episode Header Card */}
      <article className="card-glass animate-fade-in" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ display: "flex", gap: "28px", flexWrap: "wrap", alignItems: "flex-start" }}>
          {/* Thumbnail */}
          {episode.thumbnail && (
            <div
              style={{
                width: "300px",
                maxWidth: "100%",
                borderRadius: "12px",
                overflow: "hidden",
                border: "1px solid var(--border-card)",
                background: "rgba(0, 0, 0, 0.5)",
                boxShadow: "var(--shadow-md)",
                flexShrink: 0,
              }}
            >
              <img
                src={episode.thumbnail}
                alt={episode.title}
                style={{ width: "100%", height: "auto", display: "block", objectFit: "cover" }}
              />
            </div>
          )}

          {/* Core Info */}
          <div style={{ flex: 1, minWidth: "280px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
              <span className="badge badge-episode">
                <Play size={12} />
                <span>Episode</span>
              </span>
              <span className={`badge ${episode.is_free ? "badge-free" : "badge-pro"}`}>
                <span>{episode.is_free ? "Free to Watch" : "Premium"}</span>
              </span>
              {episode.content_tier && (
                <span
                  style={{
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "rgba(255, 255, 255, 0.08)",
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                  }}
                >
                  {episode.content_tier}
                </span>
              )}
              {episode.is_vertical && (
                <span className="badge badge-program">
                  <Film size={12} />
                  <span>Vertical Short</span>
                </span>
              )}
            </div>

            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, lineHeight: 1.3, marginBottom: "12px", color: "var(--text-primary)" }}>
              {episode.title}
            </h1>

            {/* Metrics Row */}
            <div style={{ display: "flex", alignItems: "center", gap: "20px", flexWrap: "wrap", color: "var(--text-secondary)", fontSize: "0.92rem", marginBottom: "16px" }}>
              {episode.duration && (
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Clock size={16} color="var(--accent-blue)" />
                  <span>{episode.duration} ({episode.duration_seconds || 0}s)</span>
                </div>
              )}
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Eye size={16} color="#34d399" />
                <span>{formatViews(episode.views)} total views</span>
              </div>
              {episode.channel_name && (
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Tv size={16} color="#d8b4fe" />
                  <span>{episode.channel_name}</span>
                </div>
              )}
            </div>

            {/* Genres */}
            {episode.genre_list && episode.genre_list.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "16px" }}>
                {episode.genre_list.map((g, idx) => (
                  <span key={idx} className="tag-topic">
                    <Tag size={12} style={{ marginRight: "4px", display: "inline" }} />
                    {g}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Parent Program Link Card */}
        {episode.program && (
          <div
            style={{
              padding: "20px",
              borderRadius: "10px",
              background: "rgba(59, 130, 246, 0.08)",
              border: "1px solid rgba(59, 130, 246, 0.25)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Tv size={18} color="var(--accent-blue)" />
                <span style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", fontWeight: 600 }}>
                  Part of TV Series / Franchise
                </span>
              </div>
              <Link
                to={`/programs/${encodeURIComponent(episode.program.id)}`}
                style={{
                  color: "#60a5fa",
                  fontSize: "0.88rem",
                  fontWeight: 500,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <span>View Program Details</span>
                <ExternalLink size={14} />
              </Link>
            </div>

            <h3 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "6px" }}>
              <Link to={`/programs/${encodeURIComponent(episode.program.id)}`} style={{ color: "var(--text-primary)" }}>
                {episode.program.name}
              </Link>
            </h3>

            <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)", display: "flex", gap: "16px", flexWrap: "wrap" }}>
              {episode.program.channel_name && <span>Channel: <strong>{episode.program.channel_name}</strong></span>}
              {episode.program.info_language && <span>Language: <strong>{episode.program.info_language}</strong></span>}
              {episode.program.info_content_type && <span>Format: <strong>{episode.program.info_content_type}</strong></span>}
            </div>

            {episode.program.info_staring && (
              <div style={{ marginTop: "8px", fontSize: "0.88rem", color: "var(--text-muted)" }}>
                <Users size={14} style={{ display: "inline", marginRight: "6px" }} />
                <span>Cast: {episode.program.info_staring}</span>
              </div>
            )}
          </div>
        )}

        {/* Synopsis / Description */}
        {episode.description && (
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "8px" }}>Synopsis & Description</h3>
            <p
              style={{
                color: "var(--text-secondary)",
                lineHeight: "1.65",
                fontSize: "0.95rem",
                whiteSpace: "pre-line",
                background: "rgba(0, 0, 0, 0.2)",
                padding: "16px 20px",
                borderRadius: "8px",
                border: "1px solid var(--border-subtle)",
              }}
            >
              {episode.description}
            </p>
          </div>
        )}

        {/* Geographic Distribution & Provenance */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
          {episode.region && (
            <div style={{ padding: "16px", borderRadius: "8px", background: "var(--bg-card)", border: "1px solid var(--border-card)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                <Globe size={15} />
                <span>Licensed Broadcast Regions</span>
              </div>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{episode.region}</div>
            </div>
          )}

          <div style={{ padding: "16px", borderRadius: "8px", background: "var(--bg-card)", border: "1px solid var(--border-card)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              <CheckCircle size={15} color="#34d399" />
              <span>Canonical Ingestion Source</span>
            </div>
            <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
              File: <code style={{ color: "#93c5fd" }}>{episode.source_file}</code>
              {episode.imported_at && <div>Imported: {new Date(episode.imported_at).toLocaleString()}</div>}
            </div>
          </div>
        </div>

        {/* Sibling Episodes from the Same Show */}
        {episode.sibling_episodes && episode.sibling_episodes.length > 0 && (
          <div>
            <h3 style={{ fontSize: "1.15rem", fontWeight: 600, marginBottom: "14px" }}>
              More from this Program
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "14px" }}>
              {episode.sibling_episodes.map((sib) => (
                <Link
                  key={sib.id}
                  to={`/episodes/${encodeURIComponent(sib.id)}`}
                  className="card-glass"
                  style={{
                    padding: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                    textDecoration: "none",
                  }}
                >
                  {sib.thumbnail && (
                    <div style={{ width: "100%", height: "100px", borderRadius: "6px", overflow: "hidden", background: "#000" }}>
                      <img src={sib.thumbnail} alt={sib.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    </div>
                  )}
                  <h4
                    style={{
                      fontSize: "0.88rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                      margin: 0,
                    }}
                  >
                    {sib.title}
                  </h4>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    <span>{sib.duration}</span>
                    <span>{formatViews(sib.views)} views</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </article>
    </div>
  );
};
