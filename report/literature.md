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

---

## 4. Media Coverage: 2025 NWS Staffing Cuts and Warning Performance

Contemporaneous journalism documenting the 2025 staffing reductions, their operational effects, and specific incidents. All entries are from outlets with editorial oversight, named sources, and corrections policies. Sources are AP wire, Washington Post, PBS NewsHour, NPR, and expert-authored opinion in The Atlantic. Statistics are noted with attribution quality; unsourced figures are flagged.

These sources are appropriate for establishing policy context and documenting the treatment timeline. They are not peer-reviewed and should be cited as journalistic sources in the manuscript.

---

**Dance, S., 2025: Trump fires hundreds at NOAA, National Weather Service.** *The Washington Post*, February 28. https://www.washingtonpost.com/climate-environment/2025/02/27/noaa-nws-mass-firings-trump-administration/

The initial breaking news account of the February 27 terminations — the treatment start date used in this analysis. Termination letters sent to probationary employees across NOAA including NWS forecasters, radar maintenance staff, satellite data scientists, and Hurricane Hunters. Preliminary tally from a person close to the agency showed largest numbers in the National Marine Fisheries Service and Weather Service; total at least 5% of NOAA's workforce (attributed to Sen. Van Hollen and a person close to the agency). Termination letters stated employees were "not fit for continued employment because your ability, knowledge and/or skills do not fit the Agency's current needs." Named example: Andrew Hazelton, physical scientist and Hurricane Hunters veteran, confirmed his firing on X. A federal judge ordered the administration to reverse the mass firings the same day; it was not immediately clear how the ruling would affect NWS terminations. The firings came days before a forecast severe weather outbreak in the southeastern U.S. and months before hurricane season. The agency announced simultaneously that staffing shortages would prevent weather balloon launches from a station in northern Alaska. Key quote: Daniel Swain (UCLA climate scientist): "If there were to be large staffing reductions at NOAA and NWS … there will be people who die in extreme weather events and weather-related disasters who would not have otherwise."

---

**Kemp, A., 2025: As NOAA braces for more cuts, scientists say public safety is at risk.** *PBS NewsHour*, March 14. https://www.pbs.org/newshour/nation/as-noaa-braces-for-more-cuts-scientists-say-public-safety-is-at-risk

Documents 500+ probationary terminations in the first round, 108 NWS-specific, and 170 NWS employees accepting deferred resignations (attributed to JoAnn Becker, National Weather Service Employees Organization). Reports suspension of weather balloon launches and cancellation of climate briefings. Establishes that private-sector weather services cannot substitute for federal capacity because commercial products depend on NOAA infrastructure.

---

**Borenstein, S. (AP), 2025: Nearly half of National Weather Service offices are critically understaffed, experts warn.** *PBS NewsHour*, April 4. https://www.pbs.org/newshour/politics/nearly-half-of-national-weather-service-offices-are-critically-understaffed-experts-warn

Based on AP analysis of NWS employee data obtained directly. Finds 55 of 122 NWS offices at or above 20% vacancy rate; 8 offices above 35%; 23 without a meteorologist-in-charge; 16 without a warning coordination meteorologist. Vacancy rate doubled from 9.3% (March 2015) to 19% (March 2025). The most granular publicly available office-level staffing baseline for the treatment period.

---

**Dance, S., 2025: National Weather Service buyouts will leave gaps as storm season ramps up.** *The Washington Post*, April 17. https://www.washingtonpost.com/weather/2025/04/16/national-weather-service-buyouts-staff-shortages-trump-administration/

