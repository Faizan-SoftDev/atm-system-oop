"""
Current Account for ATM System.

Purpose:
    Implements current account-specific business rules:
    - Overdraft limit: Rs. 50,000
    - No minimum balance requirement
    - Balance CAN go negative up to overdraft limit

OOP Concept:
    INHERITANCE — extends Account with current-account-specific rules.
    POLYMORPHISM — implements abstract methods differently from SavingsAccount.

Business Rules:
    1. Overdraft limit: Rs. 50,000.
    2. Balance can be negative up to -Rs. 50,000.
    3. Daily withdrawal limit: Rs. 100,000.
    4. Withdrawal fee: Rs. 40 (lower than savings — different fee structure).
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
    MIN_WITHDRAWAL_AMOUNT,
    OVERDRAFT_LIMIT_CURRENT,
    TRANSFER_FEE,
    WITHDRAWAL_FEE,
)


class CurrentAccount(Account):
    """Current account with overdraft facility.

    WHY this class exists:
        Current accounts serve business customers who may need
        temporary overdraft. Different rules from SavingsAccount.

    KEY DIFFERENCE from SavingsAccount:
        SavingsAccount: balance >= 5000 always (no overdraft)
        CurrentAccount: balance >= -50000 (overdraft allowed)
    """

    def __init__(
        self,
        account_number: str,
        account_holder: str,
        initial_balance: float,
        pin: str,
    ) -> None:
        """Initialize CurrentAccount.

        Args:
            account_number: Unique account identifier.
            account_holder: Name of account holder.
            initial_balance: Starting balance.
            pin: 4-digit PIN string.

        Note: Current accounts have no minimum initial balance requirement.
        """
        super().__init__(
            account_number=account_number,
            account_holder=account_holder,
            initial_balance=initial_balance,
            pin=pin,
            account_type=AccountType.CURRENT,
        )

    def withdraw(self, amount: float) -> None:
        """Withdraw with current-account-specific rules.

        Rules checked in order:
            1. Account is active.
            2. Amount is positive.
            3. Amount >= minimum withdrawal (Rs. 500).
            4. Amount <= maximum per transaction (Rs. 50,000).
            5. Balance - amount >= -overdraft_limit (Rs. -50,000).

        KEY DIFFERENCE from SavingsAccount:
            This allows balance to go negative up to overdraft limit.

        Example:
            Balance = Rs. 10,000
            Overdraft = Rs. 50,000
            Withdrawal = Rs. 30,000
            Result: Balance = -Rs. 20,000  (ALLOWED)

            Balance = Rs. 10,000
            Overdraft = Rs. 50,000
            Withdrawal = Rs. 70,000
            Result: REJECTED (exceeds overdraft)

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

        # Check overdraft limit
        remaining = self._balance - amount
        if remaining < -OVERDRAFT_LIMIT_CURRENT:
            raise InsufficientBalanceError(
                f"Cannot withdraw Rs. {amount:,.0f}. "
                f"Would exceed overdraft limit. "
                f"Available (including overdraft): "
                f"Rs. {self._balance + OVERDRAFT_LIMIT_CURRENT:,.0f}"
            )

        self._balance -= amount

    def calculate_withdrawal_limit(self) -> float:
        """Calculate available withdrawal limit for current account.

        Returns the maximum amount considering overdraft.

        Algorithm:
            1. available = balance + overdraft_limit
            2. limit = min(available, max_per_transaction)
            3. remaining_daily = daily_limit - daily_withdrawn
            4. return min(limit, remaining_daily)

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        available = self._balance + OVERDRAFT_LIMIT_CURRENT
        per_txn_limit = min(available, MAX_WITHDRAWAL_AMOUNT)
        remaining_daily = DAILY_WITHDRAWAL_LIMIT - self.get_daily_withdrawn()
        return min(per_txn_limit, remaining_daily)

    def get_withdrawal_rules(self) -> Dict[str, float]:
        """Return current-account-specific withdrawal rules."""
        return {
            "overdraft_limit": OVERDRAFT_LIMIT_CURRENT,
            "minimum_withdrawal": MIN_WITHDRAWAL_AMOUNT,
            "maximum_per_transaction": MAX_WITHDRAWAL_AMOUNT,
            "daily_limit": DAILY_WITHDRAWAL_LIMIT,
            "withdrawal_fee": WITHDRAWAL_FEE,
        }

    def get_minimum_balance(self) -> float:
        """Return minimum balance for current account.

        Current accounts have no positive minimum balance.
        Minimum effective balance = -overdraft_limit.
        """
        return -OVERDRAFT_LIMIT_CURRENT

    def calculate_fees(self, transaction_type: str) -> float:
        """Calculate fees for current account.

        WHY different from SavingsAccount:
            Demonstrates polymorphism — different account types
            have different fee structures.
        """
        if transaction_type == "WITHDRAWAL":
            return WITHDRAWAL_FEE
        elif transaction_type == "TRANSFER":
            return TRANSFER_FEE
        return 0.0

    def __repr__(self) -> str:
        return (
            f"CurrentAccount("
            f"number={self._account_number!r}, "
            f"holder={self._account_holder!r}, "
            f"balance={self._balance})"
        )
