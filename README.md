# NWS Staffing Analysis

## Research Question

Did NWS staffing cuts in 2025 result in statistically significant changes in warning performance?

## Data Source

**COW API** (`mesonet.agron.iastate.edu/api/1/cow.json`)

- 122 WFOs x 6 complete calendar years (2020-2025)
- Filtered to phenomena: **TO** (Tornado), **SV** (Severe Thunderstorm), **FF** (Flash Flood)
- Collected May 2026; 2025 is a full year with no partial-year bias
- Year boundary verified: no duplicate or misassigned events across year files

## Data Storage

```
data/
├── wfo_list.csv
├── raw/
│   └── COW/
│       └── {WFO}_{YEAR}.json   # one file per WFO-year, immutable
├── extracted/                  # flattened CSV, immutable checkpoint before cleaning
└── processed/                  # cleaned, analysis-ready files
```

## Data Model

Three tables extracted from the raw JSON:

| Table | Grain | Key fields |
|---|---|---|
| `events` | One row per warning event | `id`, `wfo`, `year`, `phenomena`, `fcster`, `issue`, `expire`, `verify`, `lead0` |
| `stormreports` | One row per LSR | `wfo`, `year`, `valid`, `lsrtype`, `warned`, `leadtime`, `events` (FK to events.id) |
| *(fcster analysis)* | TBD; unique forecasters per WFO per year | Derived from `events.fcster` |

## Analysis Design

- **Pre/post split:** 2020-2024 baseline, 2025 treatment
- **Primary metrics:** POD, FAR, CSI, and avg lead time derived from event-level data
- **Staffing proxy:** Year-over-year change in unique `fcster` values within each WFO

![Contingency table defining POD, FAR, and CSI](img/contingency_table.png)

## Notebooks

| Notebook | Purpose |
|---|---|
| `01_collection.ipynb` | Fetch raw COW API data for all WFOs and years |
| `02_extraction.ipynb` | Flatten raw JSON into events and stormreports tables |
| `03_cleaning.ipynb` | Type casting, null handling, and field normalization |
| `04_eda.ipynb` | Exploratory data analysis and feature engineering |
| `05_analysis.ipynb` | Statistical tests and before/after comparisons |
| `06_synthesis.ipynb` | Findings and visualizations for the paper |

## Methodological Notes

1. **LSR underreporting:** LSRs are filed voluntarily; miss rates should be interpreted as "among reported events." A drop in unwarned reports in 2025 could reflect fewer LSRs filed, not better performance.
2. **`fcster` field quality:** Format varies by WFO (last names, initials, badge numbers). Cross-WFO headcount comparisons are invalid. Within-WFO year-over-year changes may be valid, pending verification of within-WFO format consistency.
3. **Magnitude field:** Not comparable across phenomena (EF scale for TO, mph for SV, inches for FF). Must split by `lsrtype` before any magnitude analysis.
4. **Small-sample WFOs:** WFOs with very few events in a year will produce unreliable per-WFO statistics. A minimum events threshold may be needed.
5. **Non-CONUS offices:** Alaska, Hawaii, Guam, and Puerto Rico have fundamentally different weather patterns. Consider flagging or excluding from the main analysis.
