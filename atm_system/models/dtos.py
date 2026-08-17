"""
Data Transfer Objects for ATM System.

Purpose:
    Lightweight data containers for passing data between layers
    without coupling service internals to the UI.

OOP Concept:
    ENCAPSULATION — DTOs are read-only data containers.
    DATACLASS — Python dataclass for concise, immutable-ish models.

WHY dataclasses:
    For simple data containers that mainly hold fields and don't
    need complex behavior, dataclasses reduce boilerplate while
    maintaining type safety and readability.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TransactionResult:
    """Result of a successful transaction.

    WHY dataclass:
        This is a read-only data container passed from service to UI.
        No mutation methods needed. dataclass provides __init__,
        __repr__, __eq__ automatically.
    """

    transaction_id: str
    amount: float
    fee: float
    total_deduction: float
    new_balance: float
    timestamp: datetime
    transaction_type: str
    success: bool = True
    message: str = ""

    @property
    def net_amount(self) -> float:
        """Amount after fee deduction."""
        return self.total_deduction

    def display(self) -> str:
        """Format for console display."""
        lines = [
            f"  Transaction ID : {self.transaction_id}",
            f"  Type           : {self.transaction_type}",
            f"  Amount         : Rs. {self.amount:,.0f}",
        ]
        if self.fee > 0:
            lines.append(f"  Fee            : Rs. {self.fee:,.0f}")
            lines.append(f"  Total Deducted : Rs. {self.total_deduction:,.0f}")
        lines.append(f"  New Balance    : Rs. {self.new_balance:,.0f}")
        return "\n".join(lines)


@dataclass
class AccountInfo:
    """Account information DTO for display.

    WHY dataclass:
        Simple data transfer from AccountService to ATM UI.
        Avoids exposing internal Account object directly.
    """

    account_number: str
    account_holder: str
    balance: float
    account_type: str
    status: str
    minimum_balance: float = 0.0
    overdraft_limit: float = 0.0

    def display(self) -> str:
        """Format for console display."""
        lines = [
            f"  Account Number : {self.account_number}",
            f"  Account Holder : {self.account_holder}",
            f"  Account Type   : {self.account_type}",
            f"  Status         : {self.status}",
            f"  Balance        : Rs. {self.balance:,.0f}",
        ]
        if self.overdraft_limit > 0:
            lines.append(f"  Overdraft Limit: Rs. {self.overdraft_limit:,.0f}")
        elif self.minimum_balance > 0:
            lines.append(f"  Min Balance    : Rs. {self.minimum_balance:,.0f}")
        return "\n".join(lines)


@dataclass
class ATMStatus:
    """ATM machine status DTO.

    WHY dataclass:
        Read-only snapshot of ATM state for display/diagnostics.
    """

    total_cash: float
    notes: dict = field(default_factory=dict)
    is_operational: bool = True

    def display(self) -> str:
        """Format for console display."""
        lines = ["  ATM Status:"]
        for denom in sorted(self.notes.keys(), reverse=True):
            count = self.notes[denom]
            total = denom * count
            lines.append(f"    Rs. {denom:>5,} x {count:>3} = Rs. {total:>8,.0f}")
        lines.append(f"  {'Total':>16} = Rs. {self.total_cash:>8,.0f}")
        return "\n".join(lines)
