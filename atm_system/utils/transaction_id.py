"""
Transaction ID Generator for ATM System.

Purpose:
    Generates unique, sequential transaction IDs in the format:
    TXN-YYYYMMDD-XXXXXX

OOP Concept:
    Encapsulation — ID generation logic is hidden behind a simple interface.
    Reusability — Used by all transaction types.

Algorithm:
    Problem: Generate unique, human-readable transaction IDs.
    Input: None (stateless generation).
    Output: String like "TXN-20260817-000001".
    Approach: Date-based prefix + sequential counter per day.
    The counter resets when the date changes (new day = new sequence).

    Step-by-step:
    1. Get current date as YYYYMMDD string.
    2. If the date matches the last generation date, increment counter.
    3. If the date is new, reset counter to 1.
    4. Format as TXN-YYYYMMDD-XXXXXX (zero-padded 6 digits).
    5. Store the current date and counter for next call.

    Time Complexity: O(1)
    Space Complexity: O(1)
    Edge Cases:
    - First call of a new day: counter starts at 1.
    - Counter overflow (999,999): Not handled for educational simplicity;
      production systems would use UUID or database sequences.
"""

from datetime import datetime


class TransactionIdGenerator:
    """Generates unique transaction IDs with date-based prefix and sequential numbering.

    Instance State:
        _last_date: The date string of the last generation.
        _counter: Sequential counter for the current date.
    """

    def __init__(self) -> None:
        """Initialize the generator with no prior state."""
        self._last_date: str = ""
        self._counter: int = 0

    def generate(self) -> str:
        """Generate the next unique transaction ID.

        Returns:
            A string like "TXN-20260817-000001".

        Algorithm:
            1. Format current date as YYYYMMDD.
            2. Compare with stored _last_date.
            3. If same day, increment counter.
            4. If new day, reset counter to 1 and update _last_date.
            5. Format and return the ID.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        current_date = datetime.now().strftime("%Y%m%d")

        if current_date == self._last_date:
            self._counter += 1
        else:
            self._last_date = current_date
            self._counter = 1

        return f"TXN-{current_date}-{self._counter:06d}"

    def reset(self) -> None:
        """Reset the generator state.

        Used for testing or when a new session begins.
        """
        self._last_date = ""
        self._counter = 0
