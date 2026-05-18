# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app runs at **http://localhost:8501**. There are no tests, no linter config, and no build step.

## Architecture

ArkHub is a **multi-system Streamlit app** with a single entry point (`app.py`) that owns navigation for all pages.

### Navigation pattern

`app.py` uses `st.navigation()` to register every page under named groups (`ArkScore`, `Company`), then renders a fully custom sidebar with `st.page_link()` — the native Streamlit sidebar nav is hidden via CSS. Adding a new page requires registering it in **both** places in `app.py`.

### System layout

Each system lives under `systems/` and follows the same pattern:
- A `home.py` overview page
- Feature pages (views) alongside it
- A `utils/` sub-package containing store modules and helpers

```
systems/
  arkscore/          # EOS L10 scorecard
    utils/
      constants.py       # thresholds, colour palette, PM list, required CSV columns
      parse_clockify.py  # CSV parsing + utilization calculation logic
      utilization_store.py
      entry_store.py     # weekly check-in entries
      project_store.py
  people/            # Workforce & employee directory
    utils/
      employee_store.py  # shared employee reference used by ALL systems
      pattern_store.py   # working patterns + live availability helpers
```

### Persistence

All data is stored as flat JSON files written at runtime — **no database**. Each store module manages its own file under a `data/` directory that sits beside it (e.g. `systems/arkscore/data/`, `systems/people/data/`). These `data/` directories and all `*.json` inside them are git-ignored and created automatically on first write.

Store modules follow a consistent pattern:
- `_ensure()` creates the data dir and file if missing
- `_load()` / `_save()` handle serialization
- Public functions (`get_*`, `upsert_*`, `delete_*`) are the only API — views never touch JSON directly

### Cross-system dependency

`systems/people/utils/employee_store.py` is the **shared people registry**. Any system that needs a list of employees should import from there, not maintain its own.

### Week labelling

The ArkScore system resolves any picked date to its **Sun–Thu working week** (Cairo work week). `entry_store.week_label_from_date()` and `utilization_store` both use this convention. Week labels look like `2025-W20 – May 11 – 15, 2025`. Consistency here is critical — the week label is the primary key for utilization reports and check-in entries.

### Clockify CSV ingestion

`parse_clockify.py` expects Clockify **Detailed Report** exports. The required column list is in `constants.REQUIRED_COLUMNS`. `Duration (decimal)` is used for all hour calculations; `Duration (h)` is ignored. Utilization % is calculated against a fixed `TARGET_HOURS = 35.0`.

### Theme

The dark-navy theme is defined in `.streamlit/config.toml`. Inline styles in views should use the colour constants from `systems/arkscore/utils/constants.py` (`COLOR_BG`, `COLOR_CARD`, etc.) rather than hardcoded hex values.
