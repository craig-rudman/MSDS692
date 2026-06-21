# CLAUDE.md

Guidance for implementing the severe-weather detection-change analysis. Read this before writing or running code.

## Objective

For each event type (severe thunderstorm SV, flash flood FF, tornado TO) and each of three metrics (POD detection, FAR false alarms, lead time), analyzed separately and never pooled, test whether year 10 (2025) departs from the season-adjusted baseline trend fit over years 1 to 9 (2016 to 2024). The departure is the quantity of interest: in the model `C(season_cat) + study_year + is_year10`, the `is_year10` term answers the question, read net of season and net of baseline drift. This is not a flat baseline-versus-year-10 comparison; the `study_year` trend is what "departure" is measured against. That is nine separate questions and nine model fits; do not collapse the metrics into a single score.

The finding is associational: a before/after observational comparison, not a controlled experiment. It establishes whether a metric changed, not why. In particular it does not identify a cause such as staffing; no reliable per-office staffing data was available, and the design cannot attribute a year-10 change to it. See the interpretation cautions and future work.

## Scope rules

- Analyze the three event types separately: severe thunderstorm (SV), flash flood (FF), tornado (TO). Never pool them. They have different base rates and detection difficulty.
- Run three metrics, each as its own model, for each event type. That is nine model fits total.
- The study footprint is the continental United States (CONUS). Non-CONUS Weather Forecast Offices (Guam, Honolulu, the Alaska offices, and Pago Pago; the `NON_CONUS` set in `src/constants.py`) are out of scope and are clipped out during cleaning (`COWCleaner.clip_to_conus`), so the cleaned tables and all nine fits are CONUS-only. Clip by office (WFO) code, not coordinate: a warning is an area with no single point, so the office code is the one key common to both tables.
- Treat the result as the answer to a specific, narrow question per metric. Do not overstate.

## Data sources

- LSR table: one row per observed event (local storm report). Used to measure detection.
- Warnings table: one row per issued warning. Used to measure false alarms.
- Lead-time values: attached to warned events only (minutes of advance warning).

Confirm these structures before modeling. Do not assume schemas; inspect the actual files first.

## The three models

All use the same right-hand side: `C(season_cat) + study_year + is_year10`, fit on all ten years.

The cleaning step (03_cleaning) derives the model-ready columns from the `YYYY-Season` label, so the analysis consumes them directly:

- `season_cat`: season-of-year category (Spring/Summer/Fall/Winter), the 4-level term for `C(season_cat)`. Do not use the `season` column (the `YYYY-Season` period id) here; it encodes the year and would collide with `study_year`.
- `study_year`: numeric 1-based treatment-relative index, 1 (2016) through 10 (2025). This is the numeric trend term. It is not the calendar year; a January-2026 row carries `study_year` 10 via the `2025-Winter` label.
- `is_year10`: integer 0/1 indicator, 1 only for `study_year == 10`, derived from `study_year` in cleaning.

The `study_year` term absorbs any baseline drift across years 1 to 9. The `is_year10` term (a 0/1 indicator, 1 only for year-10 rows) is the quantity of interest: it measures how far year 10 departs from the season-adjusted baseline trend. Reading its coefficient, p-value, and confidence interval directly answers the research question. Do not reduce this to a flat baseline-versus-year-10 comparison, which ignores drift.

1. Detection (POD): logistic regression on storm-report rows. Outcome: was the observed event warned (0/1). The `warned` column is already integer 0/1 from cleaning.
   `smf.logit("warned ~ C(season_cat) + study_year + is_year10", data=stormreports)`
2. False alarms (FAR): logistic regression on warning rows. Outcome: did the warning verify (0/1). The `verify` column is already integer 0/1 from cleaning.
   `smf.logit("verify ~ C(season_cat) + study_year + is_year10", data=events)`
3. Lead time: OLS on warned storm reports only (`warned == True`). Outcome: `leadtime` in minutes (continuous).
   `smf.ols("leadtime ~ C(season_cat) + study_year + is_year10", data=warned)`

Subset by event type with `lsrtype` on storm reports and `phenomena` on events (both use TO/SV/FF codes). Use the statsmodels formula API. `season_cat` must be categorical via `C()`, never numeric. `study_year` is numeric. `is_year10` is integer 0/1.

## Analytic workflow (per metric, per event type)

