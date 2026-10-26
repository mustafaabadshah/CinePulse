import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Tv,
  ArrowLeft,
  Users,
  Tag,
  Globe,
  Film,
  CheckCircle,
  Clock,
  Eye,
} from "lucide-react";
import { getProgram } from "../api/client";
import { Program } from "../types";
import { formatDuration } from "../utils/formatDuration";
import { MediaImage } from "../components/MediaImage";

export const ProgramDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [program, setProgram] = useState<Program | null>(null);
  const [episodeSort, setEpisodeSort] = useState<"sequence" | "views">("sequence");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    getProgram(id, episodeSort)
      .then((data) => setProgram(data))
      .catch((err) => setError(err.message || "Failed to load program details."))
      .finally(() => setLoading(false));
  }, [id, episodeSort]);

  if (loading) {
    return (
      <div style={{ maxWidth: "1000px", margin: "40px auto", padding: "0 24px" }}>
        <div className="card-glass" style={{ padding: "40px", textAlign: "center" }}>
          <div className="animate-pulse" style={{ color: "var(--text-secondary)" }}>
            Loading program details...
          </div>
        </div>
      </div>
    );
  }

  if (error || !program) {
    return (
      <div style={{ maxWidth: "1000px", margin: "40px auto", padding: "0 24px" }}>
        <div className="card-glass" style={{ padding: "40px", textAlign: "center", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
          <h2 style={{ color: "#f87171", marginBottom: "12px" }}>Program Not Found</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "20px" }}>{error || "The requested show or channel does not exist."}</p>
          <Link to="/search?type=programs" className="btn-secondary">
            <ArrowLeft size={16} />
            <span>Back to Programs Search</span>
          </Link>
        </div>
      </div>
    );
  }

  const formatViews = (views?: number) => {
    if (!views) return "0";
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toLocaleString();
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "32px 24px" }}>
      {/* Back button */}
      <div style={{ marginBottom: "20px" }}>
        <Link
          to="/search?type=programs"
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

      {/* Program Header Card */}
      <article className="card-glass animate-fade-in" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ display: "flex", gap: "24px", flexWrap: "wrap", alignItems: "flex-start" }}>
          {/* Program Poster */}
          <div style={{ width: "160px", flexShrink: 0, borderRadius: "10px", overflow: "hidden" }}>
            <MediaImage
              src={program.thumbnail || (program.episodes && program.episodes[0]?.thumbnail)}
              alt={program.name}
              type={program.type === "channel" ? "channel" : "program"}
              aspectRatio="3 / 4"
              title={program.name}
            />
          </div>

          <div style={{ flex: 1, minWidth: "260px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
            <span className="badge badge-program">
              <Tv size={12} />
              <span>{program.type || "Program"}</span>
            </span>
            {program.channel_name && (
              <span
                style={{
                  padding: "2px 10px",
                  borderRadius: "9999px",
                  background: "rgba(168, 85, 247, 0.15)",
                  color: "#d8b4fe",
                  border: "1px solid rgba(168, 85, 247, 0.3)",
                  fontSize: "0.75rem",
                  fontWeight: 500,
                  textTransform: "uppercase",
                }}
              >
                {program.channel_name}
              </span>
            )}
            {program.info_language && (
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
                <Globe size={11} style={{ display: "inline", marginRight: "4px" }} />
                {program.info_language}
              </span>
            )}
            {program.info_content_type && (
              <span
                style={{
                  padding: "2px 8px",
                  borderRadius: "4px",
                  background: "rgba(59, 130, 246, 0.12)",
                  fontSize: "0.75rem",
                  color: "#93c5fd",
                }}
              >
                <Film size={11} style={{ display: "inline", marginRight: "4px" }} />
                {program.info_content_type}
              </span>
            )}
          </div>

          <h1 style={{ fontSize: "2rem", fontWeight: 700, lineHeight: 1.3, marginBottom: "8px", color: "var(--text-primary)" }}>
            {program.name}
          </h1>

            <div style={{ color: "var(--text-muted)", fontSize: "0.88rem" }}>
              Slug: <code style={{ color: "#93c5fd" }}>{program.slug}</code> • ID: <code>{program.id}</code>
            </div>
          </div>
        </div>

        {/* Cast & Starring */}
        {program.info_staring && (
          <div style={{ padding: "18px 20px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.25)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px", color: "var(--text-muted)", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
              <Users size={15} color="var(--accent-blue)" />
              <span>Cast & Starring</span>
            </div>
            <div style={{ fontSize: "1rem", color: "var(--text-primary)", lineHeight: 1.5 }}>
              {program.info_staring}
            </div>
          </div>
        )}

        {/* Genres & Keywords */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
          {program.genre_list && program.genre_list.map((g, idx) => (
            <span key={idx} className="tag-topic">
              <Tag size={12} style={{ marginRight: "4px", display: "inline" }} />
              {g}
            </span>
          ))}
          {program.info_meta_keywords && (
            <span style={{ fontSize: "0.82rem", color: "var(--text-muted)", alignSelf: "center", fontStyle: "italic" }}>
              Keywords: {program.info_meta_keywords}
            </span>
          )}
        </div>

        {/* Ingestion Provenance */}
        <div style={{ padding: "14px 18px", borderRadius: "8px", background: "var(--bg-card)", border: "1px solid var(--border-card)", fontSize: "0.85rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "8px" }}>
          <CheckCircle size={15} color="#34d399" />
          <span>Source Catalog: <code>{program.source_file}</code></span>
          {program.imported_at && <span>• Imported: {new Date(program.imported_at).toLocaleString()}</span>}
        </div>

        {/* Child Episodes List */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "10px", flexWrap: "wrap", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
              <h2 style={{ fontSize: "1.3rem", fontWeight: 600, margin: 0 }}>
                Episodes ({program.episode_count || 0})
              </h2>

              {/* Sequence Sorting Control */}
              <div style={{ display: "flex", gap: "6px", background: "rgba(255, 255, 255, 0.05)", padding: "3px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                <button
                  onClick={() => setEpisodeSort("sequence")}
                  style={{
                    padding: "4px 10px",
                    borderRadius: "6px",
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    border: "none",
                    background: episodeSort === "sequence" ? "var(--accent-red)" : "transparent",
                    color: episodeSort === "sequence" ? "#ffffff" : "var(--text-muted)",
                    transition: "all var(--transition-fast)",
                  }}
                >
                  Chronological Order
                </button>
                <button
                  onClick={() => setEpisodeSort("views")}
                  style={{
                    padding: "4px 10px",
                    borderRadius: "6px",
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    border: "none",
                    background: episodeSort === "views" ? "var(--accent-red)" : "transparent",
                    color: episodeSort === "views" ? "#ffffff" : "var(--text-muted)",
                    transition: "all var(--transition-fast)",
                  }}
                >
                  Most Viewed
                </button>
              </div>
            </div>

            <Link
              to={`/search?type=episodes&program_id=${encodeURIComponent(program.id)}`}
              style={{ color: "#60a5fa", fontSize: "0.88rem", fontWeight: 500 }}
            >
              Search all episodes
            </Link>
          </div>

          {program.episodes && program.episodes.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "16px" }}>
              {program.episodes.map((ep) => (
                <Link
                  key={ep.id}
                  to={`/episodes/${encodeURIComponent(ep.id)}`}
                  className="card-glass"
                  style={{
                    padding: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px",
                    textDecoration: "none",
                  }}
                >
                  <div style={{ width: "100%", borderRadius: "8px", overflow: "hidden", position: "relative" }}>
                    <MediaImage
                      src={ep.thumbnail}
                      alt={ep.title}
                      type="episode"
                      aspectRatio="16 / 9"
                      showPlayBadge={true}
                    />
                    {ep.episode_number !== undefined && ep.episode_number !== null && (
                      <div
                        style={{
                          position: "absolute",
                          top: "6px",
                          left: "6px",
                          background: "rgba(0, 0, 0, 0.75)",
                          color: "#ffffff",
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "4px",
                          border: "1px solid rgba(255, 255, 255, 0.15)",
                          zIndex: 2,
                        }}
                      >
                        EP {ep.episode_number}
                      </div>
                    )}
                  </div>

                  <h3
                    style={{
                      fontSize: "0.92rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                      margin: 0,
                      lineHeight: 1.4,
                    }}
                  >
                    {ep.title}
                  </h3>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    {ep.duration && (
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                        <Clock size={11} />
                        {formatDuration(ep.duration_seconds, ep.duration)}
                      </span>
                    )}
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                      <Eye size={11} />
                      {formatViews(ep.views)}
                    </span>
                    <span className={`badge ${ep.is_free ? "badge-free" : "badge-pro"}`} style={{ padding: "1px 6px", fontSize: "0.7rem" }}>
                      {ep.is_free ? "Free" : "Pro"}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div style={{ color: "var(--text-muted)", padding: "20px 0", textAlign: "center" }}>
              No episodes currently associated with this program.
            </div>
          )}
        </div>
      </article>
    </div>
  );
};
