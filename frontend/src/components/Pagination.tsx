import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  totalPages: number;
  totalHits: number;
  limit: number;
  onPageChange: (newPage: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  page,
  totalPages,
  totalHits,
  limit,
  onPageChange,
}) => {
  if (totalPages <= 1) return null;

  const startRecord = (page - 1) * limit + 1;
  const endRecord = Math.min(page * limit, totalHits);

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginTop: "24px",
      padding: "16px 0",
      borderTop: "1px solid var(--border-subtle)",
      flexWrap: "wrap",
      gap: "12px"
    }}>
      <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
        Showing <strong style={{ color: "var(--text-primary)" }}>{startRecord}-{endRecord}</strong> of <strong style={{ color: "var(--text-primary)" }}>{totalHits}</strong> results
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            padding: "8px 12px",
            borderRadius: "6px",
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid var(--border-subtle)",
            color: page <= 1 ? "var(--text-muted)" : "var(--text-primary)",
            cursor: page <= 1 ? "not-allowed" : "pointer"
          }}
        >
          <ChevronLeft size={16} />
          <span>Previous</span>
        </button>

        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", padding: "0 8px" }}>
          Page {page} of {totalPages}
        </span>

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            padding: "8px 12px",
            borderRadius: "6px",
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid var(--border-subtle)",
            color: page >= totalPages ? "var(--text-muted)" : "var(--text-primary)",
            cursor: page >= totalPages ? "not-allowed" : "pointer"
          }}
        >
          <span>Next</span>
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};
