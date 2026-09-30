# Data Directory Policy

Raw licensed/vendor market data should normally **not** be committed to this repository.

## Local layout

Recommended local structure:

```text
data/
  raw/          # downloaded source files, ignored
  vendor/       # vendor-specific datasets, ignored
  cache/        # generated caches, ignored
  fixtures/     # tiny synthetic/test fixtures may be committed
```

## Formal CIM-V1 data

See:

```text
DATA_CONTRACT.md
DATA_SOURCES.md
```

## Reproducibility

A backtest run should record enough metadata to reproduce the dataset query or local build:

```text
source/vendor
feed
symbol
date range
timezone
session
adjustment policy
download/query date
missing-data policy
checksum when practical
```

Do not claim a formal consolidated-data result if the input is venue-limited.
