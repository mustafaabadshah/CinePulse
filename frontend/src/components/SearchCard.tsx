import React from "react";
import { Link } from "react-router-dom";
import {
  User,
  BookOpen,
  Building2,
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  Play,
  Tv,
  Clock,
  Eye,
} from "lucide-react";
import { SearchResultItem } from "../types";

interface SearchCardProps {
  item: SearchResultItem;
}

export const SearchCard: React.FC<SearchCardProps> = ({ item }) => {
  const getDetailPath = () => {
    switch (item.type) {
      case "researcher":
        return `/researchers/${encodeURIComponent(item.id)}`;
      case "publication":
        return `/publications/${encodeURIComponent(item.id)}`;
      case "institution":
        return `/institutions/${encodeURIComponent(item.id)}`;
      case "episode":
        return `/episodes/${encodeURIComponent(item.id)}`;
      case "program":
        return `/programs/${encodeURIComponent(item.id)}`;
      default:
        return "#";
    }
  };

  const getBadgeClass = () => {
    switch (item.type) {
      case "researcher":
        return "badge-researcher";
      case "publication":
        return "badge-publication";
      case "institution":
        return "badge-institution";
      case "episode":
        return "badge-episode";
      case "program":
        return "badge-program";
      default:
        return "badge-publication";
    }
  };

  const getIcon = () => {
    switch (item.type) {
      case "researcher":
        return <User size={13} />;
      case "publication":
        return <BookOpen size={13} />;
      case "institution":
        return <Building2 size={13} />;
      case "episode":
        return <Play size={13} />;
      case "program":
        return <Tv size={13} />;
      default:
        return null;
    }
  };

  // Check if highlighted version is available
  const displayTitle = item.formatted?.title || item.formatted?.full_name || item.formatted?.name || item.title;
  const displaySnippet = item.formatted?.description || item.formatted?.abstract || item.formatted?.biography || item.snippet;

  // Format view count
  const formatViews = (views?: number) => {
    if (!views) return "0";
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toLocaleString();
  };

  const thumbnail = item.raw?.thumbnail || (item.type === "episode" ? item.source_url : undefined);

  return (
    <article
      className="card-glass animate-fade-in"
      style={{
        padding: "20px 24px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
      }}
    >
      {/* Header Badges */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
          <span className={`badge ${getBadgeClass()}`}>
            {getIcon()}
            <span>{item.type}</span>
          </span>

          {item.is_synthetic && (
            <span className="badge badge-synthetic">
              <AlertTriangle size={12} />
              <span>Synthetic</span>
            </span>
          )}

          {item.type === "episode" && (
            <>
              <span className={`badge ${item.raw?.is_free ? "badge-free" : "badge-pro"}`}>
                <span>{item.raw?.is_free ? "Free" : "Premium"}</span>
              </span>

              {item.raw?.content_tier && (
                <span
                  style={{
                    fontSize: "0.75rem",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "rgba(255, 255, 255, 0.06)",
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                  }}
                >
                  {item.raw.content_tier}
                </span>
              )}

              {item.raw?.duration && (
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
                  <span>{item.raw.duration}</span>
                </span>
              )}

              {item.raw?.views !== undefined && (
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
                  <span>{formatViews(item.raw.views)} views</span>
                </span>
              )}
            </>
          )}

          {item.type === "program" && item.raw?.type && (
            <span
              style={{
                fontSize: "0.75rem",
                padding: "2px 8px",
                borderRadius: "4px",
                background: "rgba(255, 255, 255, 0.06)",
                color: "var(--text-muted)",
                textTransform: "capitalize",
              }}
            >
              {item.raw.type}
            </span>
          )}

          {item.type === "researcher" && item.raw?.contact_email_verified && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "2px 8px",
                borderRadius: "4px",
                background: "rgba(16, 185, 129, 0.12)",
                color: "#34d399",
                fontSize: "0.75rem",
                fontWeight: 500,
              }}
            >
              <CheckCircle size={12} />
              <span>Verified Contact</span>
            </span>
          )}
        </div>

        {item.source_url && (
          <a
            href={item.source_url}
            target="_blank"
            rel="noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              color: "var(--text-muted)",
              fontSize: "0.78rem",
              transition: "color var(--transition-fast)",
            }}
            title="Inspect media image or external source"
          >
            <span>Preview</span>
            <ExternalLink size={12} />
          </a>
        )}
      </div>

      {/* Main Content Area (With optional thumbnail on the left for episodes) */}
      <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
        {thumbnail && (
          <Link
            to={getDetailPath()}
            style={{
              flexShrink: 0,
              width: "120px",
              height: "72px",
              borderRadius: "8px",
              overflow: "hidden",
              border: "1px solid var(--border-subtle)",
              background: "rgba(0, 0, 0, 0.4)",
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
              onError={(e) => {
                // If thumbnail fails, hide image container
                (e.target as HTMLElement).style.display = "none";
              }}
            />
          </Link>
        )}

        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Title & Subtitle */}
          <h3 style={{ fontSize: "1.18rem", fontWeight: 600, lineHeight: 1.4, marginBottom: "4px" }}>
            <Link
              to={getDetailPath()}
              style={{ color: "var(--text-primary)", transition: "color var(--transition-fast)" }}
              dangerouslySetInnerHTML={{ __html: displayTitle }}
            />
          </h3>

          {item.subtitle && (
            <div style={{ color: "var(--text-accent)", fontSize: "0.88rem", fontWeight: 500, marginBottom: "6px" }}>
              {item.subtitle}
            </div>
          )}

          {/* Snippet */}
          {displaySnippet && (
            <p
              style={{
                color: "var(--text-secondary)",
                fontSize: "0.9rem",
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

      {/* Tags / Genres / Keywords */}
      {item.tags && item.tags.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "2px" }}>
          {item.tags.slice(0, 6).map((tag, idx) => (
            <span key={idx} className="tag-topic">
              {tag}
            </span>
          ))}
          {item.tags.length > 6 && (
            <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", alignSelf: "center" }}>
              +{item.tags.length - 6} more
            </span>
          )}
        </div>
      )}
    </article>
  );
};
