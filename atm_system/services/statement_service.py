"""
Statement Service for ATM System.

Purpose:
    Generates account statements and mini statements.

OOP Concept:
    Single Responsibility — only handles statement formatting and retrieval.
    Service Layer — separates display logic from business logic.

DSA — LAST-FIVE ALGORITHM:

    Problem:
        Select the last 5 transactions from a list of n transactions.

    Input:
        transaction_history: List[Transaction] (append-ordered by time)

    Output:
        List of at most 5 most recent transactions.

    Algorithm — Manual Selection (Reverse Iteration):
        1. Get the length n of the transaction history.
        2. If n == 0: return empty list.
        3. Calculate start_index = max(0, n - 5).
        4. Iterate from start_index to n-1.
        5. Collect transactions into result list.
        6. Return result.

    WHY NOT slicing:
        While list[-5:] is more Pythonic, the manual implementation
        demonstrates index calculation and boundary handling.

    Time Complexity: O(1) — we only access at most 5 elements
        (not O(n) because n - 5 is calculated, not iterated)
    Space Complexity: O(5) = O(1)

    Edge Cases:
        - 0 transactions → return empty list
        - 3 transactions → return all 3
        - 5 transactions → return all 5
        - 12 transactions → return last 5
"""

from typing import List

from atm_system.models.account import Account
from atm_system.transactions.transaction import Transaction


class StatementService:
    """Service for generating account statements."""

    def __init__(self) -> None:
        pass

    def get_last_n_transactions(
        self, account: Account, n: int = 5
    ) -> List[Transaction]:
        """Get the last N transactions from account history.

        ALGORITHM — Manual Reverse Selection:

        Problem:
            Select the last n items from a list of length N.
            Without using built-in slicing.

        Approach:
            Calculate the start index and iterate manually.

        Step-by-step:
            1. history = account.transaction_history (copy, O(N))
            2. length = len(history)
            3. If length == 0: return []
            4. start = max(0, length - n)
            5. result = []
            6. For i in range(start, length):
                result.append(history[i])
            7. Return result

        Time Complexity: O(N) for the copy + O(n) for selection = O(N)
            N = total transactions, n = requested (5)
            Since n is bounded (always 5), the selection is O(1).
            The copy is O(N) but necessary for encapsulation.
        Space Complexity: O(N) for the copy + O(n) for result

        Args:
            account: Account to get transactions from.
            n: Number of recent transactions (default 5).

        Returns:
            List of at most n most recent transactions.
        """
        history = account.transaction_history  # Returns a copy (O(N))
        length = len(history)

        if length == 0:
            return []

        # Manual index calculation (demonstrates algorithm)
        start_index = max(0, length - n)
        result: List[Transaction] = []
        i = start_index
        while i < length:
            result.append(history[i])
            i += 1

        return result

    def format_mini_statement(self, account: Account) -> str:
        """Format a mini statement for display.

        Output Format:
            ========== MINI STATEMENT ==========
            Account: ACC-1001
            Date        Type          Amount
            -------------------------------------
            17-Aug      Deposit       +20,000
            17-Aug      Withdrawal    -10,000
            ...
            -------------------------------------
            Current Balance: Rs. 75,000

        Time Complexity: O(N) where N = total transactions (for the copy)
        Space Complexity: O(N) for the history copy
        """
        last_five = self.get_last_n_transactions(account, 5)

        lines = [
            "",
            "=" * 44,
            "         MINI STATEMENT",
            "=" * 44,
            f"Account: {account.account_number}",
            "",
            f"{'Date':<12} {'Type':<14} {'Amount':>12}",
            "-" * 44,
        ]

        if not last_five:
            lines.append("  No transactions found.")
        else:
            for txn in last_five:
                date_str = txn.get_date_display()
                type_str = txn.get_type_display()
                amount_str = txn.get_amount_display()
                lines.append(f"{date_str:<12} {type_str:<14} {amount_str:>12}")

        lines.append("-" * 44)
        lines.append(f"Current Balance: Rs. {account.balance:,.0f}")
        lines.append("=" * 44)
        lines.append("")

        return "\n".join(lines)
