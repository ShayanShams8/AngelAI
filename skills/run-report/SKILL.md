---
name: run-report
description: Run an Angel AI workflow and generate a final PDF report. Manages workflow creation, tool execution, ML model training, and delivers the report to USER_PROJECT/RESULTS/.
---

# Angel AI — Run Report

## Purpose
Execute a full analysis workflow and produce a final PDF report.

## Trigger
Use this skill when: the user asks for a report, forecast, analysis, prediction, assessment, evaluation, scoring, or any data-driven output.

## CRITICAL — No Free-Text Answers for Analytical Tasks
Any request that involves evaluation, forecasting, prediction, scoring, assessment, or analysis of any kind **must always go through the full procedure below — no exceptions**. This includes questions phrased as "evaluate", "assess", "what are the chances", "how likely is", "analyze", or similar. A plain-text answer is **never** an acceptable substitute for a data-driven report.

## Behavior

### Step 1 — Verify prerequisites
- Confirm init-project has been run (USER_PROJECT/RESULTS/ and USER_PROJECT/workflows/ must exist).
- Install dependencies on demand, not upfront. Only run `pip install <package>` when a tool fails with `ImportError` or `ModuleNotFoundError`. Identify the missing package from the error, install only that package, then retry the tool. Never run `pip install -r requirements.txt` at the start of a session.

### Step 2 — Ask clarifying questions (single message, no drip-feed)
Before doing anything else, ask the user all ambiguous questions in **one message**. Do not proceed to platform selection or workflow design until you have clear answers. Only ask what is genuinely ambiguous — do not ask about things obvious from the prompt:
- What exact outcome do they want? (number, chart, forecast, ranking)
- What time range or geographic scope applies?
- Are there specific segments, filters, or comparisons?
- What level of detail do they want in the report?
- Do they have a hypothesis to test, or do they want exploratory analysis?
- Any known constraints (budget, data freshness, acceptable error rate)?

### Step 3 — Platform selection
Prompt the user to select a platform from resources/supported_platforms.txt, or choose "General". Do not label "General" as the recommended option.

### Step 4 — Think like a senior data engineer and ML engineer
**Before writing a single line of the workflow**, reason through the following:

**Data engineering questions:**
- Where does the raw data live? What format is it in (JSON, CSV, nested, paginated API)?
- What cleaning steps are required (nulls, duplicates, type coercion, currency normalisation, timezone alignment)?
- What is the grain of the dataset (one row = one what)?
- Does the data need to be joined across sources, and on what key?
- What is the expected row count — will it fit in memory?
- Are there schema inconsistencies between sources?

**ML engineering questions:**
- What is the exact prediction target (label)?
- Is this classification, regression, clustering, or time-series?
- What features are available before the prediction time (no leakage)?
- What is the class balance — is resampling needed?
- What baseline would a naive model achieve?
- Which algorithm family is most appropriate given data size, feature types, and interpretability requirements?
- What validation strategy is correct (random split, time-based split, group k-fold)?
- What metric is most meaningful to the user (accuracy, RMSE, AUC, precision@k)?

Only after answering these questions, write the workflow. The workflow must explicitly document: the data schema, feature engineering steps, chosen algorithm and why, validation strategy, and evaluation metric.

### Step 5 — Design and write the workflow
Write the workflow to USER_PROJECT/workflows/<task-name>.md. Workflows should evolve as you learn — update them when you find better methods or encounter constraints. Do not create or overwrite a workflow without asking, unless explicitly told to.

**Data source rules by mode:**
- **Platform selected:** The user's platform data is always the primary source for anything about their own business (sales, customers, transactions). External datasets (Kaggle, BigQuery public) are for context and comparison only — never as a substitute. Supplement with external datasets when the workflow requires data beyond what the platform provides (e.g. competitor benchmarks, market averages, industry trends).
- **General selected:** Search Kaggle first for a relevant dataset. Fall back to BigQuery public datasets if nothing suitable is found on Kaggle. Write the workflow only after the data source is confirmed and API keys are verified.

**Dataset relevance filter — mandatory:** Before using any dataset, review every column for relevance to the user's question. Drop any column that does not directly inform the specific question. If an entire dataset has no relevant columns, exclude it entirely.

**STRICT — Never generate your own dataset.** Never hardcode, fabricate, or synthetically construct training data from your knowledge. All training data must come from a real external source. If no suitable dataset exists, stop and tell the user — do not proceed with made-up data.

