"""Compare matching rental quotes using explicit user-supplied amounts only."""
import argparse
import csv
import io
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

FIELDS = [
    "comparison_id", "original_scope", "replacement_scope",
    "original_currency", "replacement_currency", "original_total",
    "replacement_total", "cancellation_fee", "other_switching_cost",
    "refundable_less_fee", "new_payment_before_refund",
    "other_payment_before_refund", "additional_hold_before_refund",
    "available_funds"
]
AMOUNTS = [
    "original_total", "replacement_total", "cancellation_fee",
    "other_switching_cost", "new_payment_before_refund",
    "other_payment_before_refund", "additional_hold_before_refund",
    "available_funds"
]

def amount(value, field):
    value = str(value).strip()
    if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,4})?", value):
        raise ValueError(f"{field}: provide a known non-negative plain decimal "
                         "with at most four decimal places; unknown is not zero")
    return Decimal(value)

def display(value):
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text

def compare(row):
    for field in FIELDS:
        if not str(row.get(field, "")).strip():
            raise ValueError(f"{field}: required")
    if row["original_scope"].strip() != row["replacement_scope"].strip():
        raise ValueError("The rental scopes differ; a like-for-like saving is unresolved")
    old_currency = row["original_currency"].strip()
    new_currency = row["replacement_currency"].strip()
    if not re.fullmatch(r"[A-Z]{3}", old_currency) or old_currency != new_currency:
        raise ValueError("Use the same three-letter currency label; no conversion is performed")
    if row["refundable_less_fee"].strip().lower() != "yes":
        raise ValueError("This model requires the original total to be refundable apart from the entered fee")
    values = {key: amount(row[key], key) for key in AMOUNTS}
    if values["cancellation_fee"] > values["original_total"]:
        raise ValueError("Cancellation fee exceeds original total; this model does not cover that case")
    saving = (values["original_total"] - values["replacement_total"]
              - values["cancellation_fee"] - values["other_switching_cost"])
    break_even = (values["original_total"] - values["cancellation_fee"]
                  - values["other_switching_cost"])
    cash_needed = (values["new_payment_before_refund"]
                   + values["other_payment_before_refund"]
                   + values["additional_hold_before_refund"])
    funding_gap = max(Decimal("0"), cash_needed - values["available_funds"])
    return {
        "comparison_id": row["comparison_id"],
        "currency": old_currency,
        "net_saving": display(saving),
        "break_even_replacement_total": display(break_even),
        "additional_funds_needed_before_refund": display(cash_needed),
        "funding_gap": display(funding_gap),
        "positive_saving": saving > 0,
        "assumptions": [
            "Same rental scope and currency, confirmed by the input author",
            "Original total refundable apart from the entered fee",
            "All permanent switching costs entered",
            "Pending refunds excluded from available funds",
            "Temporary holds are funding needs, not permanent costs"
        ]
    }

def read_rows(text):
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), strict=True)
    if reader.fieldnames != FIELDS:
        raise ValueError("CSV header must match --template exactly")
    rows = list(reader)
    if not rows:
        raise ValueError("No comparisons supplied; complete the template with your own quote evidence")
    seen = set()
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("CSV row has a different number of fields from the header")
        key = row["comparison_id"]
        if key in seen:
            raise ValueError("comparison_id must be unique")
        seen.add(key)
    return rows

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", nargs="?")
    parser.add_argument("--template", action="store_true", help="Print an empty CSV header")
    args = parser.parse_args(argv)
    if args.template:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(FIELDS)
        return 0
    if not args.csv_file:
        parser.error("provide a CSV file or use --template")
    try:
        rows = read_rows(Path(args.csv_file).read_text(encoding="utf-8-sig"))
        # Validate every row before printing any comparison.
        results = [compare(row) for row in rows]
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(results, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
