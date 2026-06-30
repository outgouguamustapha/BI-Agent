# Traceability Report - BI Data Lineage

## Data Lineage
- **Source Database**: `enterprise_bi.db`
- **Tables Queried**: `accounts` (plan metadata and active status) and `monthly_metrics` (monthly operational records).
- **Extracted Fields**:
  - `accounts`: `company_name`, `plan_tier`, `status`
  - `monthly_metrics`: `log_month`, `mrr`, `active_users`, `api_calls`

## Validation & Exclusions
- Accounts with `status = 'Churned'` were cross-examined. Soylent Corp (ID: 106) was confirmed churned as of 2025-12, resulting in no 2026 metrics, which matches expected behavior.
- Missing values (NaNs) check: None found in active months metrics.

## Analytical Assumptions
- MRR additions represent upgrades or subscription additions.
- User growth is calculated as Month-on-Month percentage change.

### Model Constraints & Analytical Risk Assessments
- **Data Freshness Parameters**: The analysis relies on static monthly snapshots extracted from the `monthly_metrics` table. Any real-time modifications, mid-month plan changes, or lag in data logging are not captured, meaning metrics are only as fresh as the last fully consolidated reporting month.
- **Sample Bias Constraints (Multi-Month Timelines)**: Tracking cohorts across a multi-month timeline introduces sample bias. As new accounts sign up (e.g., Hooli in 2026-02), they skew the aggregate MoM growth metrics, making it difficult to distinguish between organic expansion of existing accounts and influx of new cohort volumes.
- **Historical Exclusion of Churned/Frozen Records**: Excluding inactive, frozen, or churned platform records (such as Soylent Corp) post-churn causes survivorship bias. It artificially inflates long-term trend calculations and growth percentages, as the analysis focuses primarily on accounts that remained active throughout the period, ignoring the revenue and API volume drop-offs from churned entities.