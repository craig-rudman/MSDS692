# Literature Review

Organized by theme. All sources are peer-reviewed journal articles, government reports, or official federal datasets unless noted. Journalistic sources are excluded; see analysis notes for how news coverage of specific 2025 events informs the treatment timeline.

## Research Process Note

This literature review was conducted with the assistance of Claude (Anthropic), an AI assistant, as part of a collaborative research workflow. Specifically, Claude performed the initial web searches across the four thematic areas, retrieved and summarized candidate sources, and drafted the annotations. All sources were identified and selected by Claude based on relevance to the research question; the author reviewed the results and directed the scope and focus of the search. Individual citations should be independently verified before inclusion in any submitted manuscript — DOIs and URLs are provided for that purpose.

---

## 1. Warning Performance Baselines and Verification Methods

**Brooks, H. E., and J. Correia Jr., 2018: Long-Term Performance Metrics for National Weather Service Tornado Warnings.** *Weather and Forecasting*, 33(6), 1601–1614. https://doi.org/10.1175/WAF-D-18-0120.1

Primary methodological anchor. Updates the NWS tornado warning verification time series over 1986–2016. Defines POD₁ (warned before event begins) vs. POD₂ (warned before or during), reports lead time averages (~18.8 min pre-2012, ~15.6 min post-2012), and documents the 2012 NWS policy discontinuity (default duration 45→30 min, raised warning threshold) as a structural break in the series. IEM `lead0` maps to POD₂ semantics; our 2020–2024 baseline sits entirely in the post-2012 regime.

---

**Brotzge, J., S. Erickson, and H. E. Brooks, 2011: A 5-yr Climatology of Tornado False Alarms.** *Weather and Forecasting*, 26(4), 534–544. https://doi.org/10.1175/WAF-D-10-05004.1

Analyzes all CONUS tornado warnings 2000–2004. Finds ~75% false alarm rate as a structural baseline; characterizes systematic FAR drivers (radar distance, population density, outbreak context). Establishes that FAR is not uniform across WFOs or conditions — relevant for interpreting any 2025 FAR shift.

---

**Brotzge, J., and W. Donner, 2013: The Tornado Warning Process: A Review of Current Research, Challenges, and Opportunities.** *Bulletin of the American Meteorological Society*, 94(11), 1715–1733. https://doi.org/10.1175/BAMS-D-12-00147.1

Interdisciplinary review covering detection, the warning decision, dissemination, and public response. Synthesizes POD/FAR/lead-time findings across the literature and identifies human and organizational factors as understudied contributors to warning performance — the key motivating gap for a staffing-focused study.

---

**Brotzge, J., S. E. Nelson, R. L. Thompson, and J. A. Smith, 2013: Tornado Probability of Detection and Lead Time as a Function of Convective Mode and Environmental Parameters.** *Weather and Forecasting*, 28(5), 1261–1276. https://doi.org/10.1175/WAF-D-12-00119.1

Shows that POD and lead time vary substantially with storm type (QLCS vs. supercell) and environmental shear. Establishes that meteorological heterogeneity drives meaningful POD variance — a confounder to acknowledge when comparing year-over-year metrics without storm-mode stratification.

---

**Krocak, M. J., M. D. Flournoy, and H. E. Brooks, 2021: Examining Subdaily Tornado Warning Performance and Associated Environmental Characteristics.** *Weather and Forecasting*, 36(5). https://doi.org/10.1175/WAF-D-21-0097.1

Demonstrates that the first tornado in a multi-event day is warned significantly less often than later events, and that within-day performance tracks kinematic parameters. Establishes within-outbreak performance gradients — relevant because staffing stress also peaks during outbreak conditions, creating a potential confound.

---

**Gourley, J. J., et al., 2012: Evaluation of Tools Used for Monitoring and Forecasting Flash Floods in the United States.** *Weather and Forecasting*, 27(1), 158–173. https://doi.org/10.1175/WAF-D-10-05043.1

