"""
Transfer Transaction for ATM System.

Purpose:
    Implements the transfer operation as an atomic transaction
    that debits the sender and credits the receiver.

OOP Concept:
    INHERITANCE — extends abstract Transaction.
    POLYMORPHISM — implements execute() for transfers.
    COMPOSITION — Transaction references two accounts.

Business Rules:
    1. Sender and receiver must be different accounts.
    2. Both accounts must be active.
    3. Amount must be positive.
    4. Sender must have sufficient balance (including fees).
    5. Daily transfer limit: Rs. 500,000.
    6. Transfer fee: Rs. 100 (deducted from sender).
    7. Receiver gets the exact transfer amount (no fee deduction).
    8. TWO transaction records are created (one per account).
    9. Transfer is ATOMIC — all-or-nothing.

ATOMICITY (in-memory):
    We track both state changes and rollback on failure.
    In production, this would use a database transaction.

Time Complexity: O(1)
Space Complexity: O(1) — aside from two transaction objects
"""

from __future__ import annotations

from typing import Optional

from atm_system.enums import TransactionStatus, TransactionType
from atm_system.exceptions.exceptions import (
    DailyLimitExceededError,
    InvalidAmountError,
    SameAccountTransferError,
)
from atm_system.models.account import Account
from atm_system.transactions.transaction import Transaction
from atm_system.utils.validators import DAILY_TRANSFER_LIMIT, TRANSFER_FEE


class TransferTransaction(Transaction):
    """Transfer transaction — moves money between two accounts.

    WHY this class exists:
        Transfer is the most complex single operation:
        - Two accounts involved (sender + receiver)
        - Atomicity requirement (all-or-nothing)
        - Two transaction records needed
        - Fee from sender only
        - Daily transfer limit tracking

    ATOMICITY Strategy (in-memory):
        1. Save sender's balance before.
        2. Save receiver's balance before.
        3. Execute sender debit.
        4. Execute receiver credit.
        5. If anything fails after step 3, rollback both balances.

    NOTE: In production, a database transaction (BEGIN/COMMIT/ROLLBACK)
    would handle this atomically with ACID guarantees.
    """

    def __init__(
        self,
        amount: float,
        sender_account: Account,
        receiver_account: Account,
    ) -> None:
        """Initialize a TransferTransaction.

        Args:
            amount: Amount to transfer (exclusive of fee).
            sender_account: Account to debit.
            receiver_account: Account to credit.
        """
        super().__init__(
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            account=sender_account,
            description=f"Transfer of Rs. {amount:,.0f} to {receiver_account.account_number}",
        )
        self._sender_account: Account = sender_account
        self._receiver_account: Account = receiver_account
        self._receiver_transaction: Optional[Transaction] = None

    @property
    def sender_account(self) -> Account:
        return self._sender_account

    @property
    def receiver_account(self) -> Account:
        return self._receiver_account

    @property
    def receiver_transaction(self) -> Optional[Transaction]:
        """The transaction record created for the receiver account."""
        return self._receiver_transaction

    @property
    def total_sender_deduction(self) -> float:
        """Total deducted from sender = transfer amount + fee.

        Time Complexity: O(1)
        """
        return self._amount + TRANSFER_FEE

    def execute(self) -> bool:
        """Execute the transfer atomically.

        Algorithm (step-by-step):
            1. Validate: sender != receiver.
            2. Validate: amount is positive.
            3. Validate: both accounts are active.
            4. Check daily transfer limit on sender.
            5. Calculate total_sender_deduction = amount + fee.
            6. Save sender balance (for rollback).
            7. Save receiver balance (for rollback).
            8. Debit sender: sender.withdraw(total_sender_deduction).
            9. Credit receiver: receiver.deposit(amount).
            10. Record daily transfer on sender.
            11. Create transaction records for both accounts.
            12. Mark both transactions COMPLETED.
            13. Return True.

        ROLLBACK:
            If step 9 fails, restore both balances to saved values.

        Returns:
            True if transfer succeeded.

        Raises:
            SameAccountTransferError: If sender == receiver.
            InvalidAmountError: If amount is not positive.
            DailyLimitExceededError: If daily limit exceeded.
            AccountInactiveError: If either account is inactive.
            InsufficientBalanceError: If sender lacks funds.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        try:
            # Validation
            if self._sender_account.account_number == self._receiver_account.account_number:
                raise SameAccountTransferError(
                    "Cannot transfer to the same account"
                )
            if self._amount <= 0:
                raise InvalidAmountError(
                    f"Transfer amount must be positive (got Rs. {self._amount:,.0f})"
                )

            self._sender_account._check_active()
            self._receiver_account._check_active()

            # Check daily transfer limit
            daily_transferred = self._sender_account.get_daily_transferred()
            if daily_transferred + self._amount > DAILY_TRANSFER_LIMIT:
                raise DailyLimitExceededError(
                    f"Daily transfer limit of Rs. {DAILY_TRANSFER_LIMIT:,.0f} would be exceeded. "
                    f"Already transferred today: Rs. {daily_transferred:,.0f}. "
                    f"This transfer: Rs. {self._amount:,.0f}"
                )

            total_sender_deduction = self._amount + TRANSFER_FEE

            # Save state for rollback
            sender_balance_before = self._sender_account.balance
            receiver_balance_before = self._receiver_account.balance

            try:
                # Step 1: Debit sender
                self._sender_account.withdraw(total_sender_deduction)

                # Step 2: Credit receiver
                self._receiver_account.deposit(self._amount)
            except Exception:
                # ROLLBACK: Restore both balances
                self._sender_account._balance = sender_balance_before
                self._receiver_account._balance = receiver_balance_before
                raise

            # Record daily transfer
            self._sender_account.record_daily_transfer(total_sender_deduction)

            # Create sender transaction record
            self._sender_account.add_transaction(self)
            self.mark_completed()

            # Create receiver transaction record (same amount, different sign)
            from atm_system.transactions.deposit import DepositTransaction
            receiver_txn = DepositTransaction(
                amount=self._amount,
                account=self._receiver_account,
            )
            receiver_txn.mark_completed()
            self._receiver_account.add_transaction(receiver_txn)
            self._receiver_transaction = receiver_txn

            return True

        except Exception:
            self.mark_failed()
            raise

    def __repr__(self) -> str:
        return (
            f"TransferTransaction("
            f"id={self._transaction_id!r}, "
            f"amount={self._amount}, "
            f"sender={self._sender_account.account_number!r}, "
            f"receiver={self._receiver_account.account_number!r}, "
            f"status={self._status.value})"
        )
