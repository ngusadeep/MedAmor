# Interactive FHIR Browser

Terminal-based patient browser for FHIR servers. Browse patients, view timelines, and export records.

## Prerequisites

Start the FHIR server:
```bash
docker compose up hapi_fhir hapi_db
```

Verify it's running:
```bash
curl -X GET "http://localhost:8080/fhir/metadata"
```

And verify it has data:
```bash
curl -s "http://localhost:9080/fhir/Patient?_count=1" | jq '.entry[0].resource.id'
```

If no data exists, see `ehr/README.md` for loading synthetic patient data.

## Usage

```bash
uv run main.py
```

### Controls

**Patient List:**
- `↑/↓` - Select patient
- `←/→` - Change page
- `Enter` - View patient timeline
- `r` - Refresh
- `q` - Quit

**Timeline View:**
- `↑/↓/PgUp/PgDn` - Scroll
- `Home/End` - Jump to start/end
- `e` - Export
- `q` - Back

### Export Options

1. **Full** - All resources
2. **Handoff Minimal** - Demo handoff set
3. **Handoff Complete** - Production handoff set
4. **Imaging Minimal** - Demo imaging set
5. **Imaging Complete** - Production imaging set
6. **Export All** - Generate all 5 files

Files are saved as: `{patient_id}_{name}_{type}_{timestamp}.txt`
