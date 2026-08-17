"""
Savings Account for ATM System.

Purpose:
    Implements savings account-specific business rules:
    - Minimum balance: Rs. 5,000
    - Maximum withdrawal per transaction: Rs. 50,000

OOP Concept:
    INHERITANCE — extends Account with savings-specific rules.
    POLYMORPHISM — implements abstract methods differently from CurrentAccount.
    ENCAPSULATION — rules are enforced internally.

Business Rules:
    1. Balance must never fall below Rs. 5,000.
    2. Maximum withdrawal per transaction: Rs. 50,000.
    3. Daily withdrawal limit: Rs. 100,000.
    4. Withdrawal fee: Rs. 50.
    5. Transfer fee: Rs. 100.
"""

from typing import Dict

from atm_system.enums import AccountType
from atm_system.exceptions.exceptions import InsufficientBalanceError, InvalidAmountError
from atm_system.models.account import Account
from atm_system.utils.validators import (
    DAILY_TRANSFER_LIMIT,
    DAILY_WITHDRAWAL_LIMIT,
    MAX_WITHDRAWAL_AMOUNT,
    MIN_BALANCE_SAVINGS,
    MIN_WITHDRAWAL_AMOUNT,
    TRANSFER_FEE,
    WITHDRAWAL_FEE,
)


class SavingsAccount(Account):
    """Savings account with minimum balance requirement.

    WHY this class exists:
        Savings accounts have different rules from Current accounts.
        Separating them follows Open/Closed Principle — new account types
        can be added without modifying existing code.

    Relationships:
        Inherits from: Account
        Owned by: Customer
        Contains: Transaction history
    """

    def __init__(
        self,
        account_number: str,
        account_holder: str,
        initial_balance: float,
        pin: str,
    ) -> None:
        """Initialize SavingsAccount.

        Args:
            account_number: Unique account identifier.
            account_holder: Name of account holder.
            initial_balance: Starting balance (must be >= MIN_BALANCE_SAVINGS).
            pin: 4-digit PIN string.

        Business Rule:
            Initial balance must meet minimum balance requirement.
        """
        super().__init__(
            account_number=account_number,
            account_holder=account_holder,
            initial_balance=initial_balance,
            pin=pin,
            account_type=AccountType.SAVINGS,
        )

    def withdraw(self, amount: float) -> None:
        """Withdraw with savings-specific rules.

        Rules checked in order:
            1. Account is active.
            2. Amount is positive.
            3. Amount >= minimum withdrawal (Rs. 500).
            4. Amount <= maximum per transaction (Rs. 50,000).
            5. Balance after withdrawal >= minimum balance (Rs. 5,000).

        Args:
            amount: The withdrawal amount (exclusive of fees).

        Raises:
            AccountInactiveError: If account is not active.
            InvalidAmountError: If amount violates min/max rules.
            InsufficientBalanceError: If balance would fall below minimum.

        WHY override Account.withdraw:
            SavingsAccount has the minimum balance constraint that
            the base Account.withdraw does not enforce.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self._check_active()

        if amount <= 0:
            raise InvalidAmountError(
                f"Withdrawal must be positive (got Rs. {amount:,.0f})"
            )
        if amount < MIN_WITHDRAWAL_AMOUNT:
            raise InvalidAmountError(
                f"Minimum withdrawal is Rs. {MIN_WITHDRAWAL_AMOUNT:,.0f} "
                f"(got Rs. {amount:,.0f})"
            )

        # Note: MAX_WITHDRAWAL_AMOUNT is validated at the TransactionService
        # layer before fees are added, so we don't check it here to avoid
        # fee-inclusive amounts (e.g. 50,050) falsely exceeding the limit.

        # Check minimum balance maintenance
        remaining = self._balance - amount
        if remaining < MIN_BALANCE_SAVINGS:
            raise InsufficientBalanceError(
                f"Cannot withdraw Rs. {amount:,.0f}. "
                f"Minimum balance of Rs. {MIN_BALANCE_SAVINGS:,.0f} must be maintained. "
                f"Available for withdrawal: Rs. {max(0, self._balance - MIN_BALANCE_SAVINGS):,.0f}"
            )

        self._balance -= amount

    def calculate_withdrawal_limit(self) -> float:
        """Calculate available withdrawal limit for savings account.

        Returns the maximum amount that can be withdrawn considering:
            - Minimum balance requirement
            - Maximum per-transaction limit
            - Daily limit

        Algorithm:
            1. available = balance - min_balance
            2. limit = min(available, max_per_transaction)
            3. remaining_daily = daily_limit - daily_withdrawn
            4. return min(limit, remaining_daily)

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        available = max(0, self._balance - MIN_BALANCE_SAVINGS)
        per_txn_limit = min(available, MAX_WITHDRAWAL_AMOUNT)
        remaining_daily = DAILY_WITHDRAWAL_LIMIT - self.get_daily_withdrawn()
        return min(per_txn_limit, remaining_daily)

    def get_withdrawal_rules(self) -> Dict[str, float]:
        """Return savings-specific withdrawal rules.

        Returns:
            Dictionary with rule names and values.
        """
        return {
            "minimum_withdrawal": MIN_WITHDRAWAL_AMOUNT,
            "maximum_per_transaction": MAX_WITHDRAWAL_AMOUNT,
            "minimum_balance": MIN_BALANCE_SAVINGS,
            "daily_limit": DAILY_WITHDRAWAL_LIMIT,
            "withdrawal_fee": WITHDRAWAL_FEE,
        }

    def get_minimum_balance(self) -> float:
        """Return minimum balance for savings account."""
        return MIN_BALANCE_SAVINGS

    def calculate_fees(self, transaction_type: str) -> float:
        """Calculate fees for savings account.

        Args:
            transaction_type: "WITHDRAWAL" or "TRANSFER".

        Returns:
            Fee amount in Rs.

        WHY polymorphic:
            Future account types might waive fees based on balance,
            account age, or other criteria.
        """
        if transaction_type == "WITHDRAWAL":
            return WITHDRAWAL_FEE
        elif transaction_type == "TRANSFER":
            return TRANSFER_FEE
        return 0.0

    def __repr__(self) -> str:
        return (
            f"SavingsAccount("
            f"number={self._account_number!r}, "
            f"holder={self._account_holder!r}, "
            f"balance={self._balance})"
        )
