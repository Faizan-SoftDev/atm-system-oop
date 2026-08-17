"""
Tests for Account hierarchy (SavingsAccount and CurrentAccount).

Test Cases:
    1. SavingsAccount creation with valid data
    2. CurrentAccount creation with valid data
    3. Deposit increases balance
    4. Invalid deposit (negative amount)
    5. Invalid deposit (zero amount)
    6. Savings withdrawal within rules
    7. Savings withdrawal below minimum balance
    8. Savings withdrawal below minimum amount
    9. Savings withdrawal above maximum amount
    10. Current account withdrawal with overdraft
    11. Current account overdraft exceeded
    12. Withdrawal on inactive account
    13. Deposit on inactive account
    14. Change PIN success
    15. Change PIN wrong old PIN
    16. Polymorphism: calculate_withdrawal_limit
    17. Polymorphism: get_withdrawal_rules
    18. Polymorphism: calculate_fees
"""

import unittest

from atm_system.enums import AccountStatus, AccountType
from atm_system.exceptions.exceptions import (
    AccountInactiveError,
    InsufficientBalanceError,
    InvalidAmountError,
    InvalidPINError,
)
from atm_system.models.current_account import CurrentAccount
from atm_system.models.savings_account import SavingsAccount


class TestSavingsAccount(unittest.TestCase):
    """Test SavingsAccount creation and operations."""

    def setUp(self):
        self.account = SavingsAccount(
            account_number="ACC-1001",
            account_holder="Test User",
            initial_balance=100_000,
            pin="1234",
        )

    def test_01_creation(self):
        """Test 1: SavingsAccount creation with valid data."""
        self.assertEqual(self.account.account_number, "ACC-1001")
        self.assertEqual(self.account.account_holder, "Test User")
        self.assertEqual(self.account.balance, 100_000)
        self.assertEqual(self.account.account_type, AccountType.SAVINGS)
        self.assertEqual(self.account.status, AccountStatus.ACTIVE)

    def test_02_deposit_increases_balance(self):
        """Test 2: Deposit increases balance correctly."""
        self.account.deposit(50_000)
        self.assertEqual(self.account.balance, 150_000)

    def test_03_invalid_deposit_negative(self):
        """Test 3: Negative deposit raises InvalidAmountError."""
        with self.assertRaises(InvalidAmountError):
            self.account.deposit(-1000)

    def test_04_invalid_deposit_zero(self):
        """Test 4: Zero deposit raises InvalidAmountError."""
        with self.assertRaises(InvalidAmountError):
            self.account.deposit(0)

    def test_05_valid_withdrawal(self):
        """Test 5: Valid withdrawal decreases balance."""
        self.account.withdraw(10_000)
        self.assertEqual(self.account.balance, 90_000)

    def test_06_withdrawal_below_minimum_balance(self):
        """Test 6: Withdrawal that would go below min balance fails."""
        # Balance: 100,000, Min balance: 5,000
        # Max withdrawable: 95,000 (but max per transaction is 50,000)
        # Withdraw 50,000 first, then try 45,001 (would leave 4,999 < 5,000)
        self.account.withdraw(50_000)
        self.assertEqual(self.account.balance, 50_000)
        with self.assertRaises(InsufficientBalanceError):
            self.account.withdraw(45_001)

    def test_07_withdrawal_below_minimum_amount(self):
        """Test 7: Withdrawal less than Rs. 500 fails."""
        with self.assertRaises(InvalidAmountError):
            self.account.withdraw(100)

    def test_08_withdrawal_above_maximum(self):
        """Test 8: Withdrawal more than Rs. 50,000 fails at service layer.

        MAX_WITHDRAWAL_AMOUNT is validated at the TransactionService
        layer before fees are added. Direct account access no longer
        enforces this limit since fee-inclusive amounts could exceed it.
        """
        from atm_system.utils.validators import validate_withdrawal_amount
        with self.assertRaises(InvalidAmountError):
            validate_withdrawal_amount(60_000)

    def test_09_withdrawal_negative_amount(self):
        """Test 9: Negative withdrawal fails."""
        with self.assertRaises(InvalidAmountError):
            self.account.withdraw(-5000)

    def test_10_inactive_account_deposit(self):
        """Test 10: Deposit on frozen account fails."""
        self.account.freeze()
        with self.assertRaises(AccountInactiveError):
            self.account.deposit(1000)

    def test_11_inactive_account_withdrawal(self):
        """Test 11: Withdrawal on frozen account fails."""
        self.account.freeze()
        with self.assertRaises(AccountInactiveError):
            self.account.withdraw(1000)

    def test_12_change_pin_success(self):
        """Test 12: PIN change with correct old PIN."""
        self.account.change_pin("1234", "5678")
        self.assertTrue(self.account.verify_pin("5678"))
        self.assertFalse(self.account.verify_pin("1234"))

    def test_13_change_pin_wrong_old(self):
        """Test 13: PIN change with wrong old PIN fails."""
        with self.assertRaises(InvalidPINError):
            self.account.change_pin("0000", "5678")

    def test_14_polymorphism_withdrawal_limit(self):
        """Test 14: calculate_withdrawal_limit returns savings-specific value."""
        limit = self.account.calculate_withdrawal_limit()
        # Available: 100,000 - 5,000 = 95,000
        # Per txn: min(95,000, 50,000) = 50,000
        self.assertEqual(limit, 50_000)

    def test_15_polymorphism_withdrawal_rules(self):
        """Test 15: get_withdrawal_rules returns savings-specific dict."""
        rules = self.account.get_withdrawal_rules()
        self.assertIn("minimum_balance", rules)
        self.assertEqual(rules["minimum_balance"], 5_000)

    def test_16_polymorphism_fees(self):
        """Test 16: calculate_fees returns correct fees."""
        self.assertEqual(self.account.calculate_fees("WITHDRAWAL"), 50)
        self.assertEqual(self.account.calculate_fees("TRANSFER"), 100)
        self.assertEqual(self.account.calculate_fees("DEPOSIT"), 0)

    def test_17_minimum_balance(self):
        """Test 17: get_minimum_balance returns Rs. 5,000."""
        self.assertEqual(self.account.get_minimum_balance(), 5_000)


