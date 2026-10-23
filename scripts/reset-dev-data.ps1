# Safely resets local development database and re-imports synthetic fixture
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Write-Host "Resetting ResearchRadar development dataset..." -ForegroundColor Yellow

$env:PYTHONPATH = "backend"
& (Join-Path $rootDir "backend\.venv\Scripts\python.exe") -c @"
import json
from app.core.database import SessionLocal, Base, engine
from app.search.client import get_meili_client
from app.search.indexes import ALL_INDEXES, initialize_indexes
from app.ingestion.importer import IngestionPipeline

print('1. Dropping and re-creating database tables...')
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print('2. Resetting Meilisearch indexes...')
client = get_meili_client()
for idx in ALL_INDEXES:
    try:
        t = client.delete_index(idx)
        client.wait_for_task(t.task_uid)
    except Exception:
        pass

initialize_indexes(client)

print('3. Re-importing canonical synthetic fixture...')
with open('fixtures/synthetic_research_data.json', 'r', encoding='utf-8') as f:
    fixture_data = json.load(f)

db = SessionLocal()
pipeline = IngestionPipeline(db, client)
job = pipeline.run_import(fixture_data, source_name='reset_fixture', dry_run=False)
print(f'Done! Processed: {job.records_processed}, Created: {job.records_created}, Status: {job.status}')
db.close()
"@

Write-Host "`nDevelopment data reset complete!" -ForegroundColor Green