### Step 6 — Verify API keys
The workflow now defines exactly which APIs are needed. For each required key, handle **one at a time**:
1. Check USER_PROJECT/.env.angel for the key.
2. If present: confirm and continue.
3. If missing: add the variable name (no value) to USER_PROJECT/.env.angel, tell the user what it is and how to obtain it (refer to check-config Key Inventory for per-key guidance), then **wait for the user to confirm it is filled in** before moving to the next key.

Do not proceed to execution until all required keys are confirmed.

### Step 7 — Identify tools
Check USER_PROJECT/tools/ for existing scripts before creating anything new. Only build a new tool when nothing suitable exists.

### Step 8 — Determine training platform
Follow this decision sequence every time:
1. Write the workflow first for the best possible output, without considering system constraints.
2. Check if USER_PROJECT/system_info.txt is empty. If it is, run `tools/system.py` (bundled with the plugin) to populate it, then read it.
3. Decide where to train based on system_info.txt:
   - Sufficient local CPU/RAM/GPU with required ML libraries installed → **train locally**. Save model artifact to USER_PROJECT/tools/models/ and log it in models.txt.
   - Local resources insufficient → **train on Kaggle** (use the Kaggle Notebooks API to submit a training job, download the output model artifact, save to USER_PROJECT/tools/models/).
   - Kaggle unavailable or unsuitable → **use BigQuery `CREATE MODEL`**.
   - Task too complex for BigQuery ML (deep learning, large unstructured data, custom architectures) → **use Vertex AI AutoML**.
4. Training data may come from BigQuery public datasets, Kaggle, the Iowa Data Portal, or any other accessible public source — the training platform decision does not restrict data sources.

**Check for existing models first:** Before training, check USER_PROJECT/tools/models/models.txt for an already-suitable model. Do not re-train unnecessarily.

**You must always build a real ML model** for any forecast, prediction, or generative AI task. A deterministic scoring formula or weighted average is not a substitute. Never skip this step — if live data is temporarily unavailable, pause and resolve the data access issue instead of approximating.

**Do not use offline training knowledge** to assess, score, or substitute for real data-driven analysis.

### Step 9 — Execute
Run tools in sequence. Write all temporary/intermediate files to USER_PROJECT/tmp/. When an error occurs:
1. Read the full error message and trace.
2. Fix the script and retest. If the tool uses paid API calls or credits, confirm with the user before re-running.
3. Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior).
This loop is how the system improves over time.

### Step 10 — Generate the report
Generate the final PDF report and save it to USER_PROJECT/RESULTS/. Never save final PDFs to tmp/.

Every PDF must include this metadata table as the **first section**. Fill every field with actual values from the run. Never leave a field blank — use "N/A" only when a field is genuinely inapplicable (e.g. test accuracy for an unsupervised model):

| Field | Value |
|---|---|
| Algorithm(s) | e.g. ARIMA, Random Forest, BigQuery BOOSTED_TREE_REGRESSOR |
| Training Samples | e.g. 12,450 rows |
| Test Accuracy | e.g. RMSE: 0.042, R²: 0.91 |
| Rows in Dataset | e.g. 15,000 |
| Training Platform | e.g. Local (scikit-learn), BigQuery ML, Vertex AI AutoML |
| Report Date | e.g. 2026-03-16 |

### Step 11 — Model saving
Ask the user whether they would like to save the model:
- If trained locally: save the model artifact to USER_PROJECT/tools/models/ and log its name + description in models.txt.
- If trained in the cloud: save it in Google Cloud Console and log its name + description in models.txt.

### Step 12 — Clean up tmp/
After completing the task, delete files from USER_PROJECT/tmp/ that were created during this operation and are no longer needed. Rules:
- **Delete:** files that served only as stepping stones to the final output.
- **Keep:** files that are inputs or dependencies for a known follow-up step.
- **Never touch RESULTS/** during cleanup — only tmp/.
- If unsure whether a file is still needed, keep it.

## Rules
- Never place final PDFs in the plugin directory or tmp/.
- **STRICT — Never fabricate training data.** All data must come from real external sources.
- Always use real data sources: Kaggle first, then BigQuery public datasets, then other verifiable sources.
- Never skip the ML model step for any forecast or prediction task.
- Never use a deterministic formula or weighted average as a substitute for a real ML model.
- Never generate a plain-text answer as a substitute for a data-driven report.
- Do not use offline training knowledge to assess or score anything.
