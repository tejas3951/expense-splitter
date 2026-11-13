"""Expense splitter: split shared expenses, compute balances, and settle debts.

All money is handled internally as integer cents to avoid floating-point
drift. Public inputs may be str, int, or Decimal with at most two decimal places.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Sequence

CENT = Decimal("0.01")


def to_cents(value: str | int | Decimal) -> int:
    """Convert a money value to integer cents.

    Raises:
        ValueError: if the value is not a number or has more than 2 decimal places.
    """
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"not a valid amount: {value!r}") from exc
    if not amount.is_finite():
        raise ValueError(f"amount must be finite: {value!r}")
    if amount != amount.quantize(CENT):
        raise ValueError(f"amount must have at most 2 decimal places: {value!r}")
    return int(amount * 100)


def _from_cents(cents: int) -> Decimal:
    return (Decimal(cents) / 100).quantize(CENT)


def split_equally(amount: str | int | Decimal, people: Sequence[str]) -> dict[str, Decimal]:
    """Split an amount equally among people, distributing leftover cents deterministically.

    Each person gets floor(total / n) cents. The remaining cents go one each to the
    first people in the given order, so the shares always sum exactly to the amount.

    Example: 100.00 split three ways -> Alice 33.34, Bob 33.33, Carol 33.33.

    Raises:
        ValueError: if the amount is not positive, people is empty, or names repeat.
    """
    cents = to_cents(amount)
    if cents <= 0:
        raise ValueError("amount must be positive")
    if not people:
        raise ValueError("at least one person is required")
    if len(set(people)) != len(people):
        raise ValueError("participant names must be unique")

    shares_cents = _split_cents(cents, len(people))
    return {name: _from_cents(c) for name, c in zip(people, shares_cents)}


def _split_cents(total_cents: int, n: int) -> list[int]:
    base, remainder = divmod(total_cents, n)
    return [base + 1 if i < remainder else base for i in range(n)]


@dataclass(frozen=True)
class Expense:
    """A single shared expense paid by one person for a group of participants."""

    description: str
    payer: str
    amount: str | int | Decimal
    participants: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("description is required")
        if not self.participants:
            raise ValueError("an expense needs at least one participant")
        if len(set(self.participants)) != len(self.participants):
            raise ValueError("participant names must be unique")
        if to_cents(self.amount) <= 0:
            raise ValueError("amount must be positive")


def compute_balances(expenses: Iterable[Expense]) -> dict[str, Decimal]:
    """Compute each person's net balance across expenses.

    Positive means the person is owed money. Negative means they owe money.
    Balances always sum to zero.
    """
    balances_cents: dict[str, int] = {}
    for expense in expenses:
        total = to_cents(expense.amount)
        balances_cents[expense.payer] = balances_cents.get(expense.payer, 0) + total
        shares = _split_cents(total, len(expense.participants))
        for person, share in zip(expense.participants, shares):
            balances_cents[person] = balances_cents.get(person, 0) - share

    return {name: _from_cents(c) for name, c in sorted(balances_cents.items())}


@dataclass(frozen=True)
class Transfer:
    sender: str
    receiver: str
    amount: Decimal


def settle(balances: dict[str, Decimal]) -> list[Transfer]:
    """Produce a list of transfers that clears all balances.

    Uses a greedy match of the largest debtor against the largest creditor.
    Ties are broken by name so the output is deterministic.

    Raises:
        ValueError: if the balances do not sum to zero.
    """
    balances_cents = {name: to_cents(b) for name, b in balances.items()}
    if sum(balances_cents.values()) != 0:
        raise ValueError("balances must sum to zero")

    creditors = sorted(
        ([name, c] for name, c in balances_cents.items() if c > 0),
        key=lambda item: (-item[1], item[0]),
    )
    debtors = sorted(
        ([name, -c] for name, c in balances_cents.items() if c < 0),
        key=lambda item: (-item[1], item[0]),
    )

    transfers: list[Transfer] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor, owed = debtors[i]
        creditor, due = creditors[j]
        paid = min(owed, due)
        transfers.append(Transfer(debtor, creditor, _from_cents(paid)))
        debtors[i][1] -= paid
        creditors[j][1] -= paid
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1
    return transfers


def main() -> None:
    """Small demo: a dinner shared among three people."""
    expenses = [
        Expense("Dinner", payer="Alice", amount="90.00", participants=("Alice", "Bob", "Carol")),
        Expense("Taxi", payer="Bob", amount="25.50", participants=("Alice", "Bob", "Carol")),
        Expense("Snacks", payer="Carol", amount="10.00", participants=("Bob", "Carol")),
    ]
    balances = compute_balances(expenses)
    print("Balances:")
    for name, balance in balances.items():
        print(f"  {name:<8} {balance:>8}")
    print("Settlements:")
    for t in settle(balances):
        print(f"  {t.sender} pays {t.receiver} {t.amount}")


if __name__ == "__main__":
    main()
