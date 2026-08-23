# aclu_marijuana_arrests_2018.csv

**Source.** ACLU, *A Tale of Two Countries: Racially Targeted Arrests in the Era of
Marijuana Reform* (2020), Table 7: "Black and White Marijuana Possession Arrest Rates and
Disparities by State (2018)". Plus the national row from Table 6 (2018).

**The ACLU's underlying sources.** FBI Uniform Crime Reporting Program arrest data
(via NACJD for 2010–2016; FBI Crime Data API for 2017–2018), supplemented by direct
state data for Illinois and New York City, combined with U.S. Census annual county
population estimates.

**Columns.** Arrest rates are per 100,000 people of that racial group. `black_white_rate_ratio`
is the Black arrest rate divided by the white arrest rate, as published.

**Transcription.** Typed from the published report table, not scraped. Verified by
recomputing every ratio from its own rate columns — all 50 rows agree with the published
figure to within 0.02.

**Known gaps, from the ACLU's own methodology section.**
- Florida and Washington, D.C. provided no data. 49 states only.
- UCR treats Latinx as an ethnicity, not a race, so Latinx individuals are absorbed into
  the Black and white counts. The ACLU notes this likely *understates* the true disparity.
- Counties with under 50% UCR reporting coverage were excluded; missing agency-months
  were imputed using the FBI's procedure.
- The UCR Hierarchy Rule means a marijuana possession arrest is only recorded when it is
  the most serious charge in the interaction.
- Figures are from 2018 and are the most recent in this report. Several states have
  changed marijuana law since.

**Why equal underlying use is a defensible assumption.** The ACLU cites SAMHSA national
survey data showing rates of marijuana use do not differ significantly between Black and
white populations. That is what licenses holding the simulation's true incident rates equal.