The most operationally detailed account of the April buyout wave. NWS Director Ken Graham told staff that 8 of 122 forecast offices would soon have 7 or fewer meteorologists doing the work of 12–15, leaving those offices functionally unable to handle a major outbreak (attributed to two people familiar with his comments). At least 300 NWS employees had applied for buyouts by the Thursday deadline; ~1,400 were eligible. Workforce dropped below 4,000 for the first time in modern history after the combined effect of probationary firings and buyouts, leaving the agency nearly 20% smaller than at Trump's inauguration. Internal Commerce Department memo obtained by the Post directs offices to reduce weather balloon launches from twice to once daily at 25% vacancy, and to suspend launches entirely when no second meteorologist is available. Offices in Kansas City, Omaha, Louisville, Des Moines, and Grand Rapids identified as most severely affected. Paducah, KY forecasters had to use portable toilets in the parking lot because the bathroom was inoperable and contracts for basic repairs had been halted. Spanish-language forecast translations were terminated in April when an AI translation contract lapsed. Key quote: Alan Gerard (recently retired, former meteorologist-in-charge, Jackson MS): "You can only stretch things so much. Eventually, things start to break." Key quote: Rep. Eric Sorensen (D-IL): "I am incredibly worried about the safety of my own constituents." **Relevant to this analysis:** The April departure wave is the second phase of the treatment timeline (February terminations → April departures); this article documents its operational severity in detail.

---

**Dance, S., and J. Muyskens, 2025: Where local forecast offices no longer monitor weather around the clock.** *The Washington Post*, May 16. https://www.washingtonpost.com/weather/2025/05/16/weather-service-offices-overnight-cuts-map/

Documents four NWS offices that ceased 24/7 operations as of publication, with several more scheduled to lose overnight coverage by May 18: Hanford CA, Sacramento CA (already dark); Pendleton OR, Cheyenne WY, Fairbanks AK (starting May 18); Goodland KS (already dark); Jackson KY (already dark); Marquette MI (starting May 18). Reports NWS workforce contracted by nearly 600 employees since January 2025 — the same number of departures the agency saw across the prior 15 years (attributed to Tom Fahy, NWSEO legislative director). When an office closes overnight, monitoring duties transfer to neighboring offices. NOAA spokeswoman Kim Doster: "NOAA anticipates no loss of critical information to the American people." Fahy: staffing has stretched employees' resilience "to the breaking point." The 155 critical vacancies the agency was urgently seeking to fill by month-end — including three senior meteorologist positions at Goodland — are documented from an internal agency email obtained by the Post. **Directly relevant to this analysis:** Goodland (GLD) is in our top-quartile SV WFO set and was explicitly operating without overnight coverage during peak severe weather season.

---

**Dance, S., 2025: How a tornado tested a Kentucky weather office that cut its overnight staff.** *The Washington Post*, May 17. https://www.washingtonpost.com/weather/2025/05/17/tornadoes-understaffed-jackson-kentucky-weather-office/

Case study of the NWS Jackson, KY office (JKL, 31% vacancy rate) during the May 15–16 tornado outbreak. The office's new reduced-staffing schedule would have left it dark overnight; forecasters were specifically called in ahead of the system. Reports 30–40 minute warning lead times despite staffing concerns, attributable to a clear radar signature. At least 18 deaths in the office's coverage area. Relevant to treatment timeline complexity: informal surge staffing may suppress measurable COW performance signals even when underlying capacity is degraded.

---

**Borenstein, S. (AP), 2025: Weather experts worry about a dangerous mix of more tornadoes and fewer meteorologists.** *PBS NewsHour*, May 22. https://www.pbs.org/newshour/nation/weather-experts-worry-about-a-dangerous-mix-of-more-tornadoes-and-fewer-meteorologists

Provides office-level vacancy rates from AP-obtained NWS data: Louisville (LMK) 29%, Wichita (ICT) 32%, Jackson (JKL) 25% as of March 2025. Quotes Rich Thompson (NWS Storm Prediction Center): cuts "made it harder on us." Elbert Friday on exhausted forecasters: "bleary-eyed, they can't identify what's going on on the radar." The office-level vacancy rates are the best available public proxy for staffing dose, though they reflect March 2025 and not the full year.

---

**Allen, G., 2025: Ahead of hurricane season, the National Weather Service is reeling from DOGE's cuts.** *NPR*, May 24. https://www.npr.org/2025/05/24/nx-s1-5407546/ahead-of-hurricane-season-the-national-weather-service-is-reeling-from-doges-cuts

