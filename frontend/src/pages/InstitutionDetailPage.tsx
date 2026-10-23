import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Building2, ExternalLink, ArrowLeft, Shield, User, BookOpen, MapPin } from "lucide-react";
import { getInstitution } from "../api/client";
import { Institution, Provenance } from "../types";

export const InstitutionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<{
    institution: Institution;
    provenance?: Provenance;
    faculty_count: number;
    researchers: { id: string; full_name: string; department?: string; research_interests: string[] }[];
    publications_count: number;
    publications: { id: string; title: string; publication_year: number; venue?: string }[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      setLoading(true);
      getInstitution(id)
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
          <div className="skeleton" style={{ width: "70%", height: "40px" }} />
          <div className="skeleton" style={{ width: "30%", height: "24px" }} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ maxWidth: "600px", margin: "60px auto", padding: "0 24px", textAlign: "center" }}>
        <div className="card-glass" style={{ padding: "40px" }}>
          <h2 style={{ color: "#f87171", marginBottom: "12px" }}>Institution Not Found</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "24px" }}>{error || "Institution record could not be located."}</p>
          <Link to="/search" className="btn-secondary">
            <ArrowLeft size={16} />
            <span>Back to Search</span>
          </Link>
        </div>
      </div>
    );
  }

  const { institution, provenance, faculty_count, researchers, publications_count, publications } = data;

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
        {/* Main Institution Header */}
        <div className="card-glass" style={{ padding: "36px 32px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
            <span className="badge badge-institution">
              <Building2 size={13} />
              <span>Institution</span>
            </span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
            <div>
              <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2.2rem", fontWeight: 700, marginBottom: "8px" }}>
                {institution.name}
              </h1>

              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-secondary)", fontSize: "1rem" }}>
                <MapPin size={18} color="var(--accent-blue)" />
                <span>{institution.city}, {institution.country}</span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              {institution.website_url && (
                <a
                  href={institution.website_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-primary"
                  style={{ fontSize: "0.85rem", padding: "8px 16px" }}
                >
                  <span>Official Portal</span>
                  <ExternalLink size={14} />
                </a>
              )}
              {institution.ror_id && (
                <a
                  href={institution.ror_id}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary"
                  style={{ fontSize: "0.85rem", padding: "8px 16px" }}
                >
                  <span>ROR Registry</span>
                  <ExternalLink size={14} />
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Affiliated Faculty Roster */}
        <div className="card-glass" style={{ padding: "28px 32px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "18px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <User size={20} color="var(--accent-purple)" />
              <h3 style={{ fontSize: "1.15rem", fontWeight: 600 }}>Affiliated Researchers & Faculty</h3>
            </div>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{faculty_count} recorded</span>
          </div>

          {researchers && researchers.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
              {researchers.map((res) => (
                <div key={res.id} style={{
                  padding: "16px 20px",
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "8px"
                }}>
                  <Link
                    to={`/researchers/${encodeURIComponent(res.id)}`}
                    style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: "4px" }}
                  >
                    {res.full_name}
                  </Link>
                  {res.department && (
                    <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "8px" }}>
                      {res.department}
                    </div>
                  )}
                  {res.research_interests && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                      {res.research_interests.slice(0, 3).map((topic, idx) => (
                        <span key={idx} className="tag-topic" style={{ fontSize: "0.75rem", padding: "2px 6px" }}>
                          {topic}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              No faculty records currently indexed for this institution.
            </div>
          )}
        </div>

        {/* Publications Roster */}
        <div className="card-glass" style={{ padding: "28px 32px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "18px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <BookOpen size={20} color="var(--accent-blue)" />
              <h3 style={{ fontSize: "1.15rem", fontWeight: 600 }}>Associated Publications</h3>
            </div>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{publications_count} recorded</span>
          </div>

          {publications && publications.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {publications.map((pub) => (
                <div key={pub.id} style={{
                  padding: "14px 18px",
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "8px"
                }}>
                  <Link
                    to={`/publications/${encodeURIComponent(pub.id)}`}
                    style={{ fontSize: "0.98rem", fontWeight: 600, color: "var(--text-primary)", display: "block", marginBottom: "4px" }}
                  >
                    {pub.title}
                  </Link>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    {pub.venue} &bull; {pub.publication_year}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              No publication records currently indexed for this institution.
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
