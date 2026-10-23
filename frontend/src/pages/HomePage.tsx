import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Sparkles, BookOpen, User, Building2, ArrowRight } from "lucide-react";

export const HomePage: React.FC = () => {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    } else {
      navigate("/search");
    }
  };

  const topicPills = [
    { label: "Generative AI", query: "Generative AI" },
    { label: "Computer Vision", query: "Computer Vision" },
    { label: "Agentic AI", query: "Agentic AI" },
    { label: "NLP", query: "NLP" },
    { label: "Medical AI", query: "Medical AI" },
    { label: "MLOps", query: "MLOps" },
    { label: "Trustworthy AI", query: "Trustworthy AI" },
  ];

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "60px 24px" }}>
      {/* Hero Header */}
      <section style={{ textAlign: "center", marginBottom: "48px" }}>
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          padding: "6px 14px",
          borderRadius: "20px",
          background: "rgba(59, 130, 246, 0.12)",
          border: "1px solid rgba(59, 130, 246, 0.3)",
          color: "#93c5fd",
          fontSize: "0.85rem",
          fontWeight: 500,
          marginBottom: "20px"
        }}>
          <Sparkles size={16} />
          <span>Powered by Meilisearch Engine &bull; Instant Typo-Tolerant Search</span>
        </div>

        <h1 style={{
          fontFamily: "var(--font-display)",
          fontSize: "3.2rem",
          fontWeight: 800,
          lineHeight: 1.15,
          letterSpacing: "-0.03em",
          marginBottom: "20px",
          background: "linear-gradient(135deg, #ffffff 40%, #93c5fd 80%, #6366f1 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent"
        }}>
          Explore Frontier Academic Research
        </h1>

        <p style={{
          fontSize: "1.15rem",
          color: "var(--text-secondary)",
          maxWidth: "680px",
          margin: "0 auto",
          lineHeight: 1.6
        }}>
          Discover academic publications, verified faculty profiles, research laboratories, and key research directions across AI and computing.
        </p>
      </section>

      {/* Main Search Input */}
      <section style={{ maxWidth: "760px", margin: "0 auto 36px" }}>
        <form onSubmit={handleSearch} style={{ position: "relative" }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            background: "var(--bg-input)",
            border: "1px solid var(--border-card)",
            borderRadius: "14px",
            padding: "8px 12px 8px 20px",
            boxShadow: "var(--shadow-md), var(--glow-blue)",
            transition: "all var(--transition-normal)"
          }}>
            <Search size={22} color="var(--text-muted)" style={{ marginRight: "12px", flexShrink: 0 }} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search papers, professors, topics, or institutions (e.g. Diffusion, Elena, Stanford)..."
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                color: "var(--text-primary)",
                fontSize: "1.05rem",
                outline: "none"
              }}
            />
            <button
              type="submit"
              className="btn-primary"
              style={{ padding: "10px 22px", borderRadius: "10px", flexShrink: 0 }}
            >
              <span>Search</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </form>

        {/* Quick Topic Filters */}
        <div style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          marginTop: "18px"
        }}>
          <span style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginRight: "4px" }}>Trending:</span>
          {topicPills.map((pill) => (
            <button
              key={pill.label}
              onClick={() => navigate(`/search?q=${encodeURIComponent(pill.query)}`)}
              className="tag-topic"
              style={{ padding: "4px 12px", fontSize: "0.85rem" }}
            >
              {pill.label}
            </button>
          ))}
        </div>
      </section>

      {/* Feature Pillar Cards */}
      <section style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
        gap: "24px",
        marginTop: "60px"
      }}>
        <div className="card-glass" style={{ padding: "30px 24px" }}>
          <div style={{
            width: "44px",
            height: "44px",
            borderRadius: "10px",
            background: "rgba(59, 130, 246, 0.15)",
            color: "#60a5fa",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: "16px"
          }}>
            <BookOpen size={24} />
          </div>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 600, marginBottom: "8px" }}>Academic Papers</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.6 }}>
            Search peer-reviewed papers and preprints with sub-millisecond retrieval, highlighted abstracts, and DOIs.
          </p>
        </div>

        <div className="card-glass" style={{ padding: "30px 24px" }}>
          <div style={{
            width: "44px",
            height: "44px",
            borderRadius: "10px",
            background: "rgba(168, 85, 247, 0.15)",
            color: "#c084fc",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: "16px"
          }}>
            <User size={24} />
          </div>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 600, marginBottom: "8px" }}>Researchers & Faculty</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.6 }}>
            Discover principal investigators, research groups, institutional affiliations, and verified contacts.
          </p>
        </div>

        <div className="card-glass" style={{ padding: "30px 24px" }}>
          <div style={{
            width: "44px",
            height: "44px",
            borderRadius: "10px",
            background: "rgba(16, 185, 129, 0.15)",
            color: "#34d399",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: "16px"
          }}>
            <Building2 size={24} />
          </div>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 600, marginBottom: "8px" }}>Global Institutions</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.6 }}>
            Explore leading universities, labs, and research organizations mapped with ROR persistent identifiers.
          </p>
        </div>
      </section>
    </div>
  );
};
