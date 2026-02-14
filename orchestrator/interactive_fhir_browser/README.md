# Interactive FHIR Browser

Terminal-based patient browser for FHIR servers. Browse patients, view timelines, and export records.

## Prerequisites

Start the FHIR server using the instructions in <ehr/README.md> for starting the EHR and loading test data

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
