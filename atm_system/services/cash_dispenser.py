"""
Cash Dispenser for ATM System.

Purpose:
    Manages physical cash inventory in the ATM.
    Handles denomination calculation and cash dispensing.

OOP Concept:
    ENCAPSULATION — Cash inventory is protected.
    Single Responsibility — Only manages ATM cash, not account operations.

DSA — DENOMINATION ALGORITHM:

    Problem:
        Given available note denominations with counts, determine if an
        exact amount can be dispensed and return the combination.

    Input:
        Denominations: {5000: count, 1000: count, 500: count}
        Requested amount: integer/float

    Output:
        Dictionary of {denomination: notes_used} or None if impossible.

    Algorithm — Greedy Strategy:
        For standard denominations (500, 1000, 5000) where each
        denomination is a multiple of the next smaller one, a greedy
        approach is CORRECT:

        1. Sort denominations descending: [5000, 1000, 500]
        2. For each denomination d:
            a. max_notes = min(available_count, amount // d)
            b. Use max_notes of denomination d
            c. Reduce amount by d * max_notes
            d. Reduce available count
        3. If remaining amount == 0: SUCCESS
        4. If remaining amount > 0: FAILURE

    Why Greedy is Correct Here:
        For denominations that are multiples of each other:
        (5000 = 10 × 500, 1000 = 2 × 500)
        the greedy algorithm always finds an optimal solution.

    Time Complexity: O(d) where d = number of denominations (3 in our case)
    Space Complexity: O(d) for the result dictionary

    Edge Cases:
        - Amount not divisible by smallest denomination → impossible
        - Amount = 0 → no notes needed
        - Available notes insufficient for any combination → None
        - Negative amount → None (invalid)

    Production Alternative:
        For arbitrary denominations (e.g., {1, 3, 4} and amount=6),
        greedy fails (greedy gives 4+1+1=3 notes, optimal is 3+3=2 notes).
        Use Dynamic Programming for the general case:
            dp[i] = minimum notes to make amount i
            dp[i] = min(dp[i-d] + 1 for d in denominations if d <= i)
        Time: O(amount × d), Space: O(amount)

        We use greedy here because our denominations are canonical
        (each is a multiple of the next smaller).
"""

from typing import Dict, Optional, Tuple


# Default ATM denominations (Rs.)
DENOMINATIONS = [5000, 1000, 500]


