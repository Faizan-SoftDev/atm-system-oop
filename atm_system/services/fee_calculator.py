"""
Fee Calculator for ATM System.

Purpose:
    Centralizes fee calculation logic for all transaction types.

OOP Concept:
    Single Responsibility — fee logic is isolated.
    Strategy Pattern — fee rules can vary by account type.

    NOTE: Currently fees are also polymorphically calculated within
    Account subclasses via calculate_fees(). This FeeCalculator
    provides an alternative/centralized approach as recommended
    by the master specification.

Business Rules:
    - Withdrawal fee: Rs. 50
    - Transfer fee: Rs. 100
    - Deposit: Free
    - Different account types may override fees (polymorphism).
"""

from typing import Dict, Optional

from atm_system.enums import TransactionType
from atm_system.models.account import Account
from atm_system.utils.validators import TRANSFER_FEE, WITHDRAWAL_FEE


class FeeCalculator:
    """Centralized fee calculation service.

    WHY this class exists:
        The master specification explicitly recommends a FeeCalculator
        class. While Account.calculate_fees() provides polymorphic
        fee calculation, this service offers a centralized alternative
        useful when fee rules need to be checked BEFORE account-type
        is known.

    Business Rule:
        Fee is charged ON TOP of the transaction amount.
        Sender pays the fee in transfers; receiver gets exact amount.
    """

    def __init__(self) -> None:
        """Initialize with default fee schedule."""
        self._fee_schedule: Dict[str, float] = {
            TransactionType.WITHDRAWAL.value: WITHDRAWAL_FEE,
            TransactionType.TRANSFER.value: TRANSFER_FEE,
            TransactionType.DEPOSIT.value: 0.0,
        }

    @property
    def withdrawal_fee(self) -> float:
        """Return default withdrawal fee."""
        return self._fee_schedule[TransactionType.WITHDRAWAL.value]

    @property
    def transfer_fee(self) -> float:
        """Return default transfer fee."""
        return self._fee_schedule[TransactionType.TRANSFER.value]

    def calculate_fee(
        self,
        transaction_type: TransactionType,
        account: Optional[Account] = None,
    ) -> float:
        """Calculate fee for a transaction.

        If an account is provided, delegates to account's polymorphic
        fee calculation (which may differ by account type).

        If no account is provided, uses the default fee schedule.

        Args:
            transaction_type: The type of transaction.
            account: Optional account for polymorphic fee calculation.

        Returns:
            Fee amount in Rs.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if account is not None:
            return account.calculate_fees(transaction_type.value)
        return self._fee_schedule.get(transaction_type.value, 0.0)

    def calculate_total_with_fee(
        self,
        amount: float,
        transaction_type: TransactionType,
        account: Optional[Account] = None,
    ) -> float:
        """Calculate total amount including fee.

        Args:
            amount: Transaction amount.
            transaction_type: Type of transaction.
            account: Optional account for polymorphic fee calculation.

        Returns:
            Total amount = amount + fee.

        Time Complexity: O(1)
        """
        fee = self.calculate_fee(transaction_type, account)
        return amount + fee

    def __repr__(self) -> str:
        return f"FeeCalculator(schedule={self._fee_schedule})"
