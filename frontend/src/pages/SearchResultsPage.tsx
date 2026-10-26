import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, X, SlidersHorizontal, RefreshCw, AlertCircle, Film } from "lucide-react";
import { search } from "../api/client";
import { SearchResponse } from "../types";
import { SearchCard } from "../components/SearchCard";
import { FilterSidebar } from "../components/FilterSidebar";
import { Pagination } from "../components/Pagination";
import { SkeletonCard } from "../components/SkeletonLoader";

export const SearchResultsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get("q") || "";
  const initialType = (searchParams.get("type") as any) || "all";

  const [inputVal, setInputVal] = useState(initialQuery);
  const [activeType, setActiveType] = useState<"all" | "episodes" | "programs" | "channels">(initialType);
  const [sortOrder, setSortOrder] = useState<string>(() => {
    return searchParams.get("sort") || (searchParams.get("program_id") ? "episode_number:asc" : "");
  });
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(12);

  // Extract initial filters from search params
  const [filters, setFilters] = useState<Record<string, any>>(() => {
    const f: Record<string, any> = {};
    if (searchParams.get("genre")) f.genre = searchParams.get("genre");
    if (searchParams.get("channel_name")) f.channel_name = searchParams.get("channel_name");
    if (searchParams.get("is_free")) f.is_free = searchParams.get("is_free") === "true";
    if (searchParams.get("content_tier")) f.content_tier = searchParams.get("content_tier");
    if (searchParams.get("program_id")) f.program_id = searchParams.get("program_id");
    return f;
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);

  // Sync external URL changes
  useEffect(() => {
    const q = searchParams.get("q") || "";
    if (q !== inputVal) {
      setInputVal(q);
    }
    const t = (searchParams.get("type") as any) || "all";
    if (t !== activeType) {
      setActiveType(t);
    }
    const pid = searchParams.get("program_id");
    if (pid) {
      setFilters((prev) => ({ ...prev, program_id: pid }));
    }
  }, [searchParams]);

  // Execute Search
  const doSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = (page - 1) * limit;
      const resp = await search({
        q: inputVal,
        type: activeType,
        limit,
        offset,
        sort: sortOrder || undefined,
        ...filters,
      });
      setResults(resp);
    } catch (err: any) {
      setError(err.message || "Failed to retrieve search results.");
    } finally {
      setLoading(false);
    }
  }, [inputVal, activeType, page, limit, sortOrder, filters]);

  // Debounced search-as-you-type
  useEffect(() => {
    const timer = setTimeout(() => {
      const params = new URLSearchParams(searchParams);
      if (inputVal.trim()) {
        params.set("q", inputVal.trim());
      } else {
        params.delete("q");
      }
      if (activeType !== "all") {
        params.set("type", activeType);
      } else {
        params.delete("type");
      }
      setSearchParams(params, { replace: true });

      doSearch();
    }, 280);

    return () => clearTimeout(timer);
  }, [inputVal, activeType, page, sortOrder, filters, doSearch]);

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === undefined || value === "") {
        delete next[key];
      } else {
        next[key] = value;
      }
      return next;
    });
    setPage(1);
  };

  const handleClearFilters = () => {
    setFilters({});
    setPage(1);
    const params = new URLSearchParams(searchParams);
    ["genre", "channel_name", "is_free", "content_tier", "program_id"].forEach((k) => params.delete(k));
    setSearchParams(params, { replace: true });
  };

  const mediaTabs = [
    { id: "all", label: "All Media" },
    { id: "episodes", label: "Episodes" },
    { id: "programs", label: "Shows" },
    { id: "channels", label: "Live Channels" },
  ];

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "32px 24px" }}>
      {/* Search Header Bar */}
      <div style={{ marginBottom: "28px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            background: "var(--bg-surface)",
            border: "1px solid var(--border-card)",
            borderRadius: "12px",
            padding: "6px 18px",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <Search size={20} color="var(--accent-red)" style={{ marginRight: "12px", flexShrink: 0 }} />
          <input
            type="text"
            value={inputVal}
            onChange={(e) => {
              setInputVal(e.target.value);
              setPage(1);
            }}
            placeholder="Search shows, channels, episodes, cast, genres (e.g. Ehd E Wafa, PakWheels, Hum News, Ahad)..."
            style={{
              width: "100%",
              background: "transparent",
              border: "none",
              color: "var(--text-primary)",
              fontSize: "1.05rem",
              padding: "8px 0",
              outline: "none",
            }}
          />
          {inputVal && (
            <button
              onClick={() => {
                setInputVal("");
                setPage(1);
              }}
              style={{
                color: "var(--text-muted)",
                padding: "4px",
                background: "transparent",
                border: "none",
                cursor: "pointer",
              }}
              title="Clear search query"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Media Tabs & Sort Options */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
            marginTop: "16px",
            borderBottom: "1px solid var(--border-subtle)",
            paddingBottom: "10px",
          }}
        >
          {/* Tabs */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {mediaTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveType(tab.id as any);
                  setPage(1);
                }}
                style={{
                  padding: "8px 18px",
                  borderRadius: "8px",
                  fontSize: "0.88rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  color: activeType === tab.id ? "#ffffff" : "var(--text-secondary)",
                  background: activeType === tab.id ? "rgba(229, 9, 20, 0.2)" : "transparent",
                  border: activeType === tab.id ? "1px solid rgba(229, 9, 20, 0.4)" : "1px solid transparent",
                  transition: "all var(--transition-fast)",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Sort Dropdown */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <SlidersHorizontal size={14} color="var(--text-muted)" />
            <select
              value={sortOrder}
              onChange={(e) => {
                setSortOrder(e.target.value);
                setPage(1);
              }}
              style={{
                background: "var(--bg-surface)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                padding: "6px 12px",
                fontSize: "0.85rem",
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="">Relevance</option>
              {(activeType === "episodes" || activeType === "all") && (
                <>
                  <option value="episode_number:asc">Episode Sequence (Ep 1, 2...)</option>
                  <option value="views:desc">Most Viewed</option>
                  <option value="duration_seconds:desc">Longest Duration</option>
                  <option value="duration_seconds:asc">Shortest Duration</option>
                  <option value="title:asc">Title (A-Z)</option>
                </>
              )}
              {activeType === "programs" && (
                <>
                  <option value="name:asc">Name (A-Z)</option>
                </>
              )}
            </select>
          </div>
        </div>
      </div>

      {/* Main Content Layout (Sidebar + Results) */}
      <div style={{ display: "flex", gap: "32px", alignItems: "flex-start" }}>
        {/* Filter Sidebar */}
        <FilterSidebar
          facets={results?.facet_distribution || {}}
          activeFilters={filters}
          onFilterChange={handleFilterChange}
          onClearFilters={handleClearFilters}
        />

        {/* Results Stream */}
        <main style={{ flex: 1, minWidth: 0 }}>
          {/* Status Bar */}
          {results && !loading && (
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "16px",
                fontSize: "0.85rem",
                color: "var(--text-muted)",
              }}
            >
              <div>
                Found <strong style={{ color: "var(--text-primary)" }}>{results.total_hits.toLocaleString()}</strong> catalog items
                {results.query && <span> matching &ldquo;{results.query}&rdquo;</span>}
              </div>
              <div>
                Engine Latency: <span style={{ color: "#34d399", fontWeight: 600 }}>{results.processing_time_ms}ms</span>
              </div>
            </div>
          )}

          {/* Loading Skeletons */}
          {loading && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          )}

          {/* Retryable Error State */}
          {!loading && error && (
            <div
              className="card-glass"
              style={{
                padding: "40px",
                textAlign: "center",
                border: "1px solid rgba(229, 9, 20, 0.4)",
              }}
            >
              <AlertCircle size={40} color="var(--accent-red)" style={{ margin: "0 auto 12px" }} />
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#f87171", marginBottom: "8px" }}>
                Search Request Failed
              </h3>
              <p style={{ color: "var(--text-secondary)", marginBottom: "20px" }}>{error}</p>
              <button onClick={doSearch} className="btn-secondary" style={{ gap: "6px" }}>
                <RefreshCw size={16} />
                <span>Retry Search</span>
              </button>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && results && results.hits.length === 0 && (
            <div className="card-glass" style={{ padding: "48px 24px", textAlign: "center" }}>
              <Film size={44} color="var(--text-muted)" style={{ margin: "0 auto 16px", opacity: 0.5 }} />
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "8px" }}>No media records found</h3>
              <p style={{ color: "var(--text-secondary)", maxWidth: "420px", margin: "0 auto 20px" }}>
                We couldn&apos;t find any shows, channels, or episodes matching your query. Try searching by cast name, show title, or clearing active filters.
              </p>
              {Object.keys(filters).length > 0 && (
                <button onClick={handleClearFilters} className="btn-secondary">
                  Clear Active Filters
                </button>
              )}
            </div>
          )}

          {/* Result Cards List */}
          {!loading && !error && results && results.hits.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {results.hits.map((item) => (
                <SearchCard key={`${item.type}_${item.id}`} item={item} />
              ))}

              <Pagination
                page={page}
                totalPages={results.total_pages}
                totalHits={results.total_hits}
                limit={limit}
                onPageChange={(p) => setPage(p)}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
