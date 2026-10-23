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
  const activeCount = Object.keys(activeFilters).filter((k) => activeFilters[k] !== undefined && activeFilters[k] !== "").length;

  const facetGroups = [
    { key: "country", label: "Countries" },
    { key: "institution_name", label: "Institutions" },
    { key: "research_interests", label: "Research Interests" },
    { key: "keywords", label: "Paper Topics" },
    { key: "publication_year", label: "Publication Year" },
  ];

  return (
    <aside style={{
      width: "280px",
      flexShrink: 0,
      display: "flex",
      flexDirection: "column",
      gap: "20px",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        paddingBottom: "12px",
        borderBottom: "1px solid var(--border-subtle)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 600 }}>
          <Filter size={18} color="var(--accent-blue)" />
          <span>Filters</span>
          {activeCount > 0 && (
            <span style={{
              background: "var(--accent-blue)",
              color: "#fff",
              fontSize: "0.75rem",
              padding: "1px 6px",
              borderRadius: "10px"
            }}>
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
              gap: "4px"
            }}
          >
            <X size={14} />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Facet Groups */}
      {facetGroups.map((group) => {
        const groupFacets = facets[group.key];
        if (!groupFacets || Object.keys(groupFacets).length === 0) return null;

        const sortedEntries = Object.entries(groupFacets).sort((a, b) => b[1] - a[1]);

        return (
          <div key={group.key} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <h4 style={{
              fontSize: "0.8rem",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-muted)",
              fontWeight: 600
            }}>
              {group.label}
            </h4>

            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {sortedEntries.slice(0, 7).map(([val, count]) => {
                const isSelected = String(activeFilters[group.key]) === String(val);

                return (
                  <button
                    key={val}
                    onClick={() => {
                      if (isSelected) {
                        onFilterChange(group.key, undefined);
                      } else {
                        onFilterChange(group.key, val);
                      }
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "6px 10px",
                      borderRadius: "6px",
                      fontSize: "0.85rem",
                      textAlign: "left",
                      background: isSelected ? "rgba(59, 130, 246, 0.2)" : "transparent",
                      color: isSelected ? "#93c5fd" : "var(--text-secondary)",
                      border: isSelected ? "1px solid rgba(59, 130, 246, 0.4)" : "1px solid transparent",
                      transition: "all var(--transition-fast)"
                    }}
                  >
                    <span style={{
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      maxWidth: "180px",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px"
                    }}>
                      {isSelected && <Check size={13} color="#60a5fa" />}
                      <span>{val}</span>
                    </span>
                    <span style={{
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                      background: "rgba(255, 255, 255, 0.05)",
                      padding: "1px 6px",
                      borderRadius: "4px"
                    }}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </aside>
  );
};
