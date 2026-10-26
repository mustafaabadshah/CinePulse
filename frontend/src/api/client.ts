import {
  SearchResponse,
  Episode,
  Program,
  ImportJob,
  HealthStatus,
  IndexStatusSummary,
  SourceFilesStatus,
} from "../types";

const API_BASE = "/api";

export interface SearchParams {
  q?: string;
  type?: "all" | "programs" | "channels" | "episodes";
  limit?: number;
  offset?: number;
  sort?: string;
  is_free?: boolean;
  content_tier?: string;
  genre?: string;
  channel_name?: string;
  info_language?: string;
  info_content_type?: string;
  region?: string;
  is_vertical?: string;
  program_id?: string;
}

export async function search(params: SearchParams): Promise<SearchResponse> {
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

export async function getEpisode(id: string): Promise<Episode> {
  const res = await fetch(`${API_BASE}/episodes/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Failed to load episode: ${res.statusText}`);
  }
  return res.json();
}

export async function getProgram(id: string): Promise<Program> {
  const res = await fetch(`${API_BASE}/programs/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Failed to load program: ${res.statusText}`);
  }
  return res.json();
}

export async function getHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

// Admin API
export async function getSourceFiles(apiKey: string = "rr_admin_secret_dev_key_change_me"): Promise<SourceFilesStatus> {
  const res = await fetch(`${API_BASE}/admin/source-files`, {
    headers: { "X-Admin-API-Key": apiKey },
  });
  if (!res.ok) throw new Error("Failed to load source files status");
  return res.json();
}

export async function getIndexStatus(apiKey: string = "rr_admin_secret_dev_key_change_me"): Promise<IndexStatusSummary> {
  const res = await fetch(`${API_BASE}/admin/index-status`, {
    headers: { "X-Admin-API-Key": apiKey },
  });
  if (!res.ok) throw new Error("Failed to load index status");
  return res.json();
}

export async function triggerImport(
  payload?: any,
  dry_run: boolean = false,
  sourceType: string = "csv",
  apiKey: string = "rr_admin_secret_dev_key_change_me"
): Promise<ImportJob> {
  const res = await fetch(`${API_BASE}/admin/import?dry_run=${dry_run}&source_type=${sourceType}`, {
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
