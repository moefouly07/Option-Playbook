# Data Sources and Tool Roles

This file describes preferred roles, not permanent guarantees. Tool capabilities, entitlements, and feeds can change.

## GitHub

Role:

```text
canonical documentation
version control
frozen rules
decision history
code and test review
```

GitHub is the source of truth for strategy definitions.

## Webull

Useful available roles include:

```text
US stock/ETF bars
snapshots
bid/ask depth where entitled
earnings/calendar context
account/order-history workflows when authorized
```

For bars, always record:

```text
timeframe
trading sessions
whether incomplete bars are included
timestamp
permission/delay status when known
```

Do not assume Webull intraday volume is consolidated across all venues unless the specific feed is documented as such.

## Alpaca

Useful available roles include:

```text
market clock
stock snapshots and quotes
equity feeds such as IEX/SIP/delayed SIP when available
option contract lookup
option quotes
option snapshots
IV and Greeks
option chains
```

Option feeds may be:

```text
OPRA
indicative
```

Always identify which one was used.

Vendor capability is not the same as installed capability. As of SCANNER-V1.1, Muse's installed `alpaca-market-data` skill is **stocks-only and read-only**. Option data listed above is an Alpaca capability that has not been integrated or tested, so scanner output is `OPTIONS_NOT_VERIFIED`.

IEX equity data is not the same thing as consolidated SIP data.

## AlphaStocks

Useful as a secondary view for:

```text
latest quote
company overview
news sentiment/headlines
risk/analysis context
chart visualization
```

Do not use a qualitative risk score as a mechanical CIM-V1 input.

## Web research

Use primary/authoritative sources for:

```text
official economic calendars
company releases
regulatory changes
exchange rules
broker policy changes
market-structure documentation
```

## Source precedence

For the formal historical backtest:

```text
documented consolidated historical dataset
>
venue-limited historical dataset
>
modeled reconstruction
```

For live examples, disagreements must be exposed rather than silently averaged.

Check:

```text
timestamp
session
feed
venue
delay
corporate-action treatment
```

before deciding that two sources conflict.
