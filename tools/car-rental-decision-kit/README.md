# Car Rental Decision Kit

Offline CSV worksheets and a Python standard-library calculator for comparing a replacement rental quote with an existing reservation.

The comparison method is documented in [Rental Promo Radar's rental rebooking guide](https://rentaldealradar.com/guides/best-car-rental-deals/).

## What is included

- `compare_quotes.py`: exact decimal arithmetic, currency/scope checks and separate funding calculations.
- `switching-checklist.csv`: a portable checklist derived from the guide's decision sheet.
- `deposit-record.csv`: an empty reconciliation worksheet derived from the site's deposit guide.
- `CHECKLIST.md`: a practical sequence for gathering evidence.
- `quote-input-template.csv`: input headers only; fill these with your own reservation evidence.
- `test_compare_quotes.py`: executable checks using explicitly synthetic fixtures.

There are no rental prices, assumed supplier fees, live availability claims, booking requests, analytics, accounts or network requests in the calculator.

## Run locally

Use Python 3.10 or newer; no packages to install.

```text
python compare_quotes.py --template > my-quotes.csv
python compare_quotes.py my-quotes.csv
python -m unittest -v test_compare_quotes
```

Keep completed quote files locally. Do not upload reservation numbers, personal details, card information or private booking documents into a public repository.

## Inputs and formulas

All numeric inputs come from the user's quote, cancellation terms, bank/card records or an explicit calculation from those records. Unknown values must remain unresolved; never replace them with zero.

Enter non-negative decimal amounts without currency signs, thousands separators or scientific notation. At most four decimal places are accepted. Use the same three-letter currency label for both quotes. No conversion or automatic currency validation is performed.

Fill original_scope and replacement_scope with an identical scope identifier only after checking dates, pickup and return stations, car class, mileage, extras and payment terms. A matching label is your assertion of comparability, not an automated check of supplier terms.

Set refundable_less_fee to yes only when the original_total is refundable apart from the entered cancellation_fee. Non-refundable bookings need a different model.

- Net saving = original_total - replacement_total - cancellation_fee - other_switching_cost.
- Break-even replacement total = original_total - cancellation_fee - other_switching_cost.
- Additional funds needed before refund = new_payment_before_refund + other_payment_before_refund + additional_hold_before_refund.
- Funding gap = max(0, additional funds needed before refund - available_funds).

other_switching_cost includes all additional permanent costs of switching, excluding the already entered cancellation_fee. other_payment_before_refund includes additional payments due before the old refund arrives; include a cancellation charge here only if it is charged separately now rather than withheld from that refund. Do not double-count a charge.

additional_hold_before_refund is a temporary authorization/deposit that ties up funds in addition to the entered payments. It does not reduce net saving unless an amount is actually retained as a cost, in which case include that cost separately. available_funds must exclude pending refunds and already committed money.

A positive saving is arithmetic under these assumptions. It is not a recommendation to cancel, proof of a confirmed replacement, or a supplier promise about refunds or card acceptance.

## Provenance

The original guide was marked reviewed 2026-10-27 when accessed on 2026-11-15. Its fee examples have deliberately not been embedded. The deposit worksheet is a blank record structure; it does not reproduce historical fee amounts or refund timelines. See SOURCES.md for exact source locations.

## Reuse and contributions

The new calculator, worksheets and documentation in this directory are available under the included MIT license. This license does not cover supplier material, linked websites or other files elsewhere in the parent repository. Corrections should identify the affected input, formula or source; do not add untested discount codes or promotional links.
