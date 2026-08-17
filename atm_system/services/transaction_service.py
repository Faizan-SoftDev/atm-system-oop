"""
Transaction Service for ATM System.

Purpose:
    Orchestrates financial transactions by creating and executing
    the appropriate transaction objects.

OOP Concept:
    Service Layer — business logic separated from UI and models.
    Factory Pattern — creates appropriate transaction type.
    Single Responsibility — only manages transaction execution.

Business Rules:
    - Validates all preconditions before creating transactions.
    - Delegates execution to transaction objects.
    - Handles rollback on failure.
"""

from typing import Optional

from atm_system.enums import TransactionType
from atm_system.exceptions.exceptions import (
    DailyLimitExceededError,
    InvalidAmountError,
    SameAccountTransferError,
)
from atm_system.models.account import Account
from atm_system.services.cash_dispenser import CashDispenser
from atm_system.transactions.deposit import DepositTransaction
from atm_system.transactions.withdrawal import WithdrawalTransaction
from atm_system.transactions.transfer import TransferTransaction
from atm_system.utils.validators import validate_amount, validate_withdrawal_amount


class TransactionService:
    """Service for executing financial transactions.

    Dependencies:
        CashDispenser — for withdrawal operations.

    WHY this class exists:
        Creating and executing transactions involves multiple validation
        steps, fee calculations, and rollback logic. Centralizing this
        in a service prevents duplication across ATM menu options.
    """

    def __init__(self, cash_dispenser: CashDispenser) -> None:
        """Initialize with a cash dispenser reference.

        Args:
            cash_dispenser: The ATM's cash dispenser.
        """
        self._cash_dispenser: CashDispenser = cash_dispenser

    def deposit(self, account: Account, amount: float) -> DepositTransaction:
        """Execute a deposit transaction.

        Algorithm:
            1. Validate amount.
            2. Create DepositTransaction.
            3. Execute (handles account debit + history).
            4. Return completed transaction.

        Returns:
            The completed DepositTransaction.

        Raises:
            InvalidAmountError: If amount is invalid.
            AccountInactiveError: If account is inactive.

        Time Complexity: O(1)
        """
        validate_amount(amount, "Deposit")
        txn = DepositTransaction(amount=amount, account=account)
        txn.execute()
        return txn

    def withdraw(self, account: Account, amount: float) -> WithdrawalTransaction:
        """Execute a withdrawal transaction.

        Algorithm:
            1. Validate withdrawal amount (min/max).
            2. Create WithdrawalTransaction.
            3. Execute (validates balance, ATM cash, denominations).
            4. Return completed transaction.

        Returns:
            The completed WithdrawalTransaction.

        Raises:
            InvalidAmountError: If amount is invalid.
            InsufficientBalanceError: If insufficient balance.
            DailyLimitExceededError: If daily limit exceeded.
            InsufficientATMFundsError: If ATM cannot dispense.

        Time Complexity: O(d) for denomination calculation
        """
        validate_withdrawal_amount(amount)
        txn = WithdrawalTransaction(
            amount=amount,
            account=account,
            cash_dispenser=self._cash_dispenser,
        )
        txn.execute()
        return txn

    def transfer(
        self,
        sender_account: Account,
        receiver_account: Account,
        amount: float,
    ) -> TransferTransaction:
        """Execute a transfer transaction.

        Algorithm:
            1. Validate amount.
            2. Validate sender != receiver.
            3. Create TransferTransaction.
            4. Execute atomically.
            5. Return completed transaction.

        Returns:
            The completed TransferTransaction.

        Raises:
            SameAccountTransferError: If sender == receiver.
            DailyLimitExceededError: If daily limit exceeded.
            InsufficientBalanceError: If sender lacks funds.

        Time Complexity: O(1)
        """
        validate_amount(amount, "Transfer")

        if sender_account.account_number == receiver_account.account_number:
            raise SameAccountTransferError(
                "Cannot transfer to the same account"
            )

        txn = TransferTransaction(
            amount=amount,
            sender_account=sender_account,
            receiver_account=receiver_account,
        )
        txn.execute()
        return txn