1. Plot the raw yearly rate (or mean lead time) before any modeling. Inspect for outlier years and visible trend.
2. Drift check: fit `C(season_cat) + study_year` on baseline years 1 to 9 only and inspect the `study_year` coefficient. This is diagnostic, to understand whether the baseline was drifting and by how much. It is not the final test.
3. Main test: fit the full model `C(season_cat) + study_year + is_year10` on all ten years. Read the `is_year10` coefficient. With `study_year` in the model absorbing the baseline trend, this coefficient is the year-10 departure from that trend.
4. Report the magnitude and uncertainty of the `is_year10` term, not just a p-value. For logistic models, exponentiate to an odds ratio. For OLS, the coefficient is already in minutes.
5. Sanity-check the two fits against each other. If the year-1-to-9 slope was steep, confirm the full model's `study_year` term is consistent; a large swing suggests year 10 is influencing the trend estimate and warrants a look.

## Placebo (falsification) test

Purpose: confirm the method only detects a change when one actually happened. If the same machinery flags a "change" in an innocent baseline year, the year-10 result cannot be trusted. Run this for each metric and each event type.

Procedure:

1. Drop year 10 entirely. The placebo runs on baseline years 1 to 9 only, so the real effect cannot leak in.
2. For each eligible baseline year, prefer interior years and avoid the first and last, which anchor the trend, build an `is_placebo` indicator set to 1 for that year and 0 otherwise.
3. Refit the same structure with the fake indicator: `warned ~ C(season_cat) + study_year + is_placebo` (use the matching outcome per metric: `warned`, `verify`, or `leadtime` via OLS). One fit per placebo year.
4. Collect the `is_placebo` coefficient, p-value, and effect size from each fit into a table.

Interpretation:

- Count how many placebo years come back significant at the chosen threshold. Roughly the alpha fraction is expected by chance; substantially more signals the model is too quick to flag noise.
- Compare the real `is_year10` effect against the distribution of placebo effects. The real effect standing clearly outside the placebo spread is persuasive; the real effect sitting among them undercuts the year-10 finding.
- A single placebo "hit" is not automatically a failure. It can mean that year had real unmodeled structure (a weather anomaly, a reporting shift), which is itself worth noting about baseline lumpiness.

Caution: with nine baseline years there are only a handful of usable placebo years. Treat the placebo distribution as a rough credibility check, not a formal null distribution.

## Data prerequisites and validation

Before fitting, and fail loudly if any check fails:

- Tidy long format, one row per opportunity.
- Logistic outcomes coded as integer 0/1. Cleaning casts the boolean `warned` and `verify` columns to int (`cast_outcome`), so the cleaned CSVs are already model-ready; re-check the dtype after load.
- `study_year` stored as a number (1 to 10), `season_cat` stored as text labels (Spring/Summer/Fall/Winter).
- An `is_year10` column coded integer 0/1, equal to 1 only for `study_year == 10`. Derived from `study_year` in cleaning; do not hand-enter it.
- No unhandled missing values in modeled columns. Report and handle NaNs deliberately; do not let the library drop rows silently. Cleaning already clips to the ten study seasons (`clip_to_study_span`) and asserts no NaNs in the season columns.
- Run `df.groupby('lsrtype')['warned'].mean()` (and the `phenomena`/`verify` equivalent on events) plus per-`season_cat` counts to surface thin cells and check for separation (a 0% or 100% rate prevents estimation).
- Verify event-matching rules (space/time tolerances linking warnings to reports) are identical across all ten years. The COW `params` block records these per file (`lsrbuffer`, `wind`, `hailsize`, `warningbuffer`), so the check is concrete. Flag any inconsistency; it can masquerade as a real change.

## Interpretation cautions (include in any written output)

- LSRs are imperfect ground truth. Changes in reporting effort can look like changes in detection. State this limitation.
- Read POD, FAR, and lead time together. Aggressive warning can raise detection while also raising false alarms. A single metric can mislead.
- Lead time is conditional on detection. More marginal late catches can pull mean lead time down even with no degradation.
- Storm clustering breaks strict independence and can understate standard errors. Note it; revisit with clustered/robust errors if it proves material.
- Nine baseline years is few points for a trend. Report wide uncertainty honestly.
- Multiple tests across metrics and event types inflate false positives. Apply a correction or label results exploratory.
- The year-10 geographic footprint shifts relative to baseline (confirmed in EDA: spatially coherent, far more cells move than sampling explains). This is ordinary year-to-year weather variation, not evidence of a performance change, but it means geographic composition is a live rival explanation for any national year-10 rate move. State it; do not treat a national shift as if the underlying weather were held fixed.
- No reliable per-office staffing or vacancy data was available for this study, so year-10 changes cannot be attributed to office-level staffing. Do not infer a staffing effect from office-level patterns; the data does not support it. (The newspaper-sourced overnight-closure list was removed for this reason.) Acquiring a credible source is a recommendation, see future work.

## Coding conventions

