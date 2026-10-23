import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { BookOpen, Building2, ExternalLink, ArrowLeft, Shield, Calendar, Award } from "lucide-react";
import { getPublication } from "../api/client";
import { Publication, Institution, Provenance } from "../types";

export const PublicationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<{
    publication: Publication;
    institution?: Institution;
    provenance?: Provenance;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      setLoading(true);
      getPublication(id)
        .then((res) => setData(res))
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return (
      <div style={{ maxWidth: "960px", margin: "40px auto", padding: "0 24px" }}>
        <div className="skeleton" style={{ width: "120px", height: "30px", marginBottom: "20px" }} />
        <div className="card-glass" style={{ padding: "40px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div className="skeleton" style={{ width: "80%", height: "40px" }} />
          <div className="skeleton" style={{ width: "40%", height: "24px" }} />
          <div className="skeleton" style={{ width: "100%", height: "140px" }} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ maxWidth: "600px", margin: "60px auto", padding: "0 24px", textAlign: "center" }}>
        <div className="card-glass" style={{ padding: "40px" }}>
          <h2 style={{ color: "#f87171", marginBottom: "12px" }}>Publication Not Found</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "24px" }}>{error || "Paper record could not be located."}</p>
          <Link to="/search" className="btn-secondary">
            <ArrowLeft size={16} />
            <span>Back to Search</span>
          </Link>
        </div>
      </div>
    );
  }

  const { publication, institution, provenance } = data;

  return (
    <div style={{ maxWidth: "980px", margin: "40px auto", padding: "0 24px" }}>
      {/* Back button */}
      <Link to="/search" style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        color: "var(--text-muted)",
        fontSize: "0.85rem",
        marginBottom: "20px"
      }}>
        <ArrowLeft size={16} />
        <span>Back to search</span>
      </Link>

      <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
        {/* Main Paper Header */}
        <div className="card-glass" style={{ padding: "36px 32px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
            <span className="badge badge-publication">
              <BookOpen size={13} />
              <span>Publication</span>
            </span>
            {publication.is_synthetic && (
              <span className="badge badge-synthetic">Synthetic Demo</span>
            )}
          </div>

          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", fontWeight: 700, lineHeight: 1.3, marginBottom: "16px" }}>
            {publication.title}
          </h1>

          {/* Authors */}
          <div style={{ fontSize: "1.05rem", color: "var(--text-primary)", fontWeight: 500, marginBottom: "12px" }}>
            {publication.authors && publication.authors.join(", ")}
          </div>

          {/* Venue & Year Meta */}
          <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "16px", color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            {publication.venue && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Award size={16} color="var(--accent-blue)" />
                <strong style={{ color: "var(--text-primary)" }}>{publication.venue}</strong>
              </div>
            )}
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Calendar size={16} />
              <span>{publication.publication_year}</span>
            </div>

            {institution && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Building2 size={16} />
                <Link to={`/institutions/${encodeURIComponent(institution.id)}`} style={{ color: "var(--text-accent)", textDecoration: "underline" }}>
                  {institution.name}
                </Link>
              </div>
            )}
          </div>

          {/* Action Links (DOI / Canonical) */}
          <div style={{ display: "flex", gap: "12px", marginTop: "24px", flexWrap: "wrap" }}>
            {publication.canonical_url && (
              <a
                href={publication.canonical_url}
                target="_blank"
                rel="noreferrer"
                className="btn-primary"
                style={{ fontSize: "0.85rem", padding: "8px 16px" }}
              >
                <span>Read Official Paper</span>
                <ExternalLink size={14} />
              </a>
            )}
            {publication.doi && (
              <a
                href={`https://doi.org/${publication.doi}`}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary"
                style={{ fontSize: "0.85rem", padding: "8px 16px" }}
              >
                <span>DOI: {publication.doi}</span>
                <ExternalLink size={14} />
              </a>
            )}
          </div>

          {/* Abstract */}
          {publication.abstract && (
            <div style={{ marginTop: "32px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 600, marginBottom: "10px", color: "var(--text-primary)" }}>
                Abstract
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.98rem", lineHeight: 1.7 }}>
                {publication.abstract}
              </p>
            </div>
          )}

          {/* Keywords / Topic Tags */}
          {publication.keywords && publication.keywords.length > 0 && (
            <div style={{ marginTop: "28px" }}>
              <div style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "8px" }}>
                Keywords & Research Domains
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {publication.keywords.map((kw, i) => (
                  <span key={i} className="tag-topic" style={{ padding: "4px 12px", fontSize: "0.85rem" }}>
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Provenance Card */}
        {provenance && (
          <div style={{
            padding: "16px 20px",
            background: "rgba(255, 255, 255, 0.02)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "10px",
            fontSize: "0.8rem",
            color: "var(--text-muted)",
            display: "flex",
            alignItems: "center",
            gap: "10px"
          }}>
            <Shield size={16} />
            <div>
              <strong>Provenance Record:</strong> Provider: <code>{provenance.source_provider}</code>
              {provenance.source_url && (
                <span> &bull; Source URL: <a href={provenance.source_url} target="_blank" rel="noreferrer" style={{ textDecoration: "underline" }}>{provenance.source_url}</a></span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
