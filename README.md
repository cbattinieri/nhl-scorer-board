# nhl-scorer-board

Public face of the NHL anytime-goal-scorer model: tonight's slate with the model's
probability beside the de-vigged market price, plus the running record.

**Live:** https://cbattinieri.github.io/nhl-scorer-board/

This repo holds only the built page. The model, the pipeline and the API keys live
elsewhere and are never committed here.

## How it updates

```
nhl_betting_models (local)
  run_daily.py        -> predictions logged before puck drop
  capture_close.cmd   -> sportsbook prices captured near puck drop
  publish_board.py    -> builds docs/ and pushes here
       |
GitHub Pages serves docs/
       |
.github/workflows/daily_email.yml  -> 6:45 PM ET email with the link
```

`docs/index.html` is self-contained — data inlined, no runtime fetch — so it keeps
working offline once loaded and installs cleanly as a home-screen app.

## Freshness

The build machine is a laptop that sleeps, so the board can silently fall behind.
Two timestamps are therefore carried everywhere (page header, `docs/status.json`,
and the email): **when the model last ran** and **when odds were last captured**.
They are separate because they fail separately. The page shows a red bar and the
email subject says `STALE` when the published slate is not today's.

## Secrets this repo needs

| Secret | What it is |
|---|---|
| `MAIL_USERNAME` | Gmail address the mail is sent from |
| `MAIL_PASSWORD` | Gmail **app password** (not the account password; requires 2FA) |
| `MAIL_TO` | Where the daily email goes |

## Not betting advice

Research output. Expected value here is computed at the single best price across
books, which by construction selects whichever book is furthest off, and the model
has been running hot against its own predictions. Nothing here is a recommendation
to stake money.
