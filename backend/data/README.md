# Stock jury evaluation dataset

Place frozen JSON array data at `STOCK_JURY_EVALUATION_DATASET`.

Each record must match `app.stock_jury.evaluation.HistoricalCase`. The loader
requires at least 100 unique cases and rejects future-data leakage. Keep input
evidence limited to data available on each `analysis_date`; append a new
dataset file for each approved prompt version.