- No code changes without first discussing the design and the intent. Before writing or editing any code (notebook cells or `src/` modules), state what the code will do and why, and reach agreement on the approach. This is a working collaboration, not an autonomous build: surface the plan, let the user weigh in, then implement. The exception is a change the user has just explicitly asked for in concrete terms; even then, if the design is non-obvious, say how you intend to do it before doing it.
- Implement quietly, then summarize. The workflow is: agree on design and intent, implement with very little narration, then report what was done so it can be reviewed. Do not narrate edits step by step or restate the code that was just written. Once the design is agreed, write it; the reply after implementation is a brief summary of what changed and what to check, not a walkthrough.
- Do not run or execute the notebook cells. Only the user runs the notebook, both individual cells and full-notebook execution (e.g. `jupyter nbconvert --execute`). You may write and edit notebook cells and run standalone scripts to smoke-test `src/` helpers, but executing the notebook itself is the user's job; hand it back for the user to run.
- Encapsulate logic in a module under `src/` whenever possible, not inline in the notebook. The goal is explainability, legibility, and reuse: a notebook cell should read as a short, narrated call into named, docstringed functions, not a wall of procedural code. Put loading and filtering in `src/analysis/data.py`, shared constants in `src/analysis/constants.py`, and statistical/model helpers in `src/analysis/stats.py` (or a sibling module). The notebook imports and orchestrates; the `src/` function carries the implementation, its docstring, and its reuse across notebooks. Reserve inline code for one-off glue (plot assembly, printing) that genuinely does not recur.
- Python, statsmodels for modeling, pandas for data, matplotlib for plots.
- Use the formula interface so categorical handling is explicit and readable.
- Keep each model fit reproducible: log the sample size, the rows dropped, and the fitted summary.
- Save plots and model summaries as artifacts; do not only print to console.
- One panel per plot by default. Every figure is a single panel unless an explicit decision is made to use multiple panels (subplots). Do not reach for a multi-panel layout to show several event types or metrics at once; prefer one focused figure, or separate figures, and raise the multi-panel option for agreement before building it.
- Follow the cell pattern: markdown (intent) then code (implementation) then output (figure) then markdown (caption). Every figure gets its own code block, so a code cell emits exactly one figure. Do not loop one code cell to emit several figures; split into one intent/code/figure/caption unit per figure (use a `src/` plot helper so the per-figure code cell is a one-line call rather than duplicated matplotlib). The intent markdown precedes the code and says what the figure will show and why; the caption markdown follows the figure and states what it shows or concludes. Cells that only run a check or print a table follow the same intent-then-code shape, with a one-line result note after.
- Do not use em dashes in generated prose or comments.
- Spell out acronyms on first use in any document. The first time an acronym appears in a notebook, module, or written output, give the full term with the acronym in parentheses (e.g. "ordinary least squares (OLS)"); the bare acronym is fine thereafter. This applies per document.

## Out of scope unless asked

- No causal language beyond what the design supports. This is a before/after observational comparison, not a controlled experiment.
- Do not invent additional metrics or covariates without confirming they exist in the data.

## Future work

The current design establishes whether metrics changed in year 10. It does not establish why. These extensions strengthen confidence and move toward causal attribution, in rough priority order.

- Acquire reliable per-office staffing data. This study had none, which is the binding limit on attribution: without a credible per-office staffing or vacancy measure (official NWS or AFGE records, not press accounts), year-10 changes cannot be tied to staffing. This is the prerequisite for the two extensions below and the single highest-value thing to obtain.
- Add a control group (difference-in-differences). The single before/after design supports an associational finding only. Comparing the year-10 change in treated units (offices that lost staff) against untreated units nets out broad weather and reporting shifts, enabling a causal claim. Depends on the staffing data above to define the treated set, and on untreated comparison units existing.
- Test the geography-by-staffing interaction. The year-10 weather footprint shifted (see interpretation cautions), so event load concentrated differently across offices. If load surged at offices that also lost staff, any performance hit would be largest where high load met high staffing loss and could be diluted to invisibility in the national figure. Modeling event load x staffing loss (an interaction or dose term), rather than netting geography out as a nuisance, targets that mechanism. Also depends on the staffing data above.
- Report and pre-specify effect sizes. With large event counts, statistical significance is cheap. Define in advance what magnitude is operationally meaningful and report effect sizes alongside p-values.
- Use clustered or robust standard errors. Storms cluster, so observations are not fully independent. Cluster at the storm or outbreak level; naive standard errors understate uncertainty.
- Test rival explanations for year 10. Document year-10 event volume and baseline reporting density over time. A shift in how much weather occurred, or how diligently it was reported, competes with a true performance change and the indicator cannot separate them.
- Run sensitivity analyses. Vary season boundaries, reference levels, and placebo years. A result that survives reasonable specification changes is credible; one that does not was fragile.
- Correct for multiple comparisons. Three metrics times three event types is nine tests. Apply a correction or explicitly label weaker results exploratory.