Reports ~550 NWS employees departed by late May 2025, bringing total NWS workforce below 4,000 for the first time in agency history (historical context attributed to Brian LaMarre, former NWS meteorologist-in-charge, Tampa). Weather balloon launches cut at some offices; upper-atmosphere data reduced ~10%. Former NOAA undersecretary Mary Glackin warned that even announced rehiring would not result in new staff onboarded before September 2025 at earliest — consistent with the August partial rehiring wave in our treatment timeline.

---

**Kayyem, J., 2025: This Tornado Mayhem Is a Warning.** *The Atlantic*, May 19. https://www.theatlantic.com/ideas/archive/2025/05/tornado-weather-alerts-doge-cuts/682847/

Opinion by Juliette Kayyem (Harvard Kennedy School, former Assistant Secretary for Intergovernmental Affairs, DHS). Frames the May 2025 tornado outbreak (42 deaths, Missouri/Kentucky/Virginia) as a warning about DOGE-driven degradation of the warning system. Central argument: NWS and NOAA are in the "time management" business — their function is to extend the lead time available for protective action, and staffing cuts directly erode that capacity. Notes that private-sector weather services cannot substitute because they depend on federal data infrastructure. Cites ~40% of offices with significant staffing gaps and >10% workforce departure consistent with AP/union reporting at the time. **Not a primary statistical source;** useful for policy framing.

---

**Biesecker, M., and B. Slodysko (AP), 2025: Debate erupts over weather forecasts for deadly Texas floods and adequate staffing.** *PBS NewsHour*, July 7. https://www.pbs.org/newshour/nation/debate-erupts-over-weather-forecasts-for-deadly-texas-floods-and-adequate-staffing

Most directly relevant to this analysis. Documents 6 of 27 positions vacant at EWX (Austin/San Antonio), the office responsible for Kerr County during the July 4 Hill Country flooding (139 deaths). The warning coordination meteorologist role — responsible for warning issuance and coordination with local emergency management — was vacant; the previous holder departed in April 2025 after 17+ years following early-retirement pressure, consistent with the April departure wave in our treatment timeline. Commerce Secretary Lutnick testified June 4 that NWS was "fully staffed with forecasters and scientists" — directly contradicted by the EWX vacancy data. Trump stated the flood was "a thing that happened in seconds. No one expected it. Nobody saw it" — contradicted by NWS records showing warnings issued hours in advance.

---

**NPR, 2025: How good was the forecast? Texas officials and the National Weather Service disagree.** *NPR*, July 6. https://www.npr.org/2025/07/06/nx-s1-5458512/texas-flash-flood-weather-forecast

Documents the timeline of EWX warnings on July 4: flash flood warning issued 1:14 a.m. CDT with "considerable" tag triggering Wireless Emergency Alerts; upgraded to flash flood emergency 4:03 a.m. — more than three hours before the Kerr County Sheriff logged first flooding reports at low-water crossings. Texas Division of Emergency Management Chief Nim Kidd publicly criticized the forecast precision ("the amount of rain that fell in this specific location was never in any of those forecasts"). The Austin/San Antonio office was operating without both its science and operations officer and its warning coordination meteorologist, both of whom departed in April 2025. The Guadalupe River rose 26 feet in 45 minutes.

---

**Natanson, H., and B. Dennis, 2025: National Weather Service at 'breaking point' as storm approaches.** *The Washington Post*, September 27. https://www.washingtonpost.com/politics/2025/09/27/national-weather-service-staffing-crisis/

