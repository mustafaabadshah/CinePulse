import React from "react";
import { Filter, X, Check } from "lucide-react";

interface FilterSidebarProps {
  facets: Record<string, Record<string, number>>;
  activeFilters: Record<string, any>;
  onFilterChange: (key: string, value: any) => void;
  onClearFilters: () => void;
}

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  facets,
  activeFilters,
  onFilterChange,
  onClearFilters,
}) => {
  const activeCount = Object.keys(activeFilters).filter(
    (k) => activeFilters[k] !== undefined && activeFilters[k] !== ""
  ).length;

  // Media catalog facet groups
  const facetGroups = [
    { key: "is_free", label: "Access Tier" },
    { key: "content_tier", label: "Content Tier" },
    { key: "channel_name", label: "Channels & Networks" },
    { key: "genre", label: "Genres" },
    { key: "language", label: "Languages" },
    { key: "region", label: "Distribution Regions" },
    { key: "is_vertical", label: "Video Format" },
  ];

  const formatFacetValue = (groupKey: string, val: string) => {
    if (groupKey === "is_free") {
      return val === "true" || val === "1" ? "Free to Watch" : "Premium";
    }
    if (groupKey === "is_vertical" && (val === "mini" || val === "true" || val === "1")) {
      return "Vertical / Shorts";
    }
    if (groupKey === "content_tier") {
      return val.toUpperCase();
    }
    return val;
  };

  return (
    <aside
      style={{
        width: "280px",
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          paddingBottom: "12px",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.95rem" }}>
          <Filter size={18} color="var(--accent-red)" />
          <span>Catalog Filters</span>
          {activeCount > 0 && (
            <span
              style={{
                background: "var(--accent-red)",
                color: "#fff",
                fontSize: "0.72rem",
                padding: "1px 6px",
                borderRadius: "10px",
                fontWeight: 700,
              }}
            >
              {activeCount}
            </span>
          )}
        </div>

        {activeCount > 0 && (
          <button
            onClick={onClearFilters}
            style={{
              color: "var(--text-muted)",
              fontSize: "0.8rem",
              display: "flex",
              alignItems: "center",
              gap: "4px",
              background: "transparent",
              border: "none",
              cursor: "pointer",
            }}
          >
            <X size={14} />
            <span>Reset</span>
          </button>
        )}
      </div>

      {/* Active Filter Chips */}
      {activeCount > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
          {Object.entries(activeFilters).map(([k, v]) => {
            if (v === undefined || v === "") return null;
            return (
              <span
                key={k}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "3px 10px",
                  borderRadius: "20px",
                  background: "rgba(229, 9, 20, 0.15)",
                  border: "1px solid rgba(229, 9, 20, 0.35)",
                  color: "#fca5a5",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                }}
              >
                <span>{k}: {String(v)}</span>
                <X
                  size={12}
                  style={{ cursor: "pointer" }}
                  onClick={() => onFilterChange(k, undefined)}
                />
              </span>
            );
          })}
        </div>
      )}

      {/* Facet Groups */}
      <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
        {facetGroups.map((group) => {
          const distribution = facets[group.key];
          if (!distribution || Object.keys(distribution).length === 0) {
            return null;
          }

          // Sort values by count descending
          const sortedEntries = Object.entries(distribution)
            .filter(([val]) => val && val.trim() !== "")
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8); // Top 8 values

          if (sortedEntries.length === 0) return null;

          return (
            <div
              key={group.key}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "8px",
              }}
            >
              <div
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "var(--text-muted)",
                }}
              >
                {group.label}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {sortedEntries.map(([value, count]) => {
                  const isChecked = String(activeFilters[group.key]) === String(value);

                  return (
                    <label
                      key={value}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "5px 8px",
                        borderRadius: "6px",
                        fontSize: "0.84rem",
                        color: isChecked ? "#ffffff" : "var(--text-secondary)",
                        background: isChecked ? "rgba(229, 9, 20, 0.12)" : "transparent",
                        cursor: "pointer",
                        transition: "all var(--transition-fast)",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
                        <div
                          style={{
                            width: "15px",
                            height: "15px",
                            borderRadius: "3px",
                            border: isChecked
                              ? "1px solid var(--accent-red)"
                              : "1px solid var(--border-card)",
                            background: isChecked ? "var(--accent-red)" : "transparent",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            flexShrink: 0,
                          }}
                        >
                          {isChecked && <Check size={11} color="#ffffff" />}
                        </div>
                        <span
                          style={{
                            whiteSpace: "nowrap",
                            textOverflow: "ellipsis",
                            overflow: "hidden",
                          }}
                        >
                          {formatFacetValue(group.key, value)}
                        </span>
                      </div>
                      <span
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--text-muted)",
                          marginLeft: "6px",
                        }}
                      >
                        {count.toLocaleString()}
                      </span>
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {
                          if (isChecked) {
                            onFilterChange(group.key, undefined);
                          } else {
                            onFilterChange(group.key, value);
                          }
                        }}
                        style={{ display: "none" }}
                      />
                    </label>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
};