Evaluates flash-flood guidance products against reported events; reports POD 0.41–0.66 and FAR 0.84–0.97 depending on product and accumulation period. The most directly citable peer-reviewed baseline for flash flood verification. Predates storm-based FF warnings and IEM COW era, so direct metric comparison requires caution.

---

**Stumpf, G. J., and A. E. Gerard, 2021: National Weather Service Severe Weather Warnings as Threats-in-Motion.** *Weather and Forecasting*, 36(2), 627–643. https://doi.org/10.1175/WAF-D-20-0159.1

Proposes moving-polygon warnings and evaluates current NWS severe thunderstorm and tornado warning verification against polygon-based metrics. Useful methodology reference for IEM COW polygon-based verification, particularly for severe thunderstorm warnings, which lack a national climatology paper comparable to Brooks & Correia.

---

**Simmons, K. M., and D. Sutter, 2009: False Alarms, Tornado Warnings, and Tornado Casualties.** *Weather, Climate, and Society*, 1(1), 38–53. https://doi.org/10.1175/2009WCAS1005.1

Using 1986–2004 data, shows that higher WFO-level FAR is associated with more casualties (cry-wolf effect): a one-standard-deviation FAR increase raises expected fatalities 12–29%. Provides causal motivation for why FAR changes have public safety consequences beyond the operational metric.

---

**Burow, D. A., et al., 2025: On the Convective Environments, Modes, and Warning Verifications of Tornado- and Flash Flood-Warned Storms in the Southeast United States.** *Meteorological Applications*, 32, e70062. https://doi.org/10.1002/met.70062

Examines simultaneous tornado and flash flood warnings, classifying by convective mode and computing verification metrics. Provides 2025 baseline data on co-occurring warning types — the most recent peer-reviewed warning verification paper and directly overlapping with our study period.

---

**NOAA/NWS: Tornado Warning Lead Time and False Alarm Ratio KPI Data, 2016–present.** U.S. Department of Commerce Performance Data Portal. https://performance.commerce.gov/KPI-NOAA/

Official federal annual KPI values for storm-based tornado warning lead time (minutes) and FAR. Usable as an independent check on IEM COW-derived metrics and as a source for pre-2020 trend context.

---

## 2. Staffing, Workload, and Human Performance in Forecasting

**Karstens, C. D., et al., 2020: Forecasters' Cognitive Task Analysis and Mental Workload Analysis of Issuing Probabilistic Hazard Information during FACETs PHI Prototype Experiment.** *Weather and Forecasting*, 35(4). https://doi.org/10.1175/WAF-D-19-0194.1

The only peer-reviewed study directly measuring NWS forecaster mental workload via NASA-Task Load Index. Mean workload 53.7/100 under prototype conditions; primary drivers were large storm counts, rapid development, and software switching. Provides the empirical workload framework for arguing that reduced staffing pushes individual workload into performance-degrading territory.

---

**Pfost, R. L., et al., 2022: To Warn or Not to Warn: Factors Influencing National Weather Service Warning Meteorologists' Tornado Warning Decisions.** *Weather, Climate, and Society*, 14(3). https://doi.org/10.1175/WCAS-D-20-0115.1

Cross-sectional forecaster survey showing that both scientific factors (radar couplet strength) and social/organizational factors (experience, office culture, peer consultation) influence tornado warning decisions. Establishes a mechanism by which staffing reductions — fewer consultable colleagues, more individual workload — could affect warning outcomes independently of meteorological inputs.

---

**GAO, 2006: Weather Forecasting: National Weather Service Is Planning to Improve Service and Gain Efficiency, but Impacts of Potential Changes Are Not Yet Known.** GAO-06-792. U.S. Government Accountability Office. https://www.gao.gov/assets/a250800.html

