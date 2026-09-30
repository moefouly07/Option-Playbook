# Security and Secrets

## Never commit secrets

Do not commit:

```text
API keys
broker tokens
account IDs
session cookies
private certificates
passwords
.env files
download URLs containing credentials
```

Use local environment variables or the platform's secure connector/authentication system.

## Broker/account data

If account/order data are used for execution research:

- minimize stored personal/account metadata;
- do not place account identifiers in examples or fixtures;
- sanitize exported order-history files before committing;
- keep raw broker exports outside the repository unless explicitly anonymized.

## Market-data licenses

Historical market-data files may have redistribution restrictions.

Do not commit vendor datasets merely because the repository is private.

Store local/vendor data outside version control and document provenance in run metadata.

## Generated outputs

Performance reports may be committed if they contain no secrets and their data-license terms permit it.

Always include the strategy version, code commit, data provenance, and assumptions.

## Incident rule

If a secret is accidentally committed, deleting the file in a later commit is not enough.

Rotate/revoke the credential and remove it from repository history when appropriate.
