import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { User, Building2, Mail, ExternalLink, CheckCircle, ArrowLeft, BookOpen, Shield, Calendar } from "lucide-react";
import { getResearcher } from "../api/client";
import { Researcher, Institution, Provenance } from "../types";

export const ResearcherDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<{
    researcher: Researcher;
    institution?: Institution;
    provenance?: Provenance;
    publications: { id: string; title: string; publication_year: number; venue?: string; doi?: string }[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      setLoading(true);
      getResearcher(id)
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
          <div className="skeleton" style={{ width: "60%", height: "40px" }} />
          <div className="skeleton" style={{ width: "40%", height: "24px" }} />
          <div className="skeleton" style={{ width: "100%", height: "120px" }} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ maxWidth: "600px", margin: "60px auto", padding: "0 24px", textAlign: "center" }}>
        <div className="card-glass" style={{ padding: "40px" }}>
          <h2 style={{ color: "#f87171", marginBottom: "12px" }}>Researcher Not Found</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "24px" }}>{error || "Record could not be located."}</p>
          <Link to="/search" className="btn-secondary">
            <ArrowLeft size={16} />
            <span>Back to Search</span>
          </Link>
        </div>
      </div>
    );
  }

  const { researcher, institution, provenance, publications } = data;

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
        {/* Main Profile Header */}
        <div className="card-glass" style={{ padding: "36px 32px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                <span className="badge badge-researcher">
                  <User size={13} />
                  <span>Researcher</span>
                </span>
                {researcher.is_synthetic && (
                  <span className="badge badge-synthetic">Synthetic Demo</span>
                )}
              </div>

              <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2.2rem", fontWeight: 700, marginBottom: "8px" }}>
                {researcher.full_name}
              </h1>

              {institution && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "1.05rem", color: "var(--text-accent)" }}>
                  <Building2 size={18} />
                  <Link to={`/institutions/${encodeURIComponent(institution.id)}`} style={{ textDecoration: "underline", textUnderlineOffset: "4px" }}>
                    {institution.name}
                  </Link>
                  <span>&bull; {researcher.country}</span>
                </div>
              )}

              {researcher.department && (
                <div style={{ color: "var(--text-secondary)", fontSize: "0.95rem", marginTop: "4px" }}>
                  {researcher.department}
                </div>
              )}
            </div>

            {/* Official Profile Link */}
            {researcher.official_profile_url && (
              <a
                href={researcher.official_profile_url}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary"
                style={{ fontSize: "0.85rem" }}
              >
                <span>Institutional Profile</span>
                <ExternalLink size={14} />
              </a>
            )}
          </div>

          {/* Research Interests */}
          {researcher.research_interests && researcher.research_interests.length > 0 && (
            <div style={{ marginTop: "24px" }}>
              <div style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "8px" }}>
                Research Interests & Focus Areas
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {researcher.research_interests.map((topic, i) => (
                  <span key={i} className="tag-topic" style={{ padding: "4px 12px", fontSize: "0.85rem" }}>
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Biography */}
          {researcher.biography && (
            <div style={{ marginTop: "24px" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "8px" }}>
                Biography & Summary
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem", lineHeight: 1.65 }}>
                {researcher.biography}
              </p>
            </div>
          )}
        </div>

        {/* Verified Public Institutional Contact Card */}
        <div className="card-glass" style={{ padding: "24px 30px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
            <Mail size={20} color={researcher.contact_email_verified ? "#34d399" : "var(--text-muted)"} />
            <h3 style={{ fontSize: "1.05rem", fontWeight: 600 }}>Verified Institutional Contact</h3>
            {researcher.contact_email_verified ? (
              <span style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                background: "rgba(16, 185, 129, 0.15)",
                color: "#34d399",
                padding: "2px 8px",
                borderRadius: "4px",
                fontSize: "0.75rem",
                fontWeight: 600
              }}>
                <CheckCircle size={12} />
                <span>Verified</span>
              </span>
            ) : (
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Unverified</span>
            )}
          </div>

          {researcher.contact_email ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.95rem", color: "#60a5fa" }}>
                {researcher.contact_email}
              </div>
              {researcher.contact_source_url && (
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Verified from:{" "}
                  <a href={researcher.contact_source_url} target="_blank" rel="noreferrer" style={{ textDecoration: "underline" }}>
                    {researcher.contact_source_url}
                  </a>
                </div>
              )}
              {researcher.last_verified_at && (
                <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  <Calendar size={13} />
                  <span>Last verified: {new Date(researcher.last_verified_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: "0.88rem" }}>
              No public institutional email address has been authoritatively verified for this profile.
            </div>
          )}
        </div>

        {/* Selected Publications Section */}
        {publications && publications.length > 0 && (
          <div className="card-glass" style={{ padding: "28px 30px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "18px" }}>
              <BookOpen size={20} color="var(--accent-blue)" />
              <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>Related Publications</h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {publications.map((pub) => (
                <div key={pub.id} style={{
                  padding: "14px 18px",
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "8px"
                }}>
                  <Link
                    to={`/publications/${encodeURIComponent(pub.id)}`}
                    style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: "4px" }}
                  >
                    {pub.title}
                  </Link>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    {pub.venue} &bull; {pub.publication_year}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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
              <strong>Source Provenance:</strong> Ingested from <code>{provenance.source_provider}</code>
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
