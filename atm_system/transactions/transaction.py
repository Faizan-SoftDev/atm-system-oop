"""
Abstract Transaction base class for ATM System.

Purpose:
    Defines the common structure and interface for all financial transactions.

OOP Concepts:
    ABSTRACTION — Transaction defines what every transaction must have,
    without specifying how each type executes.
    ENCAPSULATION — Transaction ID, status, and timestamp are controlled.
    INHERITANCE — DepositTransaction, WithdrawalTransaction, TransferTransaction
    extend this class.

Business Rule:
    Every financial operation creates a Transaction record with:
    - Unique ID (TXN-YYYYMMDD-XXXXXX)
    - Amount
    - Date/time
    - Status (PENDING → COMPLETED / FAILED / CANCELLED)
    - Account reference
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from atm_system.enums import TransactionStatus, TransactionType
from atm_system.utils.transaction_id import TransactionIdGenerator

if TYPE_CHECKING:
    from atm_system.models.account import Account


class Transaction(ABC):
    """Abstract base class for all financial transactions.

    WHY Abstract:
        Different transaction types have fundamentally different
        execution logic. Making Transaction abstract prevents
        instantiating an incomplete transaction.

    ATTRIBUTES:
        _transaction_id: Unique identifier (auto-generated)
        _amount: Transaction amount
        _transaction_type: DEPOSIT, WITHDRAWAL, or TRANSFER
        _status: Current status
        _timestamp: When the transaction was created
        _account: Primary account involved
        _description: Human-readable description
    """

    _id_generator = TransactionIdGenerator()

    def __init__(
        self,
        amount: float,
        transaction_type: TransactionType,
        account: Account,
        description: str = "",
    ) -> None:
        """Initialize a Transaction.

        Args:
            amount: Transaction amount.
            transaction_type: Type of transaction.
            account: Primary account involved.
            description: Optional human-readable description.

        Business Rule:
            Transaction ID is auto-generated, never hard-coded.
            Initial status is PENDING until execute() succeeds.
        """
        self._transaction_id: str = Transaction._id_generator.generate()
        self._amount: float = amount
        self._transaction_type: TransactionType = transaction_type
        self._status: TransactionStatus = TransactionStatus.PENDING
        self._timestamp: datetime = datetime.now()
        self._account: Account = account
        self._description: str = description

    # ── Properties ──

    @property
    def transaction_id(self) -> str:
        return self._transaction_id

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def transaction_type(self) -> TransactionType:
        return self._transaction_type

    @property
    def status(self) -> TransactionStatus:
        return self._status

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def account(self) -> Account:
        return self._account

    @property
    def description(self) -> str:
        return self._description

    # ── Status Management ──

    def mark_completed(self) -> None:
        """Mark transaction as completed."""
        self._status = TransactionStatus.COMPLETED

    def mark_failed(self) -> None:
        """Mark transaction as failed."""
        self._status = TransactionStatus.FAILED

    def mark_cancelled(self) -> None:
        """Mark transaction as cancelled."""
        self._status = TransactionStatus.CANCELLED

    # ── Core Operation (polymorphic) ──

    @abstractmethod
    def execute(self) -> bool:
        """Execute the transaction.

        WHY abstract:
            Each transaction type has different execution logic:
            - Deposit: Credit amount to account.
            - Withdrawal: Debit amount, check rules, check ATM cash.
            - Transfer: Debit sender, credit receiver atomically.

        Returns:
            True if transaction succeeded, False otherwise.

        Raises:
            Various ATMError subclasses for business rule violations.
        """
        ...

    # ── Formatting ──

    def get_amount_display(self) -> str:
        """Return formatted amount with +/- prefix.

        Algorithm:
            1. Check transaction type.
            2. Return "+Rs. X" for deposits.
            3. Return "-Rs. X" for withdrawals/transfers.

        Time Complexity: O(1)
        """
        sign = "+" if self._transaction_type == TransactionType.DEPOSIT else "-"
        return f"{sign}Rs. {self._amount:,.0f}"

    def get_date_display(self) -> str:
        """Return formatted date for statement display.

        Format: DD-Mon (e.g., 17-Aug)

        Time Complexity: O(1)
        """
        return self._timestamp.strftime("%d-%b")

    def get_type_display(self) -> str:
        """Return transaction type as display string."""
        return self._transaction_type.value.title()

    # ── Representation ──

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id={self._transaction_id!r}, "
            f"type={self._transaction_type.value}, "
            f"amount={self._amount}, "
            f"status={self._status.value})"
        )
