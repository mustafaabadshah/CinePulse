import React from "react";

export const SkeletonCard: React.FC = () => {
  return (
    <div className="card-glass" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "14px" }}>
      <div style={{ display: "flex", gap: "10px" }}>
        <div className="skeleton" style={{ width: "80px", height: "22px" }} />
        <div className="skeleton" style={{ width: "60px", height: "22px" }} />
      </div>
      <div className="skeleton" style={{ width: "70%", height: "26px" }} />
      <div className="skeleton" style={{ width: "40%", height: "16px" }} />
      <div className="skeleton" style={{ width: "100%", height: "48px" }} />
      <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
        <div className="skeleton" style={{ width: "90px", height: "20px" }} />
        <div className="skeleton" style={{ width: "110px", height: "20px" }} />
        <div className="skeleton" style={{ width: "80px", height: "20px" }} />
      </div>
    </div>
  );
};
