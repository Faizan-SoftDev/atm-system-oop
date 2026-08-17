"""
Tests for services (StatementService, TransactionService, Bank).

Test Cases:
    1. StatementService: zero transactions
    2. StatementService: one transaction
    3. StatementService: five transactions
    4. StatementService: more than five
    5. StatementService: correct ordering
    6. Bank: add and find customer
    7. Bank: add and find account
    8. Bank: add and find card
    9. Bank: duplicate account
    10. Bank: customer not found
    11. Customer: O(1) lookup by account number
    12. Customer: O(1) lookup by card number
    13. Multiple accounts per customer
    14. Multiple cards per customer
    15. Blocked card doesn't affect other cards
    """

import unittest

from atm_system.enums import AccountStatus, CardStatus
from atm_system.exceptions.exceptions import (
    CustomerNotFoundError,
    DuplicateAccountError,
    InvalidAccountError,
)
from atm_system.models.bank import Bank
from atm_system.models.card import Card
from atm_system.models.current_account import CurrentAccount
from atm_system.models.customer import Customer
from atm_system.models.savings_account import SavingsAccount
from atm_system.services.statement_service import StatementService
from atm_system.transactions.deposit import DepositTransaction


class TestStatementService(unittest.TestCase):
    """Test mini statement generation."""

    def setUp(self):
        self.service = StatementService()
        self.account = SavingsAccount("ACC-001", "User", 50_000, "1234")

    def test_01_zero_transactions(self):
        """Test 1: Empty statement for no transactions."""
        result = self.service.get_last_n_transactions(self.account, 5)
        self.assertEqual(len(result), 0)

    def test_02_one_transaction(self):
        """Test 2: One transaction returned."""
        DepositTransaction(5_000, self.account).execute()
        result = self.service.get_last_n_transactions(self.account, 5)
        self.assertEqual(len(result), 1)

    def test_03_five_transactions(self):
        """Test 3: Five transactions returned when exactly 5 exist."""
        for _ in range(5):
            DepositTransaction(1_000, self.account).execute()
        result = self.service.get_last_n_transactions(self.account, 5)
        self.assertEqual(len(result), 5)

    def test_04_more_than_five(self):
        """Test 4: Only last 5 returned from 10 transactions."""
        for _ in range(10):
            DepositTransaction(1_000, self.account).execute()
        result = self.service.get_last_n_transactions(self.account, 5)
        self.assertEqual(len(result), 5)

    def test_05_correct_ordering(self):
        """Test 5: Last 5 are the most recent (last deposited)."""
        amounts = [1000, 2000, 3000, 4000, 5000, 6000, 7000]
        for amt in amounts:
            DepositTransaction(amt, self.account).execute()

        last_five = self.service.get_last_n_transactions(self.account, 5)
        # Should be 3000, 4000, 5000, 6000, 7000 (last 5 of 7)
        self.assertEqual(last_five[0].amount, 3_000)
        self.assertEqual(last_five[4].amount, 7_000)

    def test_06_format_mini_statement(self):
        """Test 6: Mini statement formatting."""
        DepositTransaction(5_000, self.account).execute()
        stmt = self.service.format_mini_statement(self.account)
        self.assertIn("MINI STATEMENT", stmt)
        self.assertIn("ACC-001", stmt)
        self.assertIn("55,000", stmt)  # 50,000 + 5,000


class TestBank(unittest.TestCase):
    """Test Bank entity management."""

    def setUp(self):
        self.bank = Bank("Test Bank")
        self.customer = Customer("CUS-001", "Test User")
        self.account = SavingsAccount("ACC-001", "Test User", 50_000, "1234")
        self.card = Card("CARD-001", "Test User", "1234")

    def test_07_add_find_customer(self):
        """Test 7: Add and find customer by ID."""
        self.bank.add_customer(self.customer)
        found = self.bank.find_customer("CUS-001")
        self.assertEqual(found.name, "Test User")

    def test_08_add_find_account(self):
        """Test 8: Add and find account by number."""
        self.bank.add_account(self.account)
        found = self.bank.find_account("ACC-001")
        self.assertEqual(found.balance, 50_000)

    def test_09_add_find_card(self):
        """Test 9: Add and find card by number."""
        self.bank.add_card(self.card)
        found = self.bank.find_card("CARD-001")
        self.assertEqual(found.card_holder, "Test User")

    def test_10_duplicate_account(self):
        """Test 10: Adding duplicate account raises error."""
        self.bank.add_account(self.account)
        with self.assertRaises(DuplicateAccountError):
            self.bank.add_account(self.account)

    def test_11_customer_not_found(self):
        """Test 11: get_customer raises for unknown ID."""
        with self.assertRaises(CustomerNotFoundError):
            self.bank.get_customer("UNKNOWN")

    def test_12_account_not_found(self):
        """Test 12: get_account raises for unknown number."""
        with self.assertRaises(InvalidAccountError):
            self.bank.get_account("UNKNOWN")


class TestCustomerOptimization(unittest.TestCase):
    """Test optimized Customer lookups."""

    def setUp(self):
        self.customer = Customer("CUS-001", "User")
        self.acc1 = SavingsAccount("ACC-001", "User", 50_000, "1234")
        self.acc2 = CurrentAccount("ACC-002", "User", 30_000, "1234")
        self.card1 = Card("CARD-001", "User", "1234")
        self.card2 = Card("CARD-002", "User", "5678")

    def test_13_multiple_accounts(self):
        """Test 13: Customer with multiple accounts."""
        self.customer.add_account(self.acc1)
        self.customer.add_account(self.acc2)
        self.assertEqual(len(self.customer.accounts), 2)

    def test_14_multiple_cards(self):
        """Test 14: Customer with multiple cards."""
        self.customer.add_card(self.card1)
        self.customer.add_card(self.card2)
        self.assertEqual(len(self.customer.cards), 2)

    def test_15_o1_account_lookup(self):
        """Test 15: Account lookup is O(1) via dictionary."""
        self.customer.add_account(self.acc1)
        self.customer.add_account(self.acc2)
        # Direct access by number
        found = self.customer.get_account("ACC-001")
        self.assertEqual(found.account_number, "ACC-001")

    def test_16_o1_card_lookup(self):
        """Test 16: Card lookup is O(1) via dictionary."""
        self.customer.add_card(self.card1)
        self.customer.add_card(self.card2)
        found = self.customer.get_card("CARD-002")
        self.assertEqual(found.card_number, "CARD-002")

    def test_17_blocked_card_doesnt_affect_other(self):
        """Test 17: Blocking one card doesn't affect the other."""
        self.customer.add_card(self.card1)
        self.customer.add_card(self.card2)
        self.card1.block()
        self.assertEqual(self.card1.status, CardStatus.BLOCKED)
        self.assertEqual(self.card2.status, CardStatus.ACTIVE)
        self.assertTrue(self.customer.has_active_card())

    def test_18_has_active_card(self):
        """Test 18: has_active_card returns True when one card is active."""
        self.customer.add_card(self.card1)
        self.assertTrue(self.customer.has_active_card())

    def test_19_no_active_card(self):
        """Test 19: has_active_card returns False when all blocked."""
        self.customer.add_card(self.card1)
        self.card1.block()
        self.assertFalse(self.customer.has_active_card())


if __name__ == "__main__":
    unittest.main()
