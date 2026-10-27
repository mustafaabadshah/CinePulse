import React, { useState, useMemo } from "react";
import { Tv, Radio, Film, Play } from "lucide-react";

const TAMASHA_S3_BASE_URL = "https://tamasha-app-images.s3.amazonaws.com/jazzlive/";

/**
 * Normalizes relative or legacy image URLs to active Tamasha S3 CDN URLs.
 */
export function resolveImageUrl(url?: string | null): string | null {
  if (!url || typeof url !== "string") return null;
  const trimmed = url.trim();
  if (!trimmed || ["nothumbnail", "no_thumbnail", "no-thumbnail", "null", "none"].includes(trimmed.toLowerCase())) {
    return null;
  }

  if (trimmed.startsWith("uploads/")) {
    return `${TAMASHA_S3_BASE_URL}${trimmed}`;
  }
  if (trimmed.startsWith("/uploads/")) {
    return `${TAMASHA_S3_BASE_URL}${trimmed.replace(/^\/+/, "")}`;
  }
  if (trimmed.includes("srv2.jazztv.pk/jazzlive/")) {
    return trimmed.replace(
      /https?:\/\/srv2\.jazztv\.pk\/jazzlive\//,
      TAMASHA_S3_BASE_URL
    );
  }
  return trimmed;
}

export interface MediaImageProps {
  src?: string | null;
  alt: string;
  type?: "episode" | "program" | "channel" | "generic";
  aspectRatio?: string; // e.g. "16 / 9", "3 / 4", "1 / 1"
  className?: string;
  style?: React.CSSProperties;
  loading?: "lazy" | "eager";
  title?: string;
  subtitle?: string;
  showPlayBadge?: boolean;
  contentType?: string;
}

export const MediaImage: React.FC<MediaImageProps> = ({
  src,
  alt,
  type = "generic",
  aspectRatio = "16 / 9",
  className = "",
  style,
  loading = "lazy",
  title,
  subtitle,
  showPlayBadge = false,
  contentType,
}) => {
  const [hasError, setHasError] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  const resolvedSrc = useMemo(() => resolveImageUrl(src), [src]);

  // If no source or error occurred, render designed media fallback
  if (!resolvedSrc || hasError) {
    const isChannel = type === "channel";
    const isProgram = type === "program";

    return (
      <div
        className={`media-placeholder-container ${className}`}
        style={{
          width: "100%",
          height: "100%",
          aspectRatio,
          position: "relative",
          overflow: "hidden",
          borderRadius: "inherit",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "12px",
          background: isChannel
            ? "linear-gradient(135deg, #1e1b4b 0%, #09090b 100%)"
            : isProgram
            ? "linear-gradient(135deg, #1e293b 0%, #080a0f 100%)"
            : "linear-gradient(135deg, #181d28 0%, #0b0d13 100%)",
          border: "1px solid var(--border-subtle)",
          ...style,
        }}
        role="img"
        aria-label={alt}
      >
        {/* Subtle decorative background watermark */}
        <div
          style={{
            position: "absolute",
            right: "-10px",
            bottom: "-10px",
            opacity: 0.08,
            pointerEvents: "none",
          }}
        >
          {isChannel ? (
            <Radio size={84} />
          ) : isProgram ? (
            <Tv size={84} />
          ) : (
            <Film size={84} />
          )}
        </div>

        {/* Top Header Badge (Decorative placeholder artwork) */}
        <div
          aria-hidden="true"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            zIndex: 1,
            userSelect: "none",
          }}
        >
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "2px 6px",
              borderRadius: "4px",
              fontSize: "0.68rem",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              background: isChannel
                ? "rgba(168, 85, 247, 0.25)"
                : isProgram
                ? "rgba(59, 130, 246, 0.25)"
                : "rgba(229, 9, 20, 0.25)",
              color: isChannel ? "#c084fc" : isProgram ? "#93c5fd" : "#fca5a5",
              userSelect: "none",
            }}
          >
            {isChannel ? (
              <>
                <Radio size={10} />
                <span>Live Channel</span>
              </>
            ) : isProgram ? (
              contentType?.toLowerCase().includes("movie") ? (
                <>
                  <Film size={10} />
                  <span>Movie</span>
                </>
              ) : contentType?.toLowerCase().includes("telefilm") ? (
                <>
                  <Film size={10} />
                  <span>Telefilm</span>
                </>
              ) : contentType?.toLowerCase().includes("podcast") ? (
                <>
                  <Radio size={10} />
                  <span>Podcast</span>
                </>
              ) : (
                <>
                  <Tv size={10} />
                  <span>Show</span>
                </>
              )
            ) : (
              <>
                <Film size={10} />
                <span>Episode</span>
              </>
            )}
          </span>
        </div>

        {/* Center Visual Icon */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flex: 1,
            zIndex: 1,
            color: "var(--text-muted)",
          }}
        >
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "50%",
              background: "rgba(255, 255, 255, 0.05)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "1px solid rgba(255, 255, 255, 0.08)",
            }}
          >
            {isChannel ? (
              <Radio size={18} color="#c084fc" />
            ) : isProgram ? (
              <Tv size={18} color="#93c5fd" />
            ) : (
              <Play size={16} fill="var(--accent-red)" color="var(--accent-red)" style={{ marginLeft: "2px" }} />
            )}
          </div>
        </div>

        {/* Bottom Title Label */}
        {(title || subtitle) && (
          <div style={{ zIndex: 1, minWidth: 0 }}>
            {title && (
              <div
                style={{
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  color: "#ffffff",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  lineHeight: 1.2,
                }}
              >
                {title}
              </div>
            )}
            {subtitle && (
              <div
                style={{
                  fontSize: "0.68rem",
                  color: "var(--text-muted)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  marginTop: "2px",
                }}
              >
                {subtitle}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className={`media-image-wrapper ${className}`}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        aspectRatio,
        overflow: "hidden",
        borderRadius: "inherit",
        backgroundColor: "#080a0f",
        ...style,
      }}
    >
      {/* Loading Shimmer Skeleton */}
      {!isLoaded && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "linear-gradient(90deg, #141923 25%, #1e2535 50%, #141923 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.8s infinite linear",
            zIndex: 1,
          }}
        />
      )}

      {/* Actual Media Image */}
      <img
        src={resolvedSrc}
        alt={alt}
        loading={loading}
        onLoad={() => setIsLoaded(true)}
        onError={() => {
          setHasError(true);
          setIsLoaded(true);
        }}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          display: "block",
          opacity: isLoaded ? 1 : 0,
          transition: "opacity 0.3s ease-in-out, transform 0.3s ease",
        }}
      />

      {/* Optional Play Button Overlay for Episodes */}
      {showPlayBadge && isLoaded && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(0, 0, 0, 0.25)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              background: "var(--accent-red)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 2px 10px rgba(0,0,0,0.6)",
            }}
          >
            <Play size={14} fill="#ffffff" color="#ffffff" style={{ marginLeft: "2px" }} />
          </div>
        </div>
      )}
    </div>
  );
};
