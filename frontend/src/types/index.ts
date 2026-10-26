export interface SearchResultItem {
  id: string;
  type: 'researcher' | 'publication' | 'institution' | 'episode' | 'program';
  title: string;
  subtitle?: string;
  snippet?: string;
  tags: string[];
  source_url?: string;
  is_synthetic: boolean;
  raw: Record<string, any>;
  formatted?: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  type: string;
  total_hits: number;
  offset: number;
  limit: number;
  page: number;
  total_pages: number;
  processing_time_ms: number;
  hits: SearchResultItem[];
  facet_distribution: Record<string, Record<string, number>>;
}

export interface Researcher {
  id: string;
  full_name: string;
  official_profile_url?: string;
  institution_id: string;
  institution_name?: string;
  department?: string;
  country: string;
  research_interests: string[];
  biography?: string;
  contact_email_verified: boolean;
  contact_email?: string;
  contact_source_url?: string;
  last_verified_at?: string;
  is_synthetic: boolean;
  created_at: string;
  updated_at: string;
}

export interface Publication {
  id: string;
  title: string;
  abstract?: string;
  authors: string[];
  primary_institution_id?: string;
  institution_name?: string;
  publication_year: number;
  venue?: string;
  doi?: string;
  canonical_url?: string;
  keywords: string[];
  source_provider: string;
  is_synthetic: boolean;
  imported_at: string;
  created_at: string;
  updated_at: string;
}

export interface Institution {
  id: string;
  name: string;
  normalized_name?: string;
  country: string;
  city: string;
  website_url?: string;
  ror_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Episode {
  id: string;
  title: string;
  slug: string;
  description?: string;
  program_id?: string;
  duration?: string;
  duration_seconds?: number;
  views: number;
  is_free: boolean;
  is_enable: boolean;
  content_tier?: string;
  genre?: string;
  genre_list: string[];
  region?: string;
  is_vertical?: string;
  thumbnail?: string;
  channel_name?: string;
  channel_status: boolean;
  source_file: string;
  imported_at?: string;
  created_at: string;
  updated_at: string;
  program?: Program;
  sibling_episodes?: {
    id: string;
    title: string;
    duration?: string;
    views: number;
    thumbnail?: string;
    is_free: boolean;
  }[];
}

export interface Program {
  id: string;
  type: 'program' | 'channel';
  name: string;
  slug: string;
  channel_name?: string;
  info_language?: string;
  info_genre?: string;
  genre_list: string[];
  info_meta_keywords?: string;
  info_content_type?: string;
  info_staring?: string;
  starring_list: string[];
  source_file: string;
  imported_at?: string;
  created_at: string;
  updated_at: string;
  episode_count?: number;
  episodes?: {
    id: string;
    title: string;
    slug: string;
    duration?: string;
    duration_seconds?: number;
    views: number;
    is_free: boolean;
    thumbnail?: string;
    genre?: string;
  }[];
}

export interface Provenance {
  source_provider: string;
  source_url?: string;
  is_verified: boolean;
  imported_at?: string;
}

export interface ImportJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'dry_run_completed' | 'search_sync_failed';
  source_name: string;
  dry_run: boolean;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  errors: any[];
  meili_task_ids: number[];
  started_at: string;
  completed_at?: string;
}

export interface SearchAnalyticsSummary {
  total_searches: number;
  zero_result_searches: number;
  zero_result_rate: number;
  average_latency_ms: number;
  p95_latency_ms: number;
  top_queries: { query: string; count: number }[];
  recent_searches: {
    id: number;
    query_text: string;
    index_name: string;
    filters_applied: Record<string, any>;
    results_count: number;
    latency_ms: number;
    zero_result: boolean;
    timestamp: string;
  }[];
}

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  components: {
    database: { status: 'up' | 'down' };
    meilisearch: {
      status: 'up' | 'down';
      indexes?: Record<string, { number_of_documents: number; is_indexing: boolean }>;
    };
  };
}

export interface IndexStatusSummary {
  status: string;
  meilisearch_reachable: boolean;
  indexes: Record<string, { database_count: number; indexed_count: number; is_synchronized: boolean }>;
  pending_tasks_count: number;
  failed_tasks_count: number;
  last_sync_time?: string;
}

export interface SourceFilesStatus {
  data_dir: string;
  files: Record<string, {
    filename: string;
    path: string;
    exists: boolean;
    readable: boolean;
    size_bytes: number;
    modified_at?: string;
    error?: string;
  }>;
}
