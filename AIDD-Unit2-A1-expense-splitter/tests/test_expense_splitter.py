import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from expense_splitter import (  # noqa: E402
    Expense,
    compute_balances,
    settle,
    split_equally,
    to_cents,
)


class ToCentsTests(unittest.TestCase):
    def test_accepts_string_int_and_decimal(self):
        self.assertEqual(to_cents("12.34"), 1234)
        self.assertEqual(to_cents(5), 500)
        self.assertEqual(to_cents(Decimal("0.10")), 10)

    def test_rejects_more_than_two_decimals(self):
        with self.assertRaises(ValueError):
            to_cents("1.005")

    def test_rejects_non_numeric(self):
        with self.assertRaises(ValueError):
            to_cents("abc")

    def test_rejects_non_finite(self):
        with self.assertRaises(ValueError):
            to_cents("NaN")


class SplitEquallyTests(unittest.TestCase):
    def test_even_split(self):
        shares = split_equally("90.00", ["A", "B", "C"])
        self.assertEqual(shares, {"A": Decimal("30.00"), "B": Decimal("30.00"), "C": Decimal("30.00")})

    def test_remainder_cent_goes_to_first_people_in_order(self):
        shares = split_equally("100.00", ["Alice", "Bob", "Carol"])
        self.assertEqual(shares["Alice"], Decimal("33.34"))
        self.assertEqual(shares["Bob"], Decimal("33.33"))
        self.assertEqual(shares["Carol"], Decimal("33.33"))

    def test_shares_always_sum_to_total(self):
        for amount in ["0.01", "0.02", "99.99", "100.00", "1234.57"]:
            for n in range(1, 8):
                people = [f"p{i}" for i in range(n)]
                shares = split_equally(amount, people)
                self.assertEqual(sum(shares.values()), Decimal(amount), f"{amount} / {n}")

    def test_rejects_empty_people(self):
        with self.assertRaises(ValueError):
            split_equally("10.00", [])

    def test_rejects_non_positive_amount(self):
        with self.assertRaises(ValueError):
            split_equally("0", ["A"])
        with self.assertRaises(ValueError):
            split_equally("-5.00", ["A"])

    def test_rejects_duplicate_names(self):
        with self.assertRaises(ValueError):
            split_equally("10.00", ["A", "A"])


class ExpenseTests(unittest.TestCase):
    def test_rejects_empty_description(self):
        with self.assertRaises(ValueError):
            Expense("  ", payer="A", amount="5", participants=("A",))

    def test_rejects_no_participants(self):
        with self.assertRaises(ValueError):
            Expense("Lunch", payer="A", amount="5", participants=())

    def test_rejects_non_positive_amount(self):
        with self.assertRaises(ValueError):
            Expense("Lunch", payer="A", amount="0", participants=("A",))


class ComputeBalancesTests(unittest.TestCase):
    def test_single_expense(self):
        expenses = [Expense("Dinner", "Alice", "90.00", ("Alice", "Bob", "Carol"))]
        balances = compute_balances(expenses)
        self.assertEqual(balances["Alice"], Decimal("60.00"))
        self.assertEqual(balances["Bob"], Decimal("-30.00"))
        self.assertEqual(balances["Carol"], Decimal("-30.00"))

    def test_payer_not_in_participants(self):
        expenses = [Expense("Gift", "Alice", "20.00", ("Bob", "Carol"))]
        balances = compute_balances(expenses)
        self.assertEqual(balances["Alice"], Decimal("20.00"))
        self.assertEqual(balances["Bob"], Decimal("-10.00"))
        self.assertEqual(balances["Carol"], Decimal("-10.00"))

    def test_balances_sum_to_zero_with_awkward_amounts(self):
        expenses = [
            Expense("A", "Alice", "100.00", ("Alice", "Bob", "Carol")),
            Expense("B", "Bob", "0.01", ("Alice", "Bob", "Carol")),
            Expense("C", "Carol", "7.77", ("Alice", "Bob")),
        ]
        balances = compute_balances(expenses)
        self.assertEqual(sum(balances.values()), Decimal("0"))


class SettleTests(unittest.TestCase):
    def test_settlement_clears_all_balances(self):
        balances = compute_balances([
            Expense("Dinner", "Alice", "90.00", ("Alice", "Bob", "Carol")),
            Expense("Taxi", "Bob", "25.50", ("Alice", "Bob", "Carol")),
            Expense("Snacks", "Carol", "10.00", ("Bob", "Carol")),
        ])
        transfers = settle(balances)

        remaining = dict(balances)
        for t in transfers:
            remaining[t.sender] += t.amount
            remaining[t.receiver] -= t.amount
        self.assertTrue(all(v == 0 for v in remaining.values()), remaining)

    def test_no_transfers_when_already_settled(self):
        self.assertEqual(settle({"A": Decimal("0"), "B": Decimal("0")}), [])

    def test_simple_two_person_settlement(self):
        transfers = settle({"Alice": Decimal("10.00"), "Bob": Decimal("-10.00")})
        self.assertEqual(len(transfers), 1)
        self.assertEqual(transfers[0].sender, "Bob")
        self.assertEqual(transfers[0].receiver, "Alice")
        self.assertEqual(transfers[0].amount, Decimal("10.00"))

    def test_rejects_unbalanced_input(self):
        with self.assertRaises(ValueError):
            settle({"Alice": Decimal("10.00"), "Bob": Decimal("-5.00")})


if __name__ == "__main__":
    unittest.main()
