import {
  SearchResponse,
  Researcher,
  Publication,
  Institution,
  Provenance,
  ImportJob,
  SearchAnalyticsSummary,
  HealthStatus,
} from "../types";

const API_BASE = "/api";

export async function search(params: {
  q?: string;
  type?: string;
  limit?: number;
  offset?: number;
  sort?: string;
  country?: string;
  institution_name?: string;
  research_interests?: string;
  publication_year?: number;
  venue?: string;
  keywords?: string;
  source_provider?: string;
  is_synthetic?: boolean;
}): Promise<SearchResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== "") {
      query.append(key, String(val));
    }
  });

  const res = await fetch(`${API_BASE}/search?${query.toString()}`);
  if (!res.ok) {
    throw new Error(`Search request failed with status ${res.status}`);
  }
  return res.json();
}

export async function getResearcher(id: string): Promise<{
  researcher: Researcher;
  institution?: Institution;
  provenance?: Provenance;
  publications: { id: string; title: string; publication_year: number; venue?: string; doi?: string }[];
}> {
  const res = await fetch(`${API_BASE}/researchers/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Failed to load researcher: ${res.statusText}`);
  }
  return res.json();
}

export async function getPublication(id: string): Promise<{
  publication: Publication;
  institution?: Institution;
  provenance?: Provenance;
}> {
  const res = await fetch(`${API_BASE}/publications/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Failed to load publication: ${res.statusText}`);
  }
  return res.json();
}

export async function getInstitution(id: string): Promise<{
  institution: Institution;
  provenance?: Provenance;
  faculty_count: number;
  researchers: { id: string; full_name: string; department?: string; research_interests: string[] }[];
  publications_count: number;
  publications: { id: string; title: string; publication_year: number; venue?: string }[];
}> {
  const res = await fetch(`${API_BASE}/institutions/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Failed to load institution: ${res.statusText}`);
  }
  return res.json();
}

export async function getHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

// Admin API
export async function triggerImport(
  payload?: any,
  dry_run: boolean = false,
  apiKey: string = "rr_admin_secret_dev_key_change_me"
): Promise<ImportJob> {
  const res = await fetch(`${API_BASE}/admin/import?dry_run=${dry_run}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-API-Key": apiKey,
    },
    body: JSON.stringify(payload || {}),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Import failed with status ${res.status}`);
  }
  return res.json();
}

export async function listImports(apiKey: string = "rr_admin_secret_dev_key_change_me"): Promise<ImportJob[]> {
  const res = await fetch(`${API_BASE}/admin/imports`, {
    headers: { "X-Admin-API-Key": apiKey },
  });
  if (!res.ok) throw new Error("Failed to list imports");
  return res.json();
}

export async function getImportJob(jobId: string, apiKey: string = "rr_admin_secret_dev_key_change_me"): Promise<ImportJob> {
  const res = await fetch(`${API_BASE}/admin/imports/${jobId}`, {
    headers: { "X-Admin-API-Key": apiKey },
  });
  if (!res.ok) throw new Error("Failed to fetch import job");
  return res.json();
}

export async function triggerReindex(apiKey: string = "rr_admin_secret_dev_key_change_me"): Promise<any> {
  const res = await fetch(`${API_BASE}/admin/reindex`, {
    method: "POST",
    headers: { "X-Admin-API-Key": apiKey },
  });
  if (!res.ok) throw new Error("Reindex failed");
  return res.json();
}

export async function getSearchAnalytics(apiKey: string = "rr_admin_secret_dev_key_change_me"): Promise<SearchAnalyticsSummary> {
  const res = await fetch(`${API_BASE}/admin/search-analytics`, {
    headers: { "X-Admin-API-Key": apiKey },
  });
  if (!res.ok) throw new Error("Failed to load search analytics");
  return res.json();
}
