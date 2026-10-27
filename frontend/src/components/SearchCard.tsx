import React from "react";
import { Link } from "react-router-dom";
import {
  Play,
  Tv,
  Radio,
  Clock,
  Eye,
  Users,
  Film,
  Video,
  Mic,
} from "lucide-react";
import { SearchResultItem } from "../types";
import { formatDuration, isTeaserOrClip } from "../utils/formatDuration";
import { MediaImage } from "./MediaImage";

interface SearchCardProps {
  item: SearchResultItem;
}

export const SearchCard: React.FC<SearchCardProps> = ({ item }) => {
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
  const durationText = formatDuration(item.duration_seconds, item.duration);
  const isTeaser = isEpisode && isTeaserOrClip(item.duration_seconds);

  // Helper to determine the precise content badge, label, and icon
  const getBadgeDetails = () => {
    if (isEpisode) {
      return {
        label: "Episode",
        icon: <Play size={11} fill="currentColor" />,
        className: "badge-episode",
      };
    }
    if (isChannel) {
      return {
        label: "Channel",
        icon: <Radio size={11} />,
        className: "badge-channel",
      };
    }

    const ctypeStr = (
      item.content_type ||
      item.raw?.info_content_type ||
      item.raw?.content_type ||
      ""
    ).toLowerCase();

    const ctypeList: string[] = Array.isArray(item.raw?.content_type_list)
      ? item.raw.content_type_list.map((c: string) => String(c).toLowerCase())
      : [];

    const has = (keyword: string) =>
      ctypeStr.includes(keyword) || ctypeList.some((c) => c.includes(keyword));

    if (has("movie") || has("film") || has("cinema")) {
      return {
        label: "Movie",
        icon: <Film size={11} />,
        className: "badge-movie",
      };
    }
    if (has("telefilm")) {
      return {
        label: "Telefilm",
        icon: <Film size={11} />,
        className: "badge-movie",
      };
    }
    if (has("short film") || has("shortfilm")) {
      return {
        label: "Short Film",
        icon: <Film size={11} />,
        className: "badge-movie",
      };
    }
    if (has("documentary") || has("docu")) {
      return {
        label: "Documentary",
        icon: <Video size={11} />,
        className: "badge-program",
      };
    }
    if (has("podcast")) {
      return {
        label: "Podcast",
        icon: <Mic size={11} />,
        className: "badge-podcast",
      };
    }
    if (has("talk show") || has("interview")) {
      return {
        label: "Talk Show",
        icon: <Tv size={11} />,
        className: "badge-program",
      };
    }
    if (has("drama") || has("series") || has("web series")) {
      return {
        label: "Series",
        icon: <Tv size={11} />,
        className: "badge-program",
      };
    }

    return {
      label: "Show",
      icon: <Tv size={11} />,
      className: "badge-program",
    };
  };

  const badge = getBadgeDetails();

  // Guard against duplicate cast list shown in snippet
  const isDuplicateCastSnippet =
    !isEpisode &&
    displaySnippet &&
    item.raw?.info_staring &&
    (displaySnippet.toLowerCase().includes(item.raw.info_staring.toLowerCase().slice(0, 15)) ||
      displaySnippet.toLowerCase().startsWith("starring:"));

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
          <span className={`badge ${badge.className}`}>
            {badge.icon}
            <span>{badge.label}</span>
          </span>
          {" "}

          {/* Episode Specific Badges */}
          {isEpisode && (
            <>
              {item.raw?.episode_number !== undefined && item.raw?.episode_number !== null && (
                <span
                  style={{
                    fontSize: "0.72rem",
                    padding: "2px 7px",
                    borderRadius: "4px",
                    background: "rgba(229, 9, 20, 0.2)",
                    color: "#ff8a80",
                    border: "1px solid rgba(229, 9, 20, 0.3)",
                    fontWeight: 700,
                  }}
                >
                  EP {item.raw.episode_number}
                </span>
              )}
              {" "}
              <span className={`badge ${item.is_free ? "badge-free" : "badge-pro"}`}>
                <span>{item.is_free ? "Free" : "Premium"}</span>
              </span>
              {" "}

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
              {" "}

              {durationText && (
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
                  <span>{durationText}</span>
                </span>
              )}
              {" "}

              {isTeaser && (
                <span
                  style={{
                    fontSize: "0.70rem",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    background: "rgba(245, 158, 11, 0.15)",
                    color: "#fcd34d",
                    fontWeight: 600,
                  }}
                >
                  Short Clip
                </span>
              )}
              {" "}

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
                <>
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
                  {" "}
                </>
              )}
              {item.raw?.channel_name && (
                <>
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
                  {" "}
                </>
              )}
            </>
          )}
        </div>

        {/* Channel or Parent Label */}
        {item.channel_name && !item.raw?.channel_name && (
          <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
            {item.channel_name}
          </span>
        )}
      </div>

      {/* Main Body with Media Thumbnail */}
      <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
        <Link
          to={detailPath}
          aria-label={`View ${item.title}`}
          tabIndex={-1}
          style={{
            flexShrink: 0,
            width: isEpisode ? "140px" : "110px",
            aspectRatio: isEpisode ? "16 / 9" : "3 / 4",
            borderRadius: "8px",
            overflow: "hidden",
            display: "block",
            userSelect: "none",
            transition: "transform var(--transition-fast)",
          }}
        >
          <MediaImage
            src={thumbnail}
            alt={item.title}
            type={isEpisode ? "episode" : isChannel ? "channel" : "program"}
            aspectRatio={isEpisode ? "16 / 9" : "3 / 4"}
            showPlayBadge={isEpisode}
            contentType={item.content_type || item.raw?.info_content_type}
          />
        </Link>

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
          {isEpisode && item.program_name && (
            <div style={{ color: "var(--accent-red)", fontSize: "0.85rem", fontWeight: 600, marginBottom: "6px" }}>
              {(item.content_type || "").toLowerCase().includes("movie") ? "Movie: " : "Show: "}{item.program_name}
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
          {displaySnippet && !isDuplicateCastSnippet && (
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
            <React.Fragment key={idx}>
              <span className="tag-genre">
                {tag}
              </span>
              {" "}
            </React.Fragment>
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