The most comprehensive account of NWS staffing status at the peak of hurricane season, after the August hiring exemption was announced but before meaningful new staff could be onboarded. Confirms ~600 departures (nearly 1 in 7 workers) through a combination of ~100 probationary firings and ~500 buyouts/retirements/resignations. Two offices still unable to operate 24/7 as of late September (Central Valley CA and western KS — i.e., Goodland); a dozen more on reduced staffing. The Trump administration announced authority to list 450 positions in August, but hiring is slow and onboarding will take months. Key operational details: single-person overnight shifts in at least one eastern U.S. office (normally two); offices sharing employees remotely with understaffed neighbors; weather balloon launches curtailed; community outreach and school presentations suspended. NOAA spokeswoman: agency "maintained its operational excellence despite alarmist allegations," citing Texas flood response as evidence. Key quotes — Tom Fahy (NWSEO): "There's a breaking point." John Sokich (45-year NWS veteran, retired January 2025): "They're going to run out of gas. They're going to start missing things." Brian LaMarre: "In my time here, the agency has never, ever been below 4,000. This is uncharted waters." Jeff Masters: hiring questions asking what applicants would do to further Trump's policy goals "will discourage qualified employees" and are "not relevant to the job." Chris Vagasky: "We are patching something that we damaged. It's putting a Band-Aid on a major wound." **Critical relevance to this analysis:** The August hiring exemption is the third phase of the treatment timeline; this article confirms the exemption did not produce a rapid recovery — hundreds of positions remained vacant through September and the rehiring process was expected to take months. A simple pre/post (2020–2024 vs. 2025) design treats the August announcement as the end of the treatment; this article establishes it was not.

---

**Mellen, R., and H. Natanson, 2025: Winter is coming. Not all weather offices are ready.** *The Washington Post*, December 8. https://www.washingtonpost.com/weather/2025/12/06/winter-national-weather-service-staff-shortages/

End-of-year status report on NWS staffing, confirming the August rehiring announcement produced limited recovery through year-end. Of the 450 positions authorized, NOAA had advertised 184 as of early December, with "final selections and onboarding in various stages" — on track to fill remaining roles by end of fiscal year 2026 (Kim Doster, NOAA spokeswoman). A 43-day government shutdown stalled federal hiring further. Offices in more than half a dozen states remain significantly understaffed. Office-level vacancy data as of October 1 (NWSEO): Des Moines IA — 8 of ~14 meteorologists, vacancy rate up from 13% (Biden) to 38% (Trump); Rapid City SD — 7 of ~13, up from 17% to 42%, including vacant science and operations officer and senior service hydrologist; Goodland KS — still missing 8 meteorologists, up from 32% to 41%, having halted 24-hour forecasts earlier in the year. Rick Spinrad (former NOAA administrator, Biden): "It would not be a surprise if we saw a major devastating storm this winter, for which loss of life and damage to property in part was a consequence of not being as prepared as we were with a fully staffed NOAA." Spinrad also notes that even when positions are filled, institutional knowledge and relationships with local emergency managers — built over years by warning coordination meteorologists — cannot be quickly replaced. John Sokich: offices are "a car slowly running out of gas." **Critical relevance to this analysis:** Confirms that the 2025 treatment was effectively in force for the full calendar year. The August hiring exemption produced no meaningful recovery by December — Goodland (GLD), a top-quartile SV office in our dataset, remained at 41% vacancy and still without 24-hour coverage. Our full-year 2025 treatment assumption is well-supported by the documentary record.

---

## Analysis Notes

- **No peer-reviewed study yet provides a systematic quantitative pre/post analysis of 2025 NWS warning performance.** This paper would be the first. The novelty is a strength but requires careful framing of what ITS can and cannot establish causally.
- **Severe thunderstorm warning verification** has no national climatology paper comparable to Brooks & Correia. The Stumpf & Gerard (2021) paper is the best available peer-reviewed reference; the gap should be acknowledged in the methodology section.
- **Flash flood warning verification** literature is sparse relative to tornadoes. Gourley et al. (2012) predates storm-based FF warnings; direct metric comparisons require caution.
- **Treatment timeline complexity:** The 2025 staffing reduction was phased (February terminations → April departures → August partial rehiring). A simple pre/post split treats 2025 as uniformly treated. ITS with two interruption points or a sensitivity analysis should be considered.
