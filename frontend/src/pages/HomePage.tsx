import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Search,
  Sparkles,
  Play,
  Tv,
  Radio,
  Eye,
  ArrowRight,
  TrendingUp,
  Flame,
} from "lucide-react";
import { search } from "../api/client";
import { SearchResultItem } from "../types";
import { formatDuration } from "../utils/formatDuration";
import { MediaImage, resolveImageUrl } from "../components/MediaImage";

export const HomePage: React.FC = () => {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  // Shelf data states
  const [spotlight, setSpotlight] = useState<SearchResultItem | null>(null);
  const [popularEpisodes, setPopularEpisodes] = useState<SearchResultItem[]>([]);
  const [featuredPrograms, setFeaturedPrograms] = useState<SearchResultItem[]>([]);
  const [channels, setChannels] = useState<SearchResultItem[]>([]);
  const [freeEpisodes, setFreeEpisodes] = useState<SearchResultItem[]>([]);

  useEffect(() => {
    let isMounted = true;
    async function loadCatalog() {
      try {
        // Fetch popular episodes by view count
        const popRes = await search({
          type: "episodes",
          sort: "views:desc",
          limit: 12,
        });

        // Fetch top programs
        const progRes = await search({
          type: "programs",
          limit: 10,
        });

        // Fetch live channels
        const chanRes = await search({
          type: "channels",
          limit: 10,
        });

        // Fetch free episodes
        const freeRes = await search({
          type: "episodes",
          is_free: true,
          sort: "views:desc",
          limit: 10,
        });

        if (isMounted) {
          if (popRes.hits && popRes.hits.length > 0) {
            // Find a spotlight item that has a valid thumbnail
            const hero = popRes.hits.find((h) => h.thumbnail) || popRes.hits[0];
            setSpotlight(hero);
            setPopularEpisodes(popRes.hits);
          }
          if (progRes.hits) setFeaturedPrograms(progRes.hits);
          if (chanRes.hits) setChannels(chanRes.hits);
          if (freeRes.hits) setFreeEpisodes(freeRes.hits);
        }
      } catch (err) {
        console.error("Failed to load catalog shelves:", err);
      }
    }

    loadCatalog();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    } else {
      navigate("/search");
    }
  };

  const formatViews = (views?: number) => {
    if (!views && views !== 0) return "0";
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toLocaleString();
  };

  const genrePills = [
    { label: "Drama", query: "Drama" },
    { label: "News", query: "News" },
    { label: "Automotive", query: "Automotive" },
    { label: "Comedy", query: "Comedy" },
    { label: "Reality Show", query: "Reality Show" },
    { label: "Sports", query: "Sports" },
    { label: "Crime", query: "Crime" },
    { label: "Talk Show", query: "Talk Show" },
  ];

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "24px 24px 60px" }}>
      {/* Search Header Bar */}
      <section style={{ maxWidth: "840px", margin: "0 auto 36px" }}>
        <form onSubmit={handleSearch} style={{ position: "relative" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              background: "var(--bg-surface)",
              border: "1px solid var(--border-card)",
              borderRadius: "14px",
              padding: "8px 12px 8px 20px",
              boxShadow: "var(--shadow-md)",
              transition: "all var(--transition-normal)",
            }}
          >
            <Search size={22} color="var(--accent-red)" style={{ marginRight: "12px", flexShrink: 0 }} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search shows, channels, episodes, actors, or genres (e.g. Ehd E Wafa, PakWheels, Hum News, Ahad)..."
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                color: "var(--text-primary)",
                fontSize: "1.05rem",
                outline: "none",
              }}
            />
            <button
              type="submit"
              className="btn-primary"
              style={{ padding: "10px 22px", borderRadius: "10px", flexShrink: 0 }}
            >
              <span>Explore</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </form>

        {/* Quick Genre Pills */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            marginTop: "16px",
          }}
        >
          {genrePills.map((pill) => (
            <button
              key={pill.label}
              onClick={() => navigate(`/search?genre=${encodeURIComponent(pill.query)}`)}
              className="tag-genre"
              style={{ cursor: "pointer", fontSize: "0.82rem", padding: "4px 12px" }}
            >
              {pill.label}
            </button>
          ))}
        </div>
      </section>

      {/* Cinematic Spotlight Hero */}
      {spotlight && (
        <section
          style={{
            position: "relative",
            borderRadius: "18px",
            overflow: "hidden",
            marginBottom: "48px",
            background: "linear-gradient(180deg, #181d28 0%, #0e121a 100%)",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            boxShadow: "var(--shadow-lg)",
            minHeight: "380px",
            display: "flex",
            alignItems: "flex-end",
          }}
        >
          {/* Background Poster Artwork */}
          {spotlight.thumbnail && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                backgroundImage: `url(${resolveImageUrl(spotlight.thumbnail)})`,
                backgroundSize: "cover",
                backgroundPosition: "center 20%",
                filter: "brightness(0.38) blur(1px)",
                transform: "scale(1.02)",
              }}
            />
          )}

          {/* Gradient Overlay for Readability */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "linear-gradient(90deg, rgba(8,10,15,0.96) 0%, rgba(8,10,15,0.8) 50%, rgba(8,10,15,0.2) 100%)",
            }}
          />

          {/* Hero Content */}
          <div
            style={{
              position: "relative",
              zIndex: 2,
              padding: "40px",
              maxWidth: "760px",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "5px",
                  background: "var(--accent-red)",
                  color: "#ffffff",
                  fontSize: "0.75rem",
                  fontWeight: 800,
                  textTransform: "uppercase",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  letterSpacing: "0.06em",
                }}
              >
                <Flame size={13} fill="#ffffff" />
                <span>Featured Content</span>
              </span>

              <span className={`badge ${spotlight.is_free ? "badge-free" : "badge-pro"}`}>
                <span>{spotlight.is_free ? "Free to Watch" : "Premium"}</span>
              </span>

              {spotlight.views !== undefined && (
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    color: "var(--text-secondary)",
                    fontSize: "0.82rem",
                    fontWeight: 600,
                  }}
                >
                  <Eye size={13} color="var(--accent-gold)" />
                  <span>{formatViews(spotlight.views)} views</span>
                </span>
              )}
            </div>

            <h1
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "2.5rem",
                fontWeight: 800,
                lineHeight: 1.2,
                color: "#ffffff",
                letterSpacing: "-0.02em",
              }}
            >
              {spotlight.title}
            </h1>

            {spotlight.program_name && (
              <div style={{ color: "var(--accent-red)", fontSize: "1.1rem", fontWeight: 700 }}>
                Series: {spotlight.program_name}
              </div>
            )}

            {spotlight.snippet && (
              <p
                style={{
                  color: "var(--text-secondary)",
                  fontSize: "0.95rem",
                  lineHeight: 1.6,
                  display: "-webkit-box",
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                }}
              >
                {spotlight.snippet}
              </p>
            )}

            <div style={{ display: "flex", gap: "14px", marginTop: "10px", flexWrap: "wrap" }}>
              <Link
                to={`/episodes/${encodeURIComponent(spotlight.id)}`}
                className="btn-primary"
                style={{ padding: "12px 28px", fontSize: "0.95rem" }}
              >
                <Play size={18} fill="#ffffff" />
                <span>View Episode Details</span>
              </Link>

              {spotlight.raw?.program_id && (
                <Link
                  to={`/programs/${encodeURIComponent(spotlight.raw.program_id)}`}
                  className="btn-secondary"
                  style={{ padding: "12px 24px", fontSize: "0.95rem" }}
                >
                  <Tv size={18} />
                  <span>Explore Series</span>
                </Link>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Shelf 1: Popular Content by Views */}
      <section className="shelf-section">
        <div className="shelf-header">
          <div className="shelf-title">
            <span>Popular by Views</span>
            <TrendingUp size={18} color="var(--accent-gold)" />
          </div>
          <Link
            to="/search?type=episodes&sort=views:desc"
            style={{
              fontSize: "0.85rem",
              color: "var(--accent-red)",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>See all</span>
            <ArrowRight size={14} />
          </Link>
        </div>

        <div className="shelf-scroll">
          {popularEpisodes.map((item) => {
            const dur = formatDuration(item.duration_seconds, item.duration);
            return (
              <div key={item.id} className="shelf-item">
                <Link to={`/episodes/${encodeURIComponent(item.id)}`} className="media-card" style={{ height: "100%" }}>
                  <div className="media-card-thumb" style={{ position: "relative" }}>
                    <MediaImage
                      src={item.thumbnail}
                      alt={item.title}
                      type="episode"
                      aspectRatio="16 / 9"
                      showPlayBadge={true}
                    />
                    {/* View count pill */}
                    {item.views !== undefined && (
                      <div
                        style={{
                          position: "absolute",
                          bottom: "8px",
                          right: "8px",
                          background: "rgba(0, 0, 0, 0.75)",
                          padding: "2px 7px",
                          borderRadius: "4px",
                          fontSize: "0.72rem",
                          color: "#ffffff",
                          fontWeight: 600,
                          zIndex: 2,
                        }}
                      >
                        {formatViews(item.views)} views
                      </div>
                    )}
                  </div>

                  <div style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px" }}>
                      <span className={`badge ${item.is_free ? "badge-free" : "badge-pro"}`}>
                        <span>{item.is_free ? "Free" : "Pro"}</span>
                      </span>
                      {dur && (
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{dur}</span>
                      )}
                    </div>

                    <h4
                      style={{
                        fontSize: "0.95rem",
                        fontWeight: 700,
                        color: "#ffffff",
                        lineHeight: 1.35,
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {item.title}
                    </h4>

                    {item.program_name && (
                      <div style={{ fontSize: "0.8rem", color: "var(--accent-red)", fontWeight: 600 }}>
                        {item.program_name}
                      </div>
                    )}
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* Shelf 2: Shows & Dramas */}
      <section className="shelf-section">
        <div className="shelf-header">
          <div className="shelf-title">
            <span>Shows & Dramas</span>
            <Tv size={18} color="var(--accent-sky)" />
          </div>
          <Link
            to="/search?type=programs"
            style={{
              fontSize: "0.85rem",
              color: "var(--accent-red)",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>Browse Shows</span>
            <ArrowRight size={14} />
          </Link>
        </div>

        <div className="shelf-scroll">
          {featuredPrograms.map((item) => (
            <div key={item.id} className="shelf-item narrow">
              <Link to={`/programs/${encodeURIComponent(item.id)}`} className="media-card" style={{ height: "100%" }}>
                <div
                  style={{
                    padding: "20px 16px",
                    background: "linear-gradient(180deg, #1a2233 0%, #101522 100%)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px",
                    minHeight: "170px",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                      <span className="badge badge-program">Show</span>
                      {item.raw?.channel_name && (
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                          {item.raw.channel_name}
                        </span>
                      )}
                    </div>
                    <h4 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", lineHeight: 1.3 }}>
                      {item.title}
                    </h4>
                  </div>

                  {item.raw?.info_genre && (
                    <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                      Genre: {item.raw.info_genre}
                    </div>
                  )}
                </div>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Shelf 3: Live Channels & Networks */}
      <section className="shelf-section">
        <div className="shelf-header">
          <div className="shelf-title">
            <span>Live Channels & Networks</span>
            <Radio size={18} color="#c084fc" />
          </div>
          <Link
            to="/search?type=channels"
            style={{
              fontSize: "0.85rem",
              color: "var(--accent-red)",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>Browse Channels</span>
            <ArrowRight size={14} />
          </Link>
        </div>

        <div className="shelf-scroll">
          {channels.map((item) => (
            <div key={item.id} className="shelf-item narrow">
              <Link to={`/programs/${encodeURIComponent(item.id)}`} className="media-card" style={{ height: "100%" }}>
                <div
                  style={{
                    padding: "20px 16px",
                    background: "linear-gradient(180deg, #23192f 0%, #120e1a 100%)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px",
                    minHeight: "170px",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                      <span className="badge badge-channel">Live Channel</span>
                      <span className="badge badge-live">LIVE</span>
                    </div>
                    <h4 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", lineHeight: 1.3 }}>
                      {item.title}
                    </h4>
                  </div>

                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    {item.raw?.channel_name || "Broadcast Network"}
                  </div>
                </div>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Shelf 4: Free to Watch Content */}
      <section className="shelf-section">
        <div className="shelf-header">
          <div className="shelf-title">
            <span>Free to Watch</span>
            <Sparkles size={18} color="var(--accent-emerald)" />
          </div>
          <Link
            to="/search?type=episodes&is_free=true"
            style={{
              fontSize: "0.85rem",
              color: "var(--accent-red)",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>See Free Catalog</span>
            <ArrowRight size={14} />
          </Link>
        </div>

        <div className="shelf-scroll">
          {freeEpisodes.map((item) => {
            const dur = formatDuration(item.duration_seconds, item.duration);
            return (
              <div key={item.id} className="shelf-item">
                <Link to={`/episodes/${encodeURIComponent(item.id)}`} className="media-card" style={{ height: "100%" }}>
                  <div className="media-card-thumb">
                    <MediaImage
                      src={item.thumbnail}
                      alt={item.title}
                      type="episode"
                      aspectRatio="16 / 9"
                      showPlayBadge={true}
                    />
                  </div>

                  <div style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px" }}>
                      <span className="badge badge-free">Free</span>
                      {dur && (
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{dur}</span>
                      )}
                    </div>

                    <h4
                      style={{
                        fontSize: "0.95rem",
                        fontWeight: 700,
                        color: "#ffffff",
                        lineHeight: 1.35,
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {item.title}
                    </h4>
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};
