# Three-minute demonstration

Launch the app using the locked dependencies. Default language is Chinese;
the sidebar switches to English without changing model results.

1. 0:00-0:25: introduce the Yunnan snub-nosed monkey and the question,
   "Where might suitable conditions persist under the supplied 2050 scenario?"
2. 0:25-1:10: show current and future suitability with the same legend.
3. 1:10-1:50: show the change map and inspect a cell's environmental values.
4. 1:50-2:25: explain observed model performance, sample limitations, and
   environmental drivers without claiming causation.
5. 2:25-3:00: explain uncertainty, static vegetation, source attribution, and
   the educational-use boundary.

For the locked runtime at threshold 0.50, the measured baseline is 26,721 km2
current suitable area versus 24,820 km2 in 2050, a 7.1% decline. Explain that
this is threshold-dependent modeled suitability, not observed habitat loss.
Preliminary held-out ROC-AUC is 0.8173, with just eight presence cells in the
validation subset. Do not promise a species outcome.

Switch between Current, 2050, Score change, and Area classes. Select grid
G1089 using the cell inspector, then try a different threshold. Show that
area estimates change without retraining. Visit Data quality to explain why
128 records became 34 unique presence cells. Export the evidence ZIP.

No live service or map tiles are needed after dependencies are installed.
Ollama remains deferred; do not present a chat feature.

Before presenting, check launch from the independent root, readable legends,
working controls, comparable scales, and the full current/future/change flow.