Federal audit documenting ~5% vacancy rates in 2006 as a pre-DOGE baseline. Found that forecast quality is sensitive to staffing configuration and recommended rigorous analysis before workforce changes. Useful for establishing the institutional staffing context predating 2025.

---

**National Academy of Public Administration (NAPA), 2013: Forecast for the Future: Assuring the Capacity of the National Weather Service.** NAPA Panel Report. https://napawash.org/academy-studies/forecast-for-the-future-assuring-the-capacity-of-the-national-weather-servi

Independent seven-month assessment recommending zero-based staffing analyses. Concluded that NWS lacked adequate organizational capacity for its Weather-Ready Nation mandate — documenting that the agency was already operating near staffing margins before 2025. Provides authoritative pre-treatment institutional context.

---

**NWS, 2017: Operations and Workforce Analysis (OWA) Catalog.** NOAA/NWS internal analysis. https://www.weather.gov/media/nws/OWA_Catalog_09072017.pdf

Documents WFO-level staffing norms (~15 meteorologists per office), peer-office workload sharing, and pre-existing structural understaffing. The most granular official staffing baseline document predating the 2025 cuts.

---

## 3. Quasi-Experimental Methods for Policy Evaluation

**Bernal, J. L., S. Cummins, and A. Gasparrini, 2017: Interrupted Time Series Regression for the Evaluation of Public Health Interventions: A Tutorial.** *International Journal of Epidemiology*, 46(1), 348–355. https://doi.org/10.1093/ije/dyw098

The standard practical tutorial for ITS regression. Covers model specification, pre-trend testing, autocorrelation correction (Newey-West, ARIMA), and interpretation of level vs. slope changes after an interruption. Directly applicable to a monthly-aggregated pre/post analysis across 2020–2025. Should be cited when justifying the ITS framework.

---

**Penfold, R. B., and F. Zhang, 2013: Use of Interrupted Time Series Analysis in Evaluating Health Care Quality Improvements.** *Academic Pediatrics*, 13(6 Suppl), S38–S44. https://doi.org/10.1016/j.acap.2013.08.002

Concise ITS methodology reference covering segmented regression, control series, and validity threats. More accessible than Bernal et al. for non-epidemiology readers; frequently cited alongside it in applied policy papers.

---

**Angrist, J. D., and J.-S. Pischke, 2009: *Mostly Harmless Econometrics: An Empiricist's Companion*.** Princeton University Press. https://press.princeton.edu/books/paperback/9780691120355/mostly-harmless-econometrics

Standard econometrics reference for natural experiments, difference-in-differences, and instrumental variables. Useful for framing internal validity threats and for readers from an econometrics background. Angrist received the 2021 Nobel Prize in Economics for related causal inference work.

---

**Shadish, W. R., T. D. Cook, and D. T. Campbell, 2002: *Experimental and Quasi-Experimental Designs for Generalized Causal Inference*.** Houghton Mifflin.

Canonical textbook on quasi-experimental design. Provides theoretical foundations for ITS, regression discontinuity, and selection bias — the methodological scaffolding for justifying a pre/post natural experiment when RCTs are not feasible.

---

## Analysis Notes

- **No peer-reviewed study yet provides a systematic quantitative pre/post analysis of 2025 NWS warning performance.** This paper would be the first. The novelty is a strength but requires careful framing of what ITS can and cannot establish causally.
- **Severe thunderstorm warning verification** has no national climatology paper comparable to Brooks & Correia. The Stumpf & Gerard (2021) paper is the best available peer-reviewed reference; the gap should be acknowledged in the methodology section.
- **Flash flood warning verification** literature is sparse relative to tornadoes. Gourley et al. (2012) predates storm-based FF warnings; direct metric comparisons require caution.
- **Treatment timeline complexity:** The 2025 staffing reduction was phased (February terminations → April departures → August partial rehiring). A simple pre/post split treats 2025 as uniformly treated. ITS with two interruption points or a sensitivity analysis should be considered.
