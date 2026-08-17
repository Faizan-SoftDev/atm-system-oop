"""
Tests for ATM operations (CashDispenser, denomination algorithm).

Test Cases:
    1. CashDispenser total cash calculation
    2. Denomination calculation for valid amount
    3. Denomination for amount not divisible by 500
    4. Denomination for impossible amount
    5. Dispense reduces notes correctly
    6. Insufficient ATM funds
    7. Denomination edge case: exact total
    8. Note display format
    """

import unittest

from atm_system.services.cash_dispenser import CashDispenser


class TestCashDispenser(unittest.TestCase):
    """Test ATM cash management and denomination algorithm."""

    def setUp(self):
        self.dispenser = CashDispenser()

    def test_01_total_cash(self):
        """Test 1: Total cash is calculated correctly."""
        # 5000×10 + 1000×30 + 500×20 = 50,000 + 30,000 + 10,000
        self.assertEqual(self.dispenser.total_cash, 90_000)

    def test_02_denomination_valid(self):
        """Test 2: Denomination calculation for Rs. 7,500."""
        result = self.dispenser.calculate_denomination(7_500)
        self.assertIsNotNone(result)
        # 5000×1 + 1000×2 + 500×1 = 7,500
        self.assertEqual(result[5000], 1)
        self.assertEqual(result[1000], 2)
        self.assertEqual(result[500], 1)

    def test_03_denomination_not_divisible(self):
        """Test 3: Amount not divisible by 500 returns None."""
        result = self.dispenser.calculate_denomination(333)
        self.assertIsNone(result)

    def test_04_denomination_impossible(self):
        """Test 4: Amount exceeding available notes returns None."""
        result = self.dispenser.calculate_denomination(500_000)
        self.assertIsNone(result)

    def test_05_dispense_reduces_notes(self):
        """Test 5: dispense() reduces note counts correctly."""
        plan = {5000: 2, 1000: 5}
        self.dispenser.dispense(plan)
        notes = self.dispenser.note_inventory
        self.assertEqual(notes[5000], 8)   # 10 - 2
        self.assertEqual(notes[1000], 25)  # 30 - 5

    def test_06_insufficient_funds(self):
        """Test 6: has_sufficient_funds returns False for large amount."""
        self.assertFalse(self.dispenser.has_sufficient_funds(200_000))

    def test_07_denomination_exact_total(self):
        """Test 7: Denomination for exact available total."""
        # Total = 90,000
        result = self.dispenser.calculate_denomination(90_000)
        self.assertIsNotNone(result)

    def test_08_denomination_zero(self):
        """Test 8: Zero amount returns None."""
        result = self.dispenser.calculate_denomination(0)
        self.assertIsNone(result)

    def test_09_denomination_small_amount(self):
        """Test 9: Rs. 500 denomination."""
        result = self.dispenser.calculate_denomination(500)
        self.assertIsNotNone(result)
        self.assertEqual(result[500], 1)

    def test_10_restock(self):
        """Test 10: restock increases note count."""
        self.dispenser.restock(5000, 5)
        notes = self.dispenser.note_inventory
        self.assertEqual(notes[5000], 15)

    def test_11_note_display(self):
        """Test 11: get_note_display returns formatted string."""
        display = self.dispenser.get_note_display()
        self.assertIn("5,000", display)
        self.assertIn("90,000", display)


if __name__ == "__main__":
    unittest.main()
