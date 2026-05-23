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
├── 01_collection/
│   └── COW/
│       └── {WFO}_{YEAR}.json   # one file per WFO-year, immutable
├── 02_extraction/              # flattened CSV, immutable checkpoint before cleaning
└── 03_cleaning/                # cleaned, analysis-ready files
```

## Data Model

Three tables extracted from the raw JSON:

| Table | Grain | Key fields |
|---|---|---|
| `events` | One row per warning event | `wfo`, `year`, `phenomena`, `issue`, `expire`, `verify`, `lead0`, `product_id` |
| `stormreports` | One row per LSR | `wfo`, `year`, `valid`, `lsrtype`, `warned`, `leadtime`, `events` (FK to `events.product_id`) |

## Analysis Design

- **Pre/post split:** 2020-2024 baseline, 2025 treatment
- **Primary metrics:** POD, FAR, CSI, and avg lead time derived from event-level data
- **Staffing treatment:** 2025 NWS staffing cuts treated as a system-wide intervention; no WFO-level staffing covariate (see Methodological Notes)

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
2. **No WFO-level staffing covariate:** `fcster` was investigated as a staffing proxy but abandoned — rolling 3-month analysis showed chronic format mixing (badge numbers, last names, initials coexisting) in 118 of 122 WFOs, making unique-count comparisons unreliable. No public WFO-level staffing dataset exists. The analysis treats 2025 as a system-wide treatment without a per-office staffing dose variable.
3. **Small-sample WFOs:** WFOs with very few events in a year will produce unreliable per-WFO statistics. A minimum events threshold may be needed.
4. **Non-CONUS offices:** Alaska, Hawaii, Guam, and Puerto Rico have fundamentally different weather patterns. Consider flagging or excluding from the main analysis.
