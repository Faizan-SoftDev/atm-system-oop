"""
Abstract Account base class for ATM System.

Purpose:
    Defines the common interface and shared behavior for all account types.
    Enforces that subclasses implement type-specific rules.

OOP Concepts:
    ABSTRACTION — Account defines what every account MUST do,
    without specifying HOW each account type does it.
    ENCAPSULATION — Balance, PIN, and status are protected.
    INHERITANCE — SavingsAccount and CurrentAccount extend this class.
    POLYMORPHISM — calculate_withdrawal_limit() and get_withdrawal_rules()
    behave differently per subclass.

Class Relationships:
    Parent of: SavingsAccount, CurrentAccount
    Composition: Account HAS a list of Transactions
    Association: Account BELONGS TO a Customer

Protected Data:
    _account_number: Unique identifier
    _account_holder: Name of account owner
    _balance: Current balance (only modified via deposit/withdraw)
    _pin: Authentication PIN (never exposed in plain text)
    _status: Account status enum
    _transaction_history: List of Transaction objects
    _account_type: Type of account (SAVINGS/CURRENT)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from atm_system.enums import AccountStatus, AccountType, TransactionStatus
from atm_system.exceptions.exceptions import (
    AccountInactiveError,
    InsufficientBalanceError,
    InvalidAmountError,
)

if TYPE_CHECKING:
    from atm_system.transactions.transaction import Transaction


class Account(ABC):
    """Abstract base class for all bank accounts.

    WHY Abstract:
        Account alone is incomplete — it cannot enforce specific rules
        for minimum balance, overdraft, etc. Making it abstract ensures
        no one instantiates a generic Account, only concrete subclasses
        that implement all required behavior.

    WHY these attributes are protected:
        Balance and PIN must never be modified directly.
        All changes go through controlled methods with validation.
    """

    def __init__(
        self,
        account_number: str,
        account_holder: str,
        initial_balance: float,
        pin: str,
        account_type: AccountType,
    ) -> None:
        """Initialize an Account with required fields.

        Args:
            account_number: Unique account identifier.
            account_holder: Name of the account holder.
            initial_balance: Starting balance.
            pin: 4-digit PIN string.
            account_type: SAVINGS or CURRENT.
        """
        self._account_number: str = account_number
        self._account_holder: str = account_holder
        self._balance: float = initial_balance
        self._pin: str = pin
        self._status: AccountStatus = AccountStatus.ACTIVE
        self._account_type: AccountType = account_type
        self._transaction_history: List[Transaction] = []
        self._daily_withdrawal_amount: float = 0.0
        self._daily_transfer_amount: float = 0.0
        self._last_withdrawal_date: Optional[str] = None
        self._last_transfer_date: Optional[str] = None

    # ── Properties (read-only access for encapsulation) ──

    @property
    def account_number(self) -> str:
        """Return account number (read-only)."""
        return self._account_number

    @property
    def account_holder(self) -> str:
        """Return account holder name (read-only)."""
        return self._account_holder

    @property
    def balance(self) -> float:
        """Return current balance (read-only).

        WHY: Balance must never be set directly.
        All changes go through deposit() or withdraw().
        """
        return self._balance

    @property
    def status(self) -> AccountStatus:
        """Return account status (read-only)."""
        return self._status

    @property
    def account_type(self) -> AccountType:
        """Return account type (read-only)."""
        return self._account_type

    @property
    def transaction_history(self) -> List[Transaction]:
        """Return a copy of transaction history.

        WHY: Returns a copy to prevent external modification.
        """
        return list(self._transaction_history)

    # ── Status Management ──

    def activate(self) -> None:
        """Set account status to ACTIVE."""
        self._status = AccountStatus.ACTIVE

    def freeze(self) -> None:
        """Set account status to FROZEN."""
        self._status = AccountStatus.FROZEN

    def close(self) -> None:
        """Set account status to CLOSED."""
        self._status = AccountStatus.CLOSED

    def _check_active(self) -> None:
        """Raise if account is not active.

        Called before every transaction to enforce business rule:
        Only ACTIVE accounts can perform operations.

        Raises:
            AccountInactiveError: If status is not ACTIVE.
        """
        if self._status != AccountStatus.ACTIVE:
            raise AccountInactiveError(
                f"Account {self._account_number} is {self._status.value}. "
                "Only ACTIVE accounts can perform transactions."
            )

    # ── PIN Management ──

    def verify_pin(self, pin: str) -> bool:
        """Verify if the provided PIN matches.

        Args:
            pin: The PIN to verify.

        Returns:
            True if PIN matches, False otherwise.

        WHY: PIN comparison is encapsulated inside Account.
        The PIN string is never exposed outside this class.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return self._pin == pin

    def change_pin(self, old_pin: str, new_pin: str) -> None:
        """Change the account PIN after verifying old PIN.

        Args:
            old_pin: Current PIN for verification.
            new_pin: New PIN to set.

        Raises:
            InvalidAmountError → InvalidPINError: If old PIN is wrong.

        Business Rule:
            1. Old PIN must be correct.
            2. New PIN must pass validation (handled by caller/service).
        """
        if not self.verify_pin(old_pin):
            from atm_system.exceptions.exceptions import InvalidPINError
            raise InvalidPINError("Old PIN is incorrect")
        self._pin = new_pin

    # ── Core Operations ──

    def deposit(self, amount: float) -> None:
        """Deposit amount into account.

        Args:
            amount: Positive deposit amount.

        Business Rules:
            1. Account must be active.
            2. Amount must be positive.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self._check_active()
        if amount <= 0:
            raise InvalidAmountError(f"Deposit must be positive (got Rs. {amount:,.0f})")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        """Withdraw amount from account.

        Args:
            amount: Withdrawal amount.

        WHY abstractmethod:
            Each account type enforces different withdrawal rules.
            SavingsAccount checks minimum balance.
            CurrentAccount checks overdraft limit.

        MUST be overridden by subclasses.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self._check_active()
        if amount <= 0:
            raise InvalidAmountError(f"Withdrawal must be positive (got Rs. {amount:,.0f})")
        if self._balance < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance. Available: Rs. {self._balance:,.0f}, "
                f"Requested: Rs. {amount:,.0f}"
            )
        self._balance -= amount

    def add_transaction(self, transaction: Transaction) -> None:
        """Add a completed transaction to history.

        Args:
            transaction: The Transaction object to record.

        WHY: Transaction history is append-only during normal operations.
        """
        self._transaction_history.append(transaction)

    # ── Daily Limit Management ──

    def _get_today(self) -> str:
        """Return today's date as YYYY-MM-DD string."""
        return datetime.now().strftime("%Y-%m-%d")

    def _reset_daily_limits_if_new_day(self) -> None:
        """Reset daily counters when calendar date changes.

        Business Rule:
            Daily withdrawal and transfer limits reset at midnight.
            The user should not need to manually reset limits.

        Algorithm:
            1. Get today's date string.
            2. Compare with stored last dates.
            3. If different, reset the corresponding counter.
        """
        today = self._get_today()

        if self._last_withdrawal_date and self._last_withdrawal_date != today:
            self._daily_withdrawal_amount = 0.0
        if self._last_transfer_date and self._last_transfer_date != today:
            self._daily_transfer_amount = 0.0

    def get_daily_withdrawn(self) -> float:
        """Return the total amount withdrawn today."""
        self._reset_daily_limits_if_new_day()
        if self._get_today() != self._last_withdrawal_date:
            return 0.0
        return self._daily_withdrawal_amount

    def get_daily_transferred(self) -> float:
        """Return the total amount transferred today."""
        self._reset_daily_limits_if_new_day()
        if self._get_today() != self._last_transfer_date:
            return 0.0
        return self._daily_transfer_amount

    def record_daily_withdrawal(self, amount: float) -> None:
        """Record a withdrawal for daily limit tracking.

        Args:
            amount: The withdrawal amount (including fees if applicable).
        """
        today = self._get_today()
        if self._last_withdrawal_date != today:
            self._daily_withdrawal_amount = 0.0
        self._daily_withdrawal_amount += amount
        self._last_withdrawal_date = today

    def record_daily_transfer(self, amount: float) -> None:
        """Record a transfer for daily limit tracking.

        Args:
            amount: The transfer amount (including fees if applicable).
        """
        today = self._get_today()
        if self._last_transfer_date != today:
            self._daily_transfer_amount = 0.0
        self._daily_transfer_amount += amount
        self._last_transfer_date = today

    # ── Polymorphic Methods (must be overridden) ──

    @abstractmethod
    def calculate_withdrawal_limit(self) -> float:
        """Return the maximum withdrawal amount for this account type.

        WHY abstract:
            SavingsAccount returns: MIN(balance - min_balance, max_per_transaction)
            CurrentAccount returns: balance + overdraft_limit

        OOP: POLYMORPHISM — caller does not need to know the concrete type.
        """
        ...

    @abstractmethod
    def get_withdrawal_rules(self) -> dict:
        """Return account-type-specific withdrawal rules as a dictionary.

        WHY: Useful for display and validation without exposing internals.
        """
        ...

    @abstractmethod
    def get_minimum_balance(self) -> float:
        """Return the minimum balance requirement for this account type."""
        ...

    @abstractmethod
    def calculate_fees(self, transaction_type: str) -> float:
        """Calculate fees for a given transaction type.

        WHY abstract:
            Different account types may have different fee structures.
            Savings might waive fees above a certain balance.
        """
        ...

    # ── Representation ──

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"number={self._account_number!r}, "
            f"holder={self._account_holder!r}, "
            f"balance={self._balance}, "
            f"type={self._account_type.value}, "
            f"status={self._status.value})"
        )
