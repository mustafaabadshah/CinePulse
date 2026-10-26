export interface SearchResultItem {
  id: string;
  type: 'episode' | 'program';
  title: string;
  subtitle?: string;
  snippet?: string;
  tags: string[];
  source_url?: string;
  thumbnail?: string;
  views?: number;
  duration?: string;
  duration_seconds?: number;
  is_free?: boolean;
  content_tier?: string;
  channel_name?: string;
  program_name?: string;
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

export interface Episode {
  id: string;
  title: string;
  slug: string;
  description?: string;
  program_id?: string;
  raw_program_id?: string;
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
  healthy: boolean;
  indexes: Record<string, { database_count: number; indexed_count: number; is_consistent: boolean }>;
  tasks: {
    pending: number;
    failed: number;
  };
  last_sync_time?: string;
  last_job_status?: string;
}

export interface SourceFilesStatus {
  data_dir: string;
  files: {
    enrichment_file: {
      filename: string;
      path: string;
      exists: boolean;
      size_bytes: number;
      modified_at?: string;
      total_rows?: number;
      has_bom?: boolean;
    };
    episodes_file: {
      filename: string;
      path: string;
      exists: boolean;
      size_bytes: number;
      modified_at?: string;
      total_rows?: number;
      has_bom?: boolean;
    };
  };
}