class TestCurrentAccount(unittest.TestCase):
    """Test CurrentAccount creation and overdraft operations."""

    def setUp(self):
        self.account = CurrentAccount(
            account_number="ACC-1002",
            account_holder="Business User",
            initial_balance=50_000,
            pin="1234",
        )

    def test_18_creation(self):
        """Test 18: CurrentAccount creation with valid data."""
        self.assertEqual(self.account.account_number, "ACC-1002")
        self.assertEqual(self.account.balance, 50_000)
        self.assertEqual(self.account.account_type, AccountType.CURRENT)

    def test_19_withdrawal_with_overdraft(self):
        """Test 19: Withdrawal exceeding balance but within overdraft succeeds."""
        # Balance: 50,000, Overdraft: 50,000
        # Max per transaction: 50,000
        # Withdraw 50,000 (uses full available, balance goes to 0)
        self.account.withdraw(50_000)
        self.assertEqual(self.account.balance, 0)
        # Withdraw 40,000 more (overdraft: balance goes to -40,000)
        self.account.withdraw(40_000)
        self.assertEqual(self.account.balance, -40_000)

    def test_20_overdraft_exceeded(self):
        """Test 21: Withdrawal exceeding overdraft fails."""
        # Balance: 50,000, Overdraft limit: 50,000
        # Withdraw 50,000 (balance = 0), withdraw 49,501 (would go to -49,501)
        # -49,501 > -50,000, so this actually succeeds.
        # Need: balance - amount < -50,000
        # After 50,000 withdrawal: balance = 0
        # Need to withdraw > 50,000, but max per transaction is 50,000
        # So we do two withdrawals to deplete the overdraft
        self.account.withdraw(50_000)   # balance = 0
        self.account.withdraw(50_000)   # balance = -50,000 (at limit)
        with self.assertRaises(InsufficientBalanceError):
            self.account.withdraw(500)  # would go to -50,500 (exceeds)

    def test_21_no_minimum_balance_constraint(self):
        """Test 22: Current account allows zero balance without overdraft."""
        self.account.withdraw(45_000)
        self.assertEqual(self.account.balance, 5_000)

    def test_22_polymorphism_withdrawal_limit(self):
        """Test 23: calculate_withdrawal_limit uses overdraft for current."""
        limit = self.account.calculate_withdrawal_limit()
        # Available: 50,000 + 50,000 = 100,000
        # Per txn: min(100,000, 50,000) = 50,000
        self.assertEqual(limit, 50_000)

    def test_23_polymorphism_rules(self):
        """Test 24: get_withdrawal_rules includes overdraft_limit."""
        rules = self.account.get_withdrawal_rules()
        self.assertIn("overdraft_limit", rules)
        self.assertEqual(rules["overdraft_limit"], 50_000)

    def test_24_minimum_balance_negative(self):
        """Test 25: Current account minimum balance is -50,000."""
        self.assertEqual(self.account.get_minimum_balance(), -50_000)

    def test_25_activate_after_close(self):
        """Test 26: Closed account can be reactivated."""
        self.account.close()
        self.assertEqual(self.account.status, AccountStatus.CLOSED)
        self.account.activate()
        self.assertEqual(self.account.status, AccountStatus.ACTIVE)

    def test_26_repr(self):
        """Test 27: __repr__ does not expose PIN."""
        r = repr(self.account)
        self.assertNotIn("1234", r)
        self.assertIn("ACC-1002", r)


if __name__ == "__main__":
    unittest.main()
