"""Synthetic software fixtures only: these are not rental quotes or provider fees."""
import unittest
from compare_quotes import compare, read_rows, FIELDS
import csv
import io

def fixture(**changes):
    row = dict(zip(FIELDS, [
        "test-only", "same-verified-trip", "same-verified-trip",
        "USD", "USD", "200.10", "150.05", "20", "5",
        "yes", "150.05", "0", "30", "100"
    ]))
    row.update(changes)
    return row

class ComparisonTests(unittest.TestCase):
    def test_exact_decimal_and_hold_separation(self):
        result = compare(fixture())
        self.assertEqual(result["net_saving"], "25.05")
        self.assertEqual(result["additional_funds_needed_before_refund"], "180.05")
        self.assertEqual(result["funding_gap"], "80.05")

    def test_break_even_and_no_positive_saving(self):
        result = compare(fixture(replacement_total="175.10"))
        self.assertEqual(result["net_saving"], "0")
        self.assertFalse(result["positive_saving"])

    def test_negative_saving_is_not_hidden(self):
        self.assertEqual(compare(fixture(replacement_total="201"))["net_saving"], "-25.9")

    def test_currency_and_scope_must_match(self):
        for changes in [{"replacement_currency": "EUR"}, {"replacement_scope": "different-trip"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                compare(fixture(**changes))

    def test_unknown_and_invalid_amounts_fail(self):
        for invalid in ["", "unknown", "-1", "NaN", "Infinity", "1e3", "1.00001"]:
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                compare(fixture(cancellation_fee=invalid))

    def test_non_refundable_is_not_assumed(self):
        with self.assertRaises(ValueError):
            compare(fixture(refundable_less_fee="no"))

    def test_quoted_csv_round_trip(self):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(fixture(comparison_id='private,"quoted"'))
        self.assertEqual(read_rows(output.getvalue())[0]["comparison_id"], 'private,"quoted"')

    def test_empty_template_and_duplicate_ids_fail(self):
        with self.assertRaises(ValueError):
            read_rows(",".join(FIELDS) + "\n")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(fixture())
        writer.writerow(fixture())
        with self.assertRaises(ValueError):
            read_rows(output.getvalue())

if __name__ == "__main__":
    unittest.main()
