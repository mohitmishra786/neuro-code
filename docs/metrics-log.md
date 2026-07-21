# Metrics log

Manual weekly (and launch-week daily) capture of GitHub Insights and issue health.  
**North Star proxy (90 days):** weekly clones + inverse rate of `setup`-labeled issues.  
Do **not** treat stars alone as success.

## How to fill

1. GitHub repo → **Insights → Traffic** (views, unique visitors, clones, referrers).  
2. Count open issues (and open with label `setup`).  
3. Note median first-response hours for new issues that week (approx OK).  
4. CI: last main branch status (green/red).

## Template row

| Date (UTC) | Stars | Forks | Views | Uniques | Clones | Top referrers | Open issues | Open setup | Median first response (h) | CI main | Notes |
|------------|-------|-------|-------|---------|--------|---------------|-------------|------------|---------------------------|---------|-------|
| YYYY-MM-DD | 0 | 0 | | | | | | | | | |

## Baseline

| Date (UTC) | Stars | Forks | Views | Uniques | Clones | Top referrers | Open issues | Open setup | Median first response (h) | CI main | Notes |
|------------|-------|-------|-------|---------|--------|---------------|-------------|------------|---------------------------|---------|-------|
| 2026-07-21 | 0 | 0 | n/a | n/a | n/a | — | see remote | 0 | n/a | pending first CI | Pre-launch baseline after audit implementation pass; Traffic Insights not yet sampled |

## Launch week (fill at T+0, T+24h, T+7d)

| Checkpoint | Stars | Clones | Notes |
|------------|-------|--------|-------|
| T+0 | | | |
| T+24h | | | |
| T+7d | | | |
