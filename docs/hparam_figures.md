# Figure ideas for the tuning results

Metric names follow `datasets/SidsDataset/README.md` (Evaluation, "Metric names"):
answer diversity is ROME's fluency, generalizability is EasyEdit's portability, rewrite is
EasyEdit's reliability on the direct question.

Brainstorm (2026-11-07) of plots that show the important comparisons from
`docs/hparam_selection.md`. Ordered by how central the claim is. "Main" = a candidate for the
paper body, "appendix" = supporting.

## 1. The search funnel (main, schematic)
Four stacked bands, one per step, drawn as a funnel: width = settings crossed (all -> pair ->
one), with values per setting (5, 2, 3, 8-10), edits (10, 10, 40, 40) and runs annotated.
Shows the design idea in one picture: cross widely with few values, then narrow while adding
values.

## 2. Effect atlas (main)
Heatmap. Rows: every method's settings, grouped by method and coloured in the margin by
category (where / how hard / signal / inert). Columns: the 4 models. Cell colour: the main
effect on the overall score (diverging, low-is-better blue to high-is-better orange); a dot
marks a significant effect (Lenth). Answers "which settings matter, and do models agree" at a
glance: inert rows are pale, pivots are one colour across the row, model disagreements
(Mistral and Qwen) stand out as a colour flip within a row.
Variant: one panel per score (rewrite, generalizability, locality, answer diversity) for the appendix.

## 3. Strength is a trade-off (main)
For the strength settings (LoRA lr, LoCo lr, ROME clamp, IFMET v_lr), a dumbbell or diverging
bar chart of the effect on each of the 8 scores: rewrite, paraphrase, cross-lingual and
generalizability go up, locality, answer diversity and grammar go down. One small panel per setting, the 4
models as dots. Makes the point that "edit harder" buys generalisation with locality.

## 4. Where interactions live (main)
A 4 x 4 symmetric heatmap of setting categories (where, how hard, signal, inert), cell = share
of pairs with a significant interaction (31% within how hard, 9% how hard x where, about 0 for
signal). Justifies the sequential order of steps 2-3 (where, then strength, then signal).

## 5. Two canonical interaction plots (main or appendix)
Classic two-line interaction plots (x = setting A low / high, one line per level of B, y =
score):
- substitutes: LoRA lr x num_steps on rewrite (lines converge: once one is high the other adds
  nothing);
- amplifier: FiDAL candidate layers x clamp on Llama (late layers only hurt when clamp is
  high).
The shapes are easy to read and explain the two interaction families.

## 6. Where to edit, per model (main)
Grid: rows = models, columns = methods, cell = arrow or colour for "early better / late
better / no difference" (late minus early on the overall score), with a second version on
generalizability only. Shows the finding that the best location is a property of the model, not
the method, and that generalizability favours early layers almost everywhere. Optional companion:
the causal-tracing peak per model marked against the best edit layer, to show tracing does not
predict it.

## 7. Model robustness vs appetite for strength (main)
Scatter with one point per model (or per model x method): x = share of answer diversity kept after
editing (Mistral 0.88 ... Olmo 0.98), y = main effect of the strength settings on the overall
score. Expected: a rising trend, Mistral bottom left, Olmo and Qwen top right. Explains why
models disagree on how hard to edit.

## 8. The middle beats the corners (appendix)
Per method and model, the centre-run mean vs the corner mean of the overall score (paired dots
or a bar of the difference with its error bar from the 3 centre seeds). LoCo, LoRA, IFMET show
clear gains; justifies 3 values in step 2.

## 9. Seed noise (appendix)
Strip plot of the 3 centre runs' rewrite per method and model. ROME, FiDAL, LTI spread up to
33 points; the others overlap. Justifies 40 edits and 2 seeds for the ROME family.

## 10. Half-normal plots (appendix)
The standard factorial diagnostic: sorted absolute effects against half-normal quantiles, one
panel per method (pooled or one model), with Lenth's margin as a line and active effects
labelled. Readers who know DOE expect it.

## 11. Step-2 grids (main, after step 2)
For each method and model, a 3 x 3 heatmap of the overall score over the gridded pair, with
cells that fail a gate hatched and the chosen cell outlined. Small multiples across
models show where each model's best region sits.

## 12. Pareto front of the final choice (main, after step 3)
Per method: every tuning run as a point in (edit success = mean of rewrite, paraphrase,
generalizability) vs (preservation = mean of locality, answer diversity, grammar), step coloured, the
selected setting starred. Shows the chosen setting sits on the front and what the locality
weighting would change.

## 13. Default vs tuned (main)
Per method and model, the default EasyEdit setting vs the tuned one on all 8 scores (paired
bars or a slope chart). The payoff figure: how much tuning per model changes the comparison
between methods.
