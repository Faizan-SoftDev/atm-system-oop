"""
Deposit Transaction for ATM System.

Purpose:
    Implements the deposit operation as a transaction.

OOP Concept:
    INHERITANCE — extends abstract Transaction.
    POLYMORPHISM — implements execute() for deposits.

Business Rules:
    1. Amount must be positive.
    2. Account must be active.
    3. Balance increases by deposit amount.
    4. Transaction record is created and added to account history.

Time Complexity: O(1)
Space Complexity: O(1)
"""

from atm_system.enums import TransactionStatus, TransactionType
from atm_system.exceptions.exceptions import InvalidAmountError
from atm_system.models.account import Account
from atm_system.transactions.transaction import Transaction


class DepositTransaction(Transaction):
    """Deposit transaction — credits amount to an account.

    WHY this class exists:
        Deposit has distinct validation and execution logic from
        withdrawal or transfer. Separate class follows Open/Closed
        Principle — new transaction types can be added without
        modifying existing ones.

    Relationships:
        Inherits from: Transaction
        Operates on: Account (credit)
    """

    def __init__(self, amount: float, account: Account) -> None:
        """Initialize a DepositTransaction.

        Args:
            amount: Amount to deposit (must be positive).
            account: Target account to credit.
        """
        super().__init__(
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            account=account,
            description=f"Deposit of Rs. {amount:,.0f}",
        )

    def execute(self) -> bool:
        """Execute the deposit transaction.

        Algorithm:
            1. Validate amount is positive.
            2. Call account.deposit(amount) — handles active check.
            3. Add this transaction to account history.
            4. Mark transaction as COMPLETED.
            5. Return True.

        If any exception occurs:
            1. Mark transaction as FAILED.
            2. Re-raise the exception.

        Returns:
            True if deposit succeeded.

        Raises:
            InvalidAmountError: If amount is not positive.
            AccountInactiveError: If account is not active.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        try:
            if self._amount <= 0:
                raise InvalidAmountError(
                    f"Deposit amount must be positive (got Rs. {self._amount:,.0f})"
                )

            self._account.deposit(self._amount)
            self._account.add_transaction(self)
            self.mark_completed()
            return True

        except Exception:
            self.mark_failed()
            raise
