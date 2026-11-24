# Measuring the Nous plan meter during multi-lane SMAC batches

What a batch of unattended RE rounds actually costs, measured — not estimated.

## Reading the gauge (authoritative)

The portal value is the only truth; the Hermes per-turn `$` estimate is not.

```bash
cd /home/paul/.hermes/installs/d43f5b66bc9bdbcd/environments/0e98e25e08c744cb9c2d246fd22fab03/workspace
/home/paul/.hermes/installs/d43f5b66bc9bdbcd/environments/0e98e25e08c744cb9c2d246fd22fab03/venv/bin/python - <<'PY'
from hermes_cli.nous_account import get_nous_portal_account_info
info = get_nous_portal_account_info(force_fresh=True)
print({x.id: round(x.used_bp / 100, 2) for x in info.usage_window.gauges})
print(info.paid_service_access_info.purchased_credits_remaining)
PY
```

- Readings settle ~5 min after a fire; an immediate read under-reports.
- Always print `purchased_credits_remaining` too: the stop guard is "Today >= 80% **or** credits move".
  Across a measured ~54 pp of day-window burn in one batch the credits never moved ($2.4607 constant).

## What the windows do under load

Two lanes, then three, all pinned to `deepseek/deepseek-v4.1-flash-1017` (provider `nous`), each round
fired manually on a paused schedule so per-round deltas are clean:

| lanes | per-round day-gauge delta |
|---|---|
| 2 | +1.7 to +5.7 pp (early rounds) |
| 3 | +0.3 to +2.1 pp, collapsing toward +0.3 in later rounds |

- **Three lanes are ~1.5x the work for far less than 1.5x the meter**, because the lanes re-read the same
  repo docs and the prompt cache absorbs most of it. Late-round deltas near +0.3 pp are cache hit, not
  idleness — the fires still landed full milestones (80-150 API calls, 800-1850 s each).
- **A big `$` estimate does not mean a big plan hit.** Measured inversion: a round costing $0.0539 (243k
  output tokens) moved Today +1.66 pp, while a $0.0440 round (138k out) moved +3.37 pp. The plan meter tracks
  prompt/cache VOLUME, so it rewards short, cache-warm fires and punishes long fresh contexts.
- Wall-clock per lane is 14-45 min; the slow ones are the ones that rebase/merge mid-fire, not the ones that
  think hardest.

## Projecting the 80% guard

Estimate from the last 2-3 rounds' settled deltas, not the batch average (the average over-states late cost).
When the collapse sets in, a batch of this shape spends roughly a point every 3-4 rounds — say so plainly
rather than re-quoting an early-round rate.
