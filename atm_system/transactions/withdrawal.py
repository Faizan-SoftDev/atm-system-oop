"""
Withdrawal Transaction for ATM System.

Purpose:
    Implements the withdrawal operation as a transaction.

OOP Concept:
    INHERITANCE — extends abstract Transaction.
    POLYMORPHISM — implements execute() for withdrawals.

Business Rules:
    1. Amount must be positive.
    2. Amount must be >= Rs. 500 (minimum withdrawal).
    3. Amount must be <= Rs. 50,000 (maximum per transaction).
    4. Account must be active.
    5. Sufficient balance (account-type-specific rules).
    6. ATM must have enough cash AND correct denominations.
    7. Daily withdrawal limit must not be exceeded.
    8. Withdrawal fee is charged.

Time Complexity: O(d) where d = number of denominations
Space Complexity: O(d) for the denomination result
"""

from atm_system.enums import TransactionStatus, TransactionType
from atm_system.exceptions.exceptions import (
    DailyLimitExceededError,
    InsufficientATMFundsError,
)
from atm_system.models.account import Account
from atm_system.services.cash_dispenser import CashDispenser
from atm_system.transactions.transaction import Transaction
from atm_system.utils.validators import DAILY_WITHDRAWAL_LIMIT, WITHDRAWAL_FEE


class WithdrawalTransaction(Transaction):
    """Withdrawal transaction — debits amount from an account.

    WHY this class exists:
        Withdrawal involves ATM cash management, denomination checks,
        fee calculation, and daily limit tracking — complex logic
        that belongs in its own class.

    Key Responsibility:
        This class orchestrates the withdrawal by delegating:
        - Cash dispensing → CashDispenser
        - Account debit → Account.withdraw()
        - Fee calculation → Account.calculate_fees()
    """

    def __init__(
        self,
        amount: float,
        account: Account,
        cash_dispenser: CashDispenser,
    ) -> None:
        """Initialize a WithdrawalTransaction.

        Args:
            amount: Amount to withdraw (exclusive of fees).
            account: Source account to debit.
            cash_dispenser: ATM's cash dispenser for denomination check.
        """
        super().__init__(
            amount=amount,
            transaction_type=TransactionType.WITHDRAWAL,
            account=account,
            description=f"Withdrawal of Rs. {amount:,.0f}",
        )
        self._cash_dispenser: CashDispenser = cash_dispenser

    @property
    def total_deduction(self) -> float:
        """Total amount deducted including fee.

        Algorithm:
            1. fee = account.calculate_fees("WITHDRAWAL")
            2. total = amount + fee
            3. return total

        Time Complexity: O(1)
        """
        fee = self._account.calculate_fees(TransactionType.WITHDRAWAL.value)
        return self._amount + fee

    def execute(self) -> bool:
        """Execute the withdrawal transaction.

        Algorithm (step-by-step):
            1. Validate amount is positive.
            2. Calculate fee: account.calculate_fees("WITHDRAWAL")
            3. Calculate total_deduction = amount + fee
            4. Check daily withdrawal limit
            5. Check if ATM has enough total cash
            6. Check denomination feasibility (greedy algorithm)
            7. Account.withdraw(total_deduction) — validates balance + rules
            8. Dispense cash from ATM (reduce notes)
            9. Record daily withdrawal
            10. Add transaction to account history
            11. Mark COMPLETED

        ATOMICITY:
            If step 8 fails (ATM cash issue), the account balance
            change from step 7 is rolled back.

        Returns:
            True if withdrawal succeeded.

        Raises:
            DailyLimitExceededError: If daily limit exceeded.
            InsufficientATMFundsError: If ATM cannot dispense.
            Various account exceptions: For balance/rule violations.

        Time Complexity: O(d) where d = number of denominations
        Space Complexity: O(d) for denomination result
        """
        try:
            fee = self._account.calculate_fees(TransactionType.WITHDRAWAL.value)
            total_deduction = self._amount + fee

            # Check daily limit
            daily_withdrawn = self._account.get_daily_withdrawn()
            if daily_withdrawn + total_deduction > DAILY_WITHDRAWAL_LIMIT:
                raise DailyLimitExceededError(
                    f"Daily withdrawal limit of Rs. {DAILY_WITHDRAWAL_LIMIT:,.0f} would be exceeded. "
                    f"Already withdrawn today: Rs. {daily_withdrawn:,.0f}. "
                    f"This transaction: Rs. {total_deduction:,.0f}"
                )

            # Check ATM cash
            if not self._cash_dispenser.has_sufficient_funds(self._amount):
                raise InsufficientATMFundsError(
                    f"ATM has insufficient cash. Available: Rs. {self._cash_dispenser.total_cash:,.0f}, "
                    f"Requested: Rs. {self._amount:,.0f}"
                )

            # Check denomination feasibility
            denomination_result = self._cash_dispenser.calculate_denomination(self._amount)
            if denomination_result is None:
                raise InsufficientATMFundsError(
                    f"ATM cannot dispense Rs. {self._amount:,.0f} "
                    f"with available denominations."
                )

            # Execute account withdrawal (validates balance + rules)
            self._account.withdraw(total_deduction)

            # Dispense cash from ATM
            self._cash_dispenser.dispense(denomination_result)

            # Record daily limit
            self._account.record_daily_withdrawal(total_deduction)

            # Record transaction
            self._account.add_transaction(self)
            self.mark_completed()
            return True

        except Exception:
            self.mark_failed()
            raise