class CashDispenser:
    """Manages ATM physical cash inventory.

    ATTRIBUTES:
        _notes: Dict[denomination → count]

    WHY Dict:
        Natural mapping from denomination to available count.
        O(1) lookup for any denomination.
    """

    def __init__(self, initial_notes: Optional[Dict[int, int]] = None) -> None:
        """Initialize the cash dispenser.

        Args:
            initial_notes: Dict of {denomination: count}.
                          Defaults to standard ATM stock.

        Default stock:
            5000 × 10 = Rs. 50,000
            1000 × 30 = Rs. 30,000
            500 × 20  = Rs. 10,000
            Total: Rs. 90,000
        """
        if initial_notes is None:
            self._notes: Dict[int, int] = {
                5000: 10,
                1000: 30,
                500: 20,
            }
        else:
            self._notes = dict(initial_notes)

    # ── Properties ──

    @property
    def total_cash(self) -> float:
        """Calculate total available cash in ATM.

        Algorithm:
            Iterate through all denominations.
            Sum: denomination × count.

        Time Complexity: O(d) where d = number of denominations (3)
        Space Complexity: O(1)

        NOTE: This could be cached for O(1) but with only 3 denominations
        the iteration is negligible.
        """
        total = 0
        for denomination, count in self._notes.items():
            total += denomination * count
        return float(total)

    @property
    def note_inventory(self) -> Dict[int, int]:
        """Return a copy of note inventory.

        WHY copy: Prevent external mutation.
        """
        return dict(self._notes)

    # ── Cash Operations ──

    def has_sufficient_funds(self, amount: float) -> bool:
        """Check if ATM has enough total cash.

        Time Complexity: O(d)
        """
        return self.total_cash >= amount

    def get_available_denominations(self) -> Dict[int, int]:
        """Return denominations with count > 0.

        Algorithm:
            Filter _notes for count > 0.

        Time Complexity: O(d)
        Space Complexity: O(d)
        """
        return {d: c for d, c in self._notes.items() if c > 0}

    def calculate_denomination(self, amount: float) -> Optional[Dict[int, int]]:
        """Calculate exact denomination combination for requested amount.

        ALGORITHM — GREEDY (Correct for canonical denominations):

        Problem:
            Find non-negative integers x1, x2, x3 such that:
            5000*x1 + 1000*x2 + 500*x3 = amount
            where x1 <= notes[5000], x2 <= notes[1000], x3 <= notes[500]

        Algorithm:
            1. Validate amount is positive and divisible by smallest denomination.
            2. Sort denominations descending: [5000, 1000, 500].
            3. For each denomination d in sorted order:
                a. max_notes = min(available[d], amount_remaining // d)
                b. result[d] = max_notes
                c. amount_remaining -= d × max_notes
            4. If amount_remaining == 0: return result.
            5. Else: return None (impossible).

        WHY Greedy Works:
            For our denominations (500, 1000, 5000):
            - 1000 = 2 × 500
            - 5000 = 10 × 500 = 5 × 1000
            Each denomination is a multiple of the next smaller one.
            This means using as many large notes as possible always
            leads to an optimal (and correct) solution.

        Time Complexity: O(d log d) for sorting + O(d) for greedy = O(d log d)
            With d = 3 constant: effectively O(1)
        Space Complexity: O(d) for result dictionary

        Args:
            amount: The exact amount to dispense.

        Returns:
            Dict of {denomination: notes_used} if possible, None otherwise.
        """
        amount = int(amount)

        if amount <= 0:
            return None

        if amount % min(DENOMINATIONS) != 0:
            return None

        result: Dict[int, int] = {}
        remaining = amount

        # Sort descending for greedy approach
        sorted_dens = sorted(DENOMINATIONS, reverse=True)

        for denomination in sorted_dens:
            available_count = self._notes.get(denomination, 0)
            if denomination <= remaining and available_count > 0:
                max_notes = remaining // denomination
                notes_to_use = min(available_count, max_notes)
                result[denomination] = notes_to_use
                remaining -= denomination * notes_to_use

        if remaining == 0:
            return result
        return None

    def dispense(self, denomination_plan: Dict[int, int]) -> None:
        """Dispense cash according to the denomination plan.

        Args:
            denomination_plan: Dict of {denomination: notes_to_dispense}.

        Business Rule:
            Only call after calculate_denomination() confirms feasibility.

        Time Complexity: O(d)
        """
        for denomination, count in denomination_plan.items():
            self._notes[denomination] -= count

    def get_note_display(self) -> str:
        """Return formatted note inventory for display.

        Time Complexity: O(d)
        """
        lines = []
        for denom in sorted(self._notes.keys(), reverse=True):
            count = self._notes[denom]
            total = denom * count
            lines.append(
                f"  Rs. {denom:>5,} × {count:>3} = Rs. {total:>8,.0f}"
            )
        lines.append(f"  {'Total':>14} = Rs. {self.total_cash:>8,.0f}")
        return "\n".join(lines)

    def restock(self, denomination: int, count: int) -> None:
        """Restock a specific denomination.

        Args:
            denomination: Note value to restock.
            count: Number of notes to add.

        Time Complexity: O(1)
        """
        self._notes[denomination] = self._notes.get(denomination, 0) + count

    def __repr__(self) -> str:
        return (
            f"CashDispenser(total=Rs. {self.total_cash:,.0f}, "
            f"denominations={self._notes})"
        )
