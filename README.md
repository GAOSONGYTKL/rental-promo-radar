# Rental Promo Radar

Official rental offers, with sources and clear limits.

**Production site: https://rental-promo-radar.pages.dev/**

English-language directory for `car rental coupon codes`. Sources span multiple regions; currencies, terms and regions remain those of the original provider. An advertised rate is not a live booking quote or a verified coupon.

## Run

Python 3.12 or newer. No packages, paid inference, or scraping API keys.

```
python scraper.py
python -m unittest discover -s tests -v
python build.py
```

`scraper.py` checks robots.txt before each source, fails closed on robots errors, and never bypasses login or anti-bot pages. Only reviewed deterministic adapters produce rates; other providers retain a source/status page. Failure removes old prices. Unknown dates and availability are never invented. Source evidence stays in ignored `work/source-checks/`; published rows include the URL, timestamp and SHA-256 of the fetched response.

`.ilang/site.ilang` is the actual configuration read by scraper and builder. Change its PROVIDERS section to change generated providers. `tests/` checks that behavior, expiry removal, JSON-LD and sitemap consistency. No live conversion of currencies is performed.

## Automation and hosting

The workflow requests a run every six hours at minute 17 UTC using a standard GitHub-hosted Ubuntu runner. GitHub may delay schedules or disable inactive schedules; this is not an uptime guarantee. The built-in GitHub token commits results; no user secret is needed for scraping/building. Configure Cloudflare Pages Git integration, build command `python build.py`, output `site`. After the first deployment, write the **actual returned URL** into `base_url` and `@SITE domain`, rebuild and redeploy. An unconfigured build is intentionally noindex and has no production canonical or sitemap URLs.

Cloudflare API deployment requires a pre-existing local Cloudflare credential. It is a deployment credential, never a scraper/runtime dependency. A token-based Actions deployment would require a stored Cloudflare secret; prefer Pages Git integration when no user-managed runtime secret is desired.

## Monetization

No affiliate programs have been approved, no commissions or income are claimed, and all links start as direct official links. After approval of a rental program, enter its permitted tracking link in the provider's fourth column; the site adds `rel=sponsored` and commission disclosure. Check program rules for coupon publishing, geography and promotion restrictions first. No hosting offers, paid brand bidding, cookie injection or self-referrals. Social publishing is not enabled in v1. A future sale should rely on verifiable traffic/income and owned branding, not promises about domain age.

Useful primary documentation: [GitHub Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage), [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/), [Pages Git integration](https://developers.cloudflare.com/pages/configuration/git-integration/).

站点规则用 I-Lang 协议描述，见 .ilang/site.ilang；协议说明 ilang.ai。
