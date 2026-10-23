import React from "react";
import { Link } from "react-router-dom";
import { User, BookOpen, Building2, ExternalLink, CheckCircle, AlertTriangle } from "lucide-react";
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
    }
  };

  const getIcon = () => {
    switch (item.type) {
      case "researcher":
        return <User size={14} />;
      case "publication":
        return <BookOpen size={14} />;
      case "institution":
        return <Building2 size={14} />;
    }
  };

  // Check if highlighted version is available
  const displayTitle = item.formatted?.title || item.formatted?.full_name || item.formatted?.name || item.title;
  const displaySnippet = item.formatted?.abstract || item.formatted?.biography || item.snippet;

  return (
    <article className="card-glass animate-fade-in" style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: "12px" }}>
      {/* Header Badges */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
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

          {item.type === "researcher" && item.raw?.contact_email_verified && (
            <span style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "2px 8px",
              borderRadius: "4px",
              background: "rgba(16, 185, 129, 0.12)",
              color: "#34d399",
              fontSize: "0.75rem",
              fontWeight: 500
            }}>
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
              transition: "color var(--transition-fast)"
            }}
            title="Inspect external source"
          >
            <span>Source</span>
            <ExternalLink size={12} />
          </a>
        )}
      </div>

      {/* Title & Subtitle */}
      <div>
        <h3 style={{ fontSize: "1.2rem", fontWeight: 600, lineHeight: 1.4, marginBottom: "4px" }}>
          <Link
            to={getDetailPath()}
            style={{ color: "var(--text-primary)", transition: "color var(--transition-fast)" }}
            dangerouslySetInnerHTML={{ __html: displayTitle }}
          />
        </h3>
        {item.subtitle && (
          <div style={{ color: "var(--text-accent)", fontSize: "0.88rem", fontWeight: 500 }}>
            {item.subtitle}
          </div>
        )}
      </div>

      {/* Snippet */}
      {displaySnippet && (
        <p
          style={{
            color: "var(--text-secondary)",
            fontSize: "0.9rem",
            lineHeight: "1.5",
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden"
          }}
          dangerouslySetInnerHTML={{ __html: displaySnippet }}
        />
      )}

      {/* Tags / Research Interests */}
      {item.tags && item.tags.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "4px" }}>
          {item.tags.map((tag, idx) => (
            <span key={idx} className="tag-topic">
              {tag}
            </span>
          ))}
        </div>
      )}
    </article>
  );
};
