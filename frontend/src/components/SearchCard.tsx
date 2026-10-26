import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Play,
  Tv,
  Radio,
  Clock,
  Eye,
  Users,
  Film,
} from "lucide-react";
import { SearchResultItem } from "../types";

interface SearchCardProps {
  item: SearchResultItem;
}

export const SearchCard: React.FC<SearchCardProps> = ({ item }) => {
  const [imageFailed, setImageFailed] = useState(false);

  const isEpisode = item.type === "episode";
  const isChannel = !isEpisode && (item.raw?.type === "channel" || item.raw?.info_content_type === "channel");
  
  const detailPath = isEpisode 
    ? `/episodes/${encodeURIComponent(item.id)}` 
    : `/programs/${encodeURIComponent(item.id)}`;

  // Highlighted matching text from Meilisearch formatted object
  const displayTitle = item.formatted?.title || item.formatted?.name || item.title;
  const displaySnippet = item.formatted?.description || item.snippet;

  // Format view count nicely
  const formatViews = (views?: number) => {
    if (!views && views !== 0) return null;
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toLocaleString();
  };

  const thumbnail = item.thumbnail || item.raw?.thumbnail;

  return (
    <article
      className="card-glass animate-fade-in"
      style={{
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        transition: "all var(--transition-normal)",
      }}
    >
      {/* Top Meta Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
          {/* Entity Type Badge */}
          {isEpisode ? (
            <span className="badge badge-episode">
              <Play size={11} fill="currentColor" />
              <span>Episode</span>
            </span>
          ) : isChannel ? (
            <span className="badge badge-channel">
              <Radio size={11} />
              <span>Channel</span>
            </span>
          ) : (
            <span className="badge badge-program">
              <Tv size={11} />
              <span>Show</span>
            </span>
          )}

          {/* Episode Specific Badges */}
          {isEpisode && (
            <>
              <span className={`badge ${item.is_free ? "badge-free" : "badge-pro"}`}>
                <span>{item.is_free ? "Free" : "Premium"}</span>
              </span>

              {item.content_tier && (
                <span
                  style={{
                    fontSize: "0.72rem",
                    padding: "2px 7px",
                    borderRadius: "4px",
                    background: "rgba(255, 255, 255, 0.08)",
                    color: "var(--text-secondary)",
                    textTransform: "uppercase",
                    fontWeight: 600,
                  }}
                >
                  {item.content_tier}
                </span>
              )}

              {item.duration && (
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                  }}
                >
                  <Clock size={12} />
                  <span>{item.duration}</span>
                </span>
              )}

              {item.views !== undefined && (
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                  }}
                >
                  <Eye size={12} />
                  <span>{formatViews(item.views)} views</span>
                </span>
              )}
            </>
          )}

          {/* Program/Channel Badges */}
          {!isEpisode && (
            <>
              {item.raw?.info_language && (
                <span
                  style={{
                    fontSize: "0.72rem",
                    padding: "2px 7px",
                    borderRadius: "4px",
                    background: "rgba(255, 255, 255, 0.08)",
                    color: "var(--text-secondary)",
                    fontWeight: 600,
                    textTransform: "uppercase",
                  }}
                >
                  {item.raw.info_language}
                </span>
              )}

              {item.raw?.channel_name && (
                <span
                  style={{
                    fontSize: "0.72rem",
                    padding: "2px 7px",
                    borderRadius: "4px",
                    background: "rgba(229, 9, 20, 0.12)",
                    color: "#fca5a5",
                    fontWeight: 600,
                  }}
                >
                  {item.raw.channel_name}
                </span>
              )}
            </>
          )}
        </div>

        {/* Channel or Parent Label */}
        {item.channel_name && (
          <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
            {item.channel_name}
          </span>
        )}
      </div>

      {/* Main Body with Media Thumbnail */}
      <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
        {thumbnail && !imageFailed ? (
          <Link
            to={detailPath}
            style={{
              flexShrink: 0,
              width: "135px",
              aspectRatio: "16 / 9",
              borderRadius: "8px",
              overflow: "hidden",
              border: "1px solid var(--border-subtle)",
              background: "#080a0f",
              position: "relative",
              display: "block",
            }}
          >
            <img
              src={thumbnail}
              alt={item.title}
              loading="lazy"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transition: "transform var(--transition-normal)",
              }}
              onError={() => setImageFailed(true)}
            />
            {isEpisode && (
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "rgba(0, 0, 0, 0.35)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  opacity: 0.85,
                }}
              >
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "50%",
                    background: "var(--accent-red)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.5)",
                  }}
                >
                  <Play size={13} fill="#ffffff" color="#ffffff" style={{ marginLeft: "2px" }} />
                </div>
              </div>
            )}
          </Link>
        ) : (
          <Link
            to={detailPath}
            style={{
              flexShrink: 0,
              width: "100px",
              height: "64px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px dashed var(--border-card)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--text-muted)",
            }}
          >
            {isEpisode ? <Film size={20} /> : <Tv size={20} />}
          </Link>
        )}

        {/* Content Details */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{ fontSize: "1.12rem", fontWeight: 700, lineHeight: 1.35, marginBottom: "4px" }}>
            <Link
              to={detailPath}
              style={{ color: "var(--text-primary)", transition: "color var(--transition-fast)" }}
              dangerouslySetInnerHTML={{ __html: displayTitle }}
            />
          </h3>

          {/* Program name connection for episodes */}
          {item.program_name && (
            <div style={{ color: "var(--accent-red)", fontSize: "0.85rem", fontWeight: 600, marginBottom: "6px" }}>
              Show: {item.program_name}
            </div>
          )}

          {/* Cast/Starring for programs */}
          {!isEpisode && item.raw?.info_staring && (
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-secondary)", fontSize: "0.82rem", marginBottom: "6px" }}>
              <Users size={13} color="var(--accent-gold)" />
              <span>Cast: {item.raw.info_staring}</span>
            </div>
          )}

          {/* Description snippet */}
          {displaySnippet && (
            <p
              style={{
                color: "var(--text-secondary)",
                fontSize: "0.88rem",
                lineHeight: "1.5",
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
                margin: 0,
              }}
              dangerouslySetInnerHTML={{ __html: displaySnippet }}
            />
          )}
        </div>
      </div>

      {/* Tags / Genres */}
      {item.tags && item.tags.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "2px" }}>
          {item.tags.slice(0, 5).map((tag, idx) => (
            <span key={idx} className="tag-genre">
              {tag}
            </span>
          ))}
          {item.tags.length > 5 && (
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", alignSelf: "center" }}>
              +{item.tags.length - 5} more
            </span>
          )}
        </div>
      )}
    </article>
  );
};
