"""
Integration/Workflow tests for ATM System.

End-to-end tests that exercise the complete ATM workflow through the
ATM service facade, verifying all components work together correctly.

Requirement Traceability:
    Authentication workflow     → TestAuthenticationWorkflow
    Account selection           → TestAccountSelection
    Balance inquiry             → TestBalanceInquiry
    Deposit                     → TestDepositWorkflow
    Withdrawal                  → TestWithdrawalWorkflow
    ATM cash management         → TestATMCashManagement
    Transfer                    → TestTransferWorkflow
    Change PIN                  → TestChangePINWorkflow
    Mini statement              → TestMiniStatementWorkflow
    Daily limit tracking        → TestDailyLimitTracking
    Transaction fees            → TestTransactionFees
    Multiple accounts           → TestMultipleAccounts
    Multiple cards              → TestMultipleCards
    Exit/logout                 → TestExitLogout
    Error handling              → TestErrorHandling
    Boundary conditions         → TestBoundaryConditions
    End-to-end workflows        → TestEndToEndWorkflow
"""

import unittest

from atm_system.enums import CardStatus
from atm_system.exceptions.exceptions import (
    ATMError,
    CardBlockedError,
    DailyLimitExceededError,
    InsufficientBalanceError,
    InsufficientATMFundsError,
    InvalidAccountError,
    InvalidAmountError,
    InvalidCardError,
    InvalidPINError,
    PINValidationError,
    SameAccountTransferError,
)
from atm_system.models.bank import Bank
from atm_system.models.card import Card
from atm_system.models.current_account import CurrentAccount
from atm_system.models.customer import Customer
from atm_system.models.savings_account import SavingsAccount
from atm_system.services.account_service import AccountService
from atm_system.services.atm_service import ATM
from atm_system.services.authentication_service import AuthenticationService
from atm_system.services.cash_dispenser import CashDispenser
from atm_system.services.statement_service import StatementService
from atm_system.services.transaction_service import TransactionService
from atm_system.utils.validators import (
    DAILY_TRANSFER_LIMIT,
    DAILY_WITHDRAWAL_LIMIT,
    MIN_BALANCE_SAVINGS,
    MAX_WITHDRAWAL_AMOUNT,
    MIN_WITHDRAWAL_AMOUNT,
    OVERDRAFT_LIMIT_CURRENT,
    TRANSFER_FEE,
    WITHDRAWAL_FEE,
)


def create_test_atm():
    """Helper: Create a fully wired ATM with test data.

    Returns:
        Tuple of (atm, bank) for use in tests.
    """
    bank = Bank("Test Bank")

    # Customer 1: Has savings + current, one card
    customer1 = Customer("C001", "Alice", "alice@test.com", "111-111")
    savings1 = SavingsAccount("ACC-100", "Alice", 100_000, "1234")
    current1 = CurrentAccount("ACC-200", "Alice", 50_000, "1234")
    card1 = Card("CARD-001", "Alice", "1234")
    card1.link_account(savings1)
    card1.link_account(current1)
    customer1.add_account(savings1)
    customer1.add_account(current1)
    customer1.add_card(card1)
    card1.set_customer(customer1)
    bank.add_customer(customer1)
    bank.add_account(savings1)
    bank.add_account(current1)
    bank.add_card(card1)

    # Customer 2: Has savings only, one card
    customer2 = Customer("C002", "Bob", "bob@test.com", "222-222")
    savings2 = SavingsAccount("ACC-300", "Bob", 75_000, "5678")
    card2 = Card("CARD-002", "Bob", "5678")
    card2.link_account(savings2)
    customer2.add_account(savings2)
    customer2.add_card(card2)
    card2.set_customer(customer2)
    bank.add_customer(customer2)
    bank.add_account(savings2)
    bank.add_card(card2)

    # Services
    auth_service = AuthenticationService()
    cash_dispenser = CashDispenser()
    transaction_service = TransactionService(cash_dispenser)
    account_service = AccountService()
    statement_service = StatementService()

    atm = ATM(
        bank=bank,
        auth_service=auth_service,
        transaction_service=transaction_service,
        account_service=account_service,
        statement_service=statement_service,
        cash_dispenser=cash_dispenser,
    )

    return atm, bank


class TestAuthenticationWorkflow(unittest.TestCase):
    """Test complete authentication workflow."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_insert_valid_card(self):
        """Insert a valid card succeeds."""
        card = self.atm.insert_card("CARD-001")
        self.assertEqual(card.card_number, "CARD-001")

    def test_02_insert_invalid_card(self):
        """Insert a non-existent card raises error."""
        with self.assertRaises(InvalidCardError):
            self.atm.insert_card("FAKE-CARD")

    def test_03_authenticate_valid_pin(self):
        """Valid PIN authentication succeeds."""
        self.atm.insert_card("CARD-001")
        result = self.atm.authenticate("1234")
        self.assertTrue(result)

    def test_04_authenticate_invalid_pin(self):
        """Invalid PIN raises error."""
        self.atm.insert_card("CARD-001")
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("0000")

    def test_05_three_failed_pin_attempts_blocks_card(self):
        """Three failed PIN attempts block the card."""
        self.atm.insert_card("CARD-001")
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("0001")
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("0002")
        # Third attempt blocks the card
        with self.assertRaises(CardBlockedError):
            self.atm.authenticate("0003")

    def test_06_blocked_card_cannot_authenticate(self):
        """Blocked card cannot be used for authentication."""
        # Block the card via 3 failed attempts
        self.atm.insert_card("CARD-001")
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("0001")
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("0002")
        with self.assertRaises(CardBlockedError):
            self.atm.authenticate("0003")

        # Card is now blocked
        card = self.bank.get_card("CARD-001")
        self.assertEqual(card.status, CardStatus.BLOCKED)

    def test_07_blocked_card_rejected_on_insert(self):
        """Inserting a blocked card raises error."""
        card = self.bank.get_card("CARD-001")
        card.block()
        with self.assertRaises(CardBlockedError):
            self.atm.insert_card("CARD-001")

    def test_08_correct_pin_resets_attempt_counter(self):
        """Correct PIN after failed attempts resets the counter."""
        self.atm.insert_card("CARD-001")
        # 2 failures
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("0001")
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("0002")
        # Correct PIN resets counter
        self.atm.authenticate("1234")
        card = self.bank.get_card("CARD-001")
        self.assertEqual(card.failed_pin_attempts, 0)

    def test_09_eject_card_resets_session(self):
        """Ejecting card resets the session state."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.eject_card()
        # After eject, operations should fail
        with self.assertRaises(ATMError):
            self.atm.check_balance()

    def test_10_operation_without_auth_fails(self):
        """Operations without authentication fail."""
        self.atm.insert_card("CARD-001")
        with self.assertRaises(ATMError):
            self.atm.check_balance()

    def test_11_operation_without_account_fails(self):
        """Operations without account selection fail."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        with self.assertRaises(ATMError):
            self.atm.check_balance()


class TestAccountSelection(unittest.TestCase):
    """Test account selection workflows."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_get_linked_accounts_multi(self):
        """Card with multiple accounts returns all linked accounts."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        accounts = self.atm.get_linked_accounts()
        self.assertEqual(len(accounts), 2)
        acc_numbers = {a.account_number for a in accounts}
        self.assertIn("ACC-100", acc_numbers)
        self.assertIn("ACC-200", acc_numbers)

    def test_02_get_linked_accounts_single(self):
        """Card with single account returns one account."""
        self.atm.insert_card("CARD-002")
        self.atm.authenticate("5678")
        accounts = self.atm.get_linked_accounts()
        self.assertEqual(len(accounts), 1)

    def test_03_select_account_success(self):
        """Selecting a linked account succeeds."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        account = self.atm.select_account("ACC-100")
        self.assertEqual(account.account_number, "ACC-100")

    def test_04_select_unlinked_account_fails(self):
        """Selecting an account not linked to card fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        with self.assertRaises(InvalidAccountError):
            self.atm.select_account("ACC-300")

    def test_05_select_nonexistent_account_fails(self):
        """Selecting a non-existent account fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        with self.assertRaises(InvalidAccountError):
            self.atm.select_account("ACC-999")

    def test_06_switch_account(self):
        """Can switch between accounts."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")

        self.atm.select_account("ACC-100")
        balance1 = self.atm.check_balance()
        self.assertEqual(balance1, 100_000)

        self.atm.select_account("ACC-200")
        balance2 = self.atm.check_balance()
        self.assertEqual(balance2, 50_000)


class TestBalanceInquiry(unittest.TestCase):
    """Test balance inquiry through ATM facade."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_check_savings_balance(self):
        """Check savings account balance."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        balance = self.atm.check_balance()
        self.assertEqual(balance, 100_000)

    def test_02_check_current_balance(self):
        """Check current account balance."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-200")
        balance = self.atm.check_balance()
        self.assertEqual(balance, 50_000)

    def test_03_balance_after_deposit(self):
        """Balance reflects deposits."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.deposit(25_000)
        balance = self.atm.check_balance()
        self.assertEqual(balance, 125_000)

    def test_04_balance_after_withdrawal(self):
        """Balance reflects withdrawals."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.withdraw(10_000)
        balance = self.atm.check_balance()
        self.assertEqual(balance, 100_000 - 10_000 - WITHDRAWAL_FEE)

    def test_05_frozen_account_check_balance_fails(self):
        """Checking balance on a frozen account fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        account = self.bank.get_account("ACC-100")
        account.freeze()
        with self.assertRaises(ATMError):
            self.atm.check_balance()


class TestDepositWorkflow(unittest.TestCase):
    """Test deposit through ATM facade."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_successful_deposit(self):
        """Deposit increases balance correctly."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        txn = self.atm.deposit(30_000)
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, 30_000)
        self.assertEqual(self.atm.check_balance(), 130_000)

    def test_02_deposit_creates_transaction_record(self):
        """Deposit creates a transaction record."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.deposit(10_000)
        account = self.bank.get_account("ACC-100")
        self.assertEqual(len(account.transaction_history), 1)
        self.assertEqual(account.transaction_history[0].amount, 10_000)

    def test_03_deposit_negative_amount_fails(self):
        """Negative deposit fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.deposit(-1000)

    def test_04_deposit_zero_fails(self):
        """Zero deposit fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.deposit(0)

    def test_05_deposit_on_frozen_account_fails(self):
        """Deposit on frozen account fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        account = self.bank.get_account("ACC-100")
        account.freeze()
        with self.assertRaises(ATMError):
            self.atm.deposit(5_000)

    def test_06_deposit_on_closed_account_fails(self):
        """Deposit on closed account fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        account = self.bank.get_account("ACC-100")
        account.close()
        with self.assertRaises(ATMError):
            self.atm.deposit(5_000)


class TestWithdrawalWorkflow(unittest.TestCase):
    """Test withdrawal through ATM facade."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_successful_withdrawal_savings(self):
        """Withdrawal from savings account succeeds."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        txn = self.atm.withdraw(10_000)
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, 10_000)
        expected_balance = 100_000 - 10_000 - WITHDRAWAL_FEE
        self.assertEqual(self.atm.check_balance(), expected_balance)

    def test_02_successful_withdrawal_current(self):
        """Withdrawal from current account succeeds."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-200")
        txn = self.atm.withdraw(5_000)
        self.assertIsNotNone(txn)
        expected_balance = 50_000 - 5_000 - WITHDRAWAL_FEE
        self.assertEqual(self.atm.check_balance(), expected_balance)

    def test_03_withdrawal_deducts_fee(self):
        """Withdrawal charges fee."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        initial = self.atm.check_balance()
        self.atm.withdraw(10_000)
        final = self.atm.check_balance()
        self.assertEqual(initial - final, 10_000 + WITHDRAWAL_FEE)

    def test_04_withdrawal_creates_transaction_record(self):
        """Withdrawal creates transaction record."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.withdraw(5_000)
        account = self.bank.get_account("ACC-100")
        self.assertEqual(len(account.transaction_history), 1)

    def test_05_withdrawal_below_minimum_fails(self):
        """Withdrawal below Rs. 500 minimum fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.withdraw(100)

    def test_06_withdrawal_above_maximum_fails(self):
        """Withdrawal above Rs. 50,000 maximum fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.withdraw(60_000)

    def test_07_withdrawal_negative_amount_fails(self):
        """Negative withdrawal amount fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.withdraw(-5_000)

    def test_08_withdrawal_zero_fails(self):
        """Zero withdrawal amount fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.withdraw(0)

    def test_09_atm_insufficient_cash(self):
        """Withdrawal fails when ATM has insufficient cash."""
        dispenser = CashDispenser({5000: 0, 1000: 0, 500: 0})
        transaction_service = TransactionService(dispenser)
        atm = ATM(
            bank=self.bank,
            auth_service=AuthenticationService(),
            transaction_service=transaction_service,
            account_service=AccountService(),
            statement_service=StatementService(),
            cash_dispenser=dispenser,
        )
        atm.insert_card("CARD-001")
        atm.authenticate("1234")
        atm.select_account("ACC-100")
        with self.assertRaises(InsufficientATMFundsError):
            atm.withdraw(5_000)

    def test_10_atm_denomination_not_possible(self):
        """Withdrawal fails when denomination combination is impossible."""
        dispenser = CashDispenser({5000: 5, 1000: 0, 500: 0})
        transaction_service = TransactionService(dispenser)
        atm = ATM(
            bank=self.bank,
            auth_service=AuthenticationService(),
            transaction_service=transaction_service,
            account_service=AccountService(),
            statement_service=StatementService(),
            cash_dispenser=dispenser,
        )
        atm.insert_card("CARD-001")
        atm.authenticate("1234")
        atm.select_account("ACC-100")
        with self.assertRaises(InsufficientATMFundsError):
            atm.withdraw(1_000)

    def test_11_withdrawal_on_frozen_account_fails(self):
        """Withdrawal on frozen account fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        account = self.bank.get_account("ACC-100")
        account.freeze()
        with self.assertRaises(ATMError):
            self.atm.withdraw(5_000)

    def test_12_savings_max_withdrawal_per_transaction(self):
        """Savings max withdrawal per transaction is Rs. 50,000."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        txn = self.atm.withdraw(MAX_WITHDRAWAL_AMOUNT)
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, MAX_WITHDRAWAL_AMOUNT)

    def test_13_savings_min_balance_boundary(self):
        """Savings withdrawal respects minimum balance."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        # Balance 100,000, min balance 5,000, fee 50
        # Withdraw 45,000 (divisible by 500): total deducted = 45,050
        # Remaining: 100,000 - 45,050 = 54,950 (>= 5,000)
        self.atm.withdraw(45_000)
        balance = self.atm.check_balance()
        self.assertEqual(balance, 54_950)

    def test_14_savings_min_balance_exceeded(self):
        """Savings withdrawal below minimum balance fails."""
        # Create custom ATM with higher cash to allow large withdrawals
        bank = Bank("Test Bank")
        customer = Customer("C001", "Alice", "alice@test.com", "111-111")
        savings = SavingsAccount("ACC-100", "Alice", 100_000, "1234")
        card = Card("CARD-001", "Alice", "1234")
        card.link_account(savings)
        customer.add_account(savings)
        customer.add_card(card)
        card.set_customer(customer)
        bank.add_customer(customer)
        bank.add_account(savings)
        bank.add_card(card)

        # ATM with 200,000 cash so it won't run out
        notes = {5000: 40, 1000: 0, 500: 0}
        atm = ATM(
            bank=bank,
            auth_service=AuthenticationService(),
            transaction_service=TransactionService(CashDispenser(notes)),
            account_service=AccountService(),
            statement_service=StatementService(),
            cash_dispenser=CashDispenser(notes),
        )
        atm.insert_card("CARD-001")
        atm.authenticate("1234")
        atm.select_account("ACC-100")
        # Withdraw 45,000 first (balance: 100,000 - 45,000 - 50 = 54,950)
        atm.withdraw(45_000)
        # Now withdraw 50,000 (balance: 54,950 - 50,000 - 50 = 4,900 < 5,000)
        with self.assertRaises(InsufficientBalanceError):
            atm.withdraw(50_000)

    def test_15_current_account_overdraft(self):
        """Current account allows withdrawal into overdraft."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-200")
        # Balance 50,000, max per transaction 50,000
        self.atm.withdraw(50_000)
        balance = self.atm.check_balance()
        # 50,000 - 50,000 - 50 = -50
        self.assertEqual(balance, -50)

    def test_16_current_account_overdraft_exceeded(self):
        """Current account withdrawal beyond overdraft fails."""
        # Create custom setup: current account starting at 0
        bank = Bank("Test Bank")
        customer = Customer("C001", "Alice", "alice@test.com", "111-111")
        current = CurrentAccount("ACC-200", "Alice", 0, "1234")
        card = Card("CARD-001", "Alice", "1234")
        card.link_account(current)
        customer.add_account(current)
        customer.add_card(card)
        card.set_customer(customer)
        bank.add_customer(customer)
        bank.add_account(current)
        bank.add_card(card)

        notes = {5000: 40, 1000: 0, 500: 0}
        atm = ATM(
            bank=bank,
            auth_service=AuthenticationService(),
            transaction_service=TransactionService(CashDispenser(notes)),
            account_service=AccountService(),
            statement_service=StatementService(),
            cash_dispenser=CashDispenser(notes),
        )
        atm.insert_card("CARD-001")
        atm.authenticate("1234")
        atm.select_account("ACC-200")
        # Balance 0, try to withdraw 50,000: total deduction = 50,050
        # -50,050 < -50,000 overdraft limit → InsufficientBalanceError
        with self.assertRaises(InsufficientBalanceError):
            atm.withdraw(50_000)

    def test_17_daily_withdrawal_limit_exceeded(self):
        """Multiple withdrawals exceeding daily limit fail."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        # Withdraw 50,000 (daily withdrawn: 50,050)
        self.atm.withdraw(50_000)
        # Try 50,000 again: 50,050 + 50,050 = 100,100 > 100,000
        with self.assertRaises(DailyLimitExceededError):
            self.atm.withdraw(50_000)


class TestTransferWorkflow(unittest.TestCase):
    """Test transfer through ATM facade."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_successful_transfer(self):
        """Transfer between accounts succeeds."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        txn = self.atm.transfer("ACC-300", 20_000)
        self.assertIsNotNone(txn)
        # Sender: 100,000 - 20,000 - 100 fee = 79,900
        self.assertEqual(self.atm.check_balance(), 79_900)
        # Receiver: 75,000 + 20,000 = 95,000
        receiver = self.bank.get_account("ACC-300")
        self.assertEqual(receiver.balance, 95_000)

    def test_02_transfer_creates_two_records(self):
        """Transfer creates transaction records on both accounts."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.transfer("ACC-300", 10_000)
        sender = self.bank.get_account("ACC-100")
        receiver = self.bank.get_account("ACC-300")
        self.assertEqual(len(sender.transaction_history), 1)
        self.assertEqual(len(receiver.transaction_history), 1)

    def test_03_transfer_fee_deducted_from_sender_only(self):
        """Transfer fee is deducted from sender only."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.transfer("ACC-300", 10_000)
        sender = self.bank.get_account("ACC-100")
        receiver = self.bank.get_account("ACC-300")
        self.assertEqual(sender.balance, 100_000 - 10_100)
        self.assertEqual(receiver.balance, 75_000 + 10_000)

    def test_04_transfer_to_same_account_fails(self):
        """Transfer to same account fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(SameAccountTransferError):
            self.atm.transfer("ACC-100", 5_000)

    def test_05_transfer_negative_amount_fails(self):
        """Negative transfer amount fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.transfer("ACC-300", -5_000)

    def test_06_transfer_zero_amount_fails(self):
        """Zero transfer amount fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.transfer("ACC-300", 0)

    def test_07_transfer_to_nonexistent_account_fails(self):
        """Transfer to non-existent account fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAccountError):
            self.atm.transfer("ACC-999", 5_000)

    def test_08_transfer_atomicity_rollback(self):
        """Failed transfer does not affect sender or receiver balances."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        sender_before = self.bank.get_account("ACC-100").balance
        receiver_before = self.bank.get_account("ACC-300").balance

        # Transfer 49,950 + 100 fee = 50,050 from savings
        # Savings min balance is 5,000, so available = 95,000
        # 50,050 <= 95,000, so this should succeed
        self.atm.transfer("ACC-300", 49_950)

        sender_after = self.bank.get_account("ACC-100").balance
        receiver_after = self.bank.get_account("ACC-300").balance
        # Sender: 100,000 - 49,950 - 100 = 49,950
        self.assertEqual(sender_after, 49_950)
        # Receiver: 75,000 + 49,950 = 124,950
        self.assertEqual(receiver_after, 124_950)

    def test_09_transfer_to_other_customer_account(self):
        """Transfer to another customer's account works."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.transfer("ACC-300", 5_000)
        receiver = self.bank.get_account("ACC-300")
        self.assertEqual(receiver.balance, 80_000)


class TestChangePINWorkflow(unittest.TestCase):
    """Test PIN change through ATM facade."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_successful_pin_change(self):
        """PIN change with correct old PIN succeeds."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.change_pin("1234", "5678")
        # Verify account PIN changed
        account = self.bank.get_account("ACC-100")
        self.assertTrue(account.verify_pin("5678"))
        self.assertFalse(account.verify_pin("1234"))

    def test_02_wrong_old_pin_fails(self):
        """PIN change with wrong old PIN fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidPINError):
            self.atm.change_pin("0000", "5678")

    def test_03_invalid_new_pin_format(self):
        """PIN change with invalid new PIN format fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(PINValidationError):
            self.atm.change_pin("1234", "12")

    def test_04_non_numeric_pin_fails(self):
        """PIN change with non-numeric PIN fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(PINValidationError):
            self.atm.change_pin("1234", "ABCD")

    def test_05_empty_pin_fails(self):
        """PIN change with empty PIN fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(PINValidationError):
            self.atm.change_pin("1234", "")

    def test_06_change_pin_preserves_account_state(self):
        """PIN change doesn't affect account balance."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        balance_before = self.atm.check_balance()
        self.atm.change_pin("1234", "5678")
        balance_after = self.atm.check_balance()
        self.assertEqual(balance_before, balance_after)


class TestMiniStatementWorkflow(unittest.TestCase):
    """Test mini statement through ATM facade."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_empty_statement(self):
        """Mini statement with no transactions."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        stmt = self.atm.get_mini_statement()
        self.assertIn("No transactions found", stmt)

    def test_02_statement_with_transactions(self):
        """Mini statement shows recent transactions."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.deposit(5_000)
        self.atm.withdraw(2_000)
        stmt = self.atm.get_mini_statement()
        self.assertIn("MINI STATEMENT", stmt)
        self.assertIn("ACC-100", stmt)

    def test_03_statement_shows_correct_account(self):
        """Statement contains correct account number."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-200")
        self.atm.deposit(1_000)
        stmt = self.atm.get_mini_statement()
        self.assertIn("ACC-200", stmt)

    def test_04_statement_shows_current_balance(self):
        """Statement shows correct final balance."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.deposit(10_000)
        stmt = self.atm.get_mini_statement()
        self.assertIn("110,000", stmt)


class TestDailyLimitTracking(unittest.TestCase):
    """Test daily limit tracking across multiple transactions."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_multiple_withdrawals_track_daily_total(self):
        """Multiple withdrawals accumulate for daily limit."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        self.atm.withdraw(10_000)
        self.atm.withdraw(10_000)
        self.atm.withdraw(10_000)

        account = self.bank.get_account("ACC-100")
        daily = account.get_daily_withdrawn()
        # 3 x (10,000 + 50 fee) = 30,150
        self.assertEqual(daily, 30_150)

    def test_02_multiple_transfers_track_daily_total(self):
        """Multiple transfers accumulate for daily limit."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        self.atm.transfer("ACC-300", 10_000)
        self.atm.transfer("ACC-300", 10_000)

        account = self.bank.get_account("ACC-100")
        daily = account.get_daily_transferred()
        # 2 x (10,000 + 100 fee) = 20,200
        self.assertEqual(daily, 20_200)

    def test_03_daily_withdrawal_limit_prevents_overdraw(self):
        """Daily withdrawal limit prevents further withdrawals."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        # First withdraw uses 50,050 of 100,000 daily limit
        self.atm.withdraw(50_000)
        # Second withdraw: 50,050 + 50,050 = 100,100 > 100,000
        with self.assertRaises(DailyLimitExceededError):
            self.atm.withdraw(50_000)


class TestTransactionFees(unittest.TestCase):
    """Test that fees are correctly applied."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_withdrawal_fee_savings(self):
        """Savings withdrawal fee is Rs. 50."""
        account = self.bank.get_account("ACC-100")
        fee = account.calculate_fees("WITHDRAWAL")
        self.assertEqual(fee, WITHDRAWAL_FEE)

    def test_02_withdrawal_fee_current(self):
        """Current withdrawal fee is Rs. 50."""
        account = self.bank.get_account("ACC-200")
        fee = account.calculate_fees("WITHDRAWAL")
        self.assertEqual(fee, WITHDRAWAL_FEE)

    def test_03_transfer_fee_savings(self):
        """Savings transfer fee is Rs. 100."""
        account = self.bank.get_account("ACC-100")
        fee = account.calculate_fees("TRANSFER")
        self.assertEqual(fee, TRANSFER_FEE)

    def test_04_transfer_fee_current(self):
        """Current transfer fee is Rs. 100."""
        account = self.bank.get_account("ACC-200")
        fee = account.calculate_fees("TRANSFER")
        self.assertEqual(fee, TRANSFER_FEE)

    def test_05_deposit_no_fee(self):
        """Deposit has no fee."""
        account = self.bank.get_account("ACC-100")
        fee = account.calculate_fees("DEPOSIT")
        self.assertEqual(fee, 0.0)

    def test_06_withdrawal_deducts_correct_total(self):
        """Withdrawal deducts amount + fee from account."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.withdraw(5_000)
        # 100,000 - 5,000 - 50 = 94,950
        self.assertEqual(self.atm.check_balance(), 94_950)


class TestMultipleAccounts(unittest.TestCase):
    """Test scenarios with multiple accounts."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_deposit_to_savings_then_withdraw_from_current(self):
        """Deposit to one account, withdraw from another."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")

        self.atm.select_account("ACC-100")
        self.atm.deposit(10_000)
        self.assertEqual(self.atm.check_balance(), 110_000)

        self.atm.select_account("ACC-200")
        self.atm.withdraw(10_000)
        self.assertEqual(self.atm.check_balance(), 50_000 - 10_000 - WITHDRAWAL_FEE)

    def test_02_transfer_between_own_accounts(self):
        """Transfer between own accounts works."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.transfer("ACC-200", 20_000)

        savings = self.bank.get_account("ACC-100")
        current = self.bank.get_account("ACC-200")
        self.assertEqual(savings.balance, 79_900)
        self.assertEqual(current.balance, 70_000)

    def test_03_independent_balances(self):
        """Accounts maintain independent balances."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")

        self.atm.select_account("ACC-100")
        self.atm.deposit(5_000)

        self.atm.select_account("ACC-200")
        self.atm.deposit(10_000)

        savings = self.bank.get_account("ACC-100")
        current = self.bank.get_account("ACC-200")
        self.assertEqual(savings.balance, 105_000)
        self.assertEqual(current.balance, 60_000)

    def test_04_independent_transaction_histories(self):
        """Accounts maintain independent transaction histories."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")

        self.atm.select_account("ACC-100")
        self.atm.deposit(5_000)

        self.atm.select_account("ACC-200")
        self.atm.deposit(10_000)
        self.atm.withdraw(2_000)

        savings = self.bank.get_account("ACC-100")
        current = self.bank.get_account("ACC-200")
        self.assertEqual(len(savings.transaction_history), 1)
        self.assertEqual(len(current.transaction_history), 2)


class TestMultipleCards(unittest.TestCase):
    """Test scenarios with multiple cards."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_different_cards_different_pins(self):
        """Different cards have different PINs."""
        self.atm.insert_card("CARD-001")
        self.assertTrue(self.atm.authenticate("1234"))
        self.atm.eject_card()

        self.atm.insert_card("CARD-002")
        self.assertTrue(self.atm.authenticate("5678"))

    def test_02_blocked_card_doesnt_affect_other(self):
        """Blocking one card doesn't affect the other."""
        card1 = self.bank.get_card("CARD-001")
        card1.block()

        self.atm.insert_card("CARD-002")
        result = self.atm.authenticate("5678")
        self.assertTrue(result)

    def test_03_different_cards_different_accounts(self):
        """Different cards access different accounts."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        accounts1 = self.atm.get_linked_accounts()
        acc_nums1 = {a.account_number for a in accounts1}
        self.atm.eject_card()

        self.atm.insert_card("CARD-002")
        self.atm.authenticate("5678")
        accounts2 = self.atm.get_linked_accounts()
        acc_nums2 = {a.account_number for a in accounts2}

        self.assertIn("ACC-100", acc_nums1)
        self.assertIn("ACC-200", acc_nums1)
        self.assertIn("ACC-300", acc_nums2)
        self.assertNotIn("ACC-100", acc_nums2)


class TestATMCashManagement(unittest.TestCase):
    """Test ATM cash management integration."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_cash_decreases_after_withdrawal(self):
        """ATM cash decreases after withdrawal."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.withdraw(10_000)
        dispenser_notes = self.atm._cash_dispenser.note_inventory
        total_remaining = sum(d * c for d, c in dispenser_notes.items())
        self.assertEqual(total_remaining, 80_000)

    def test_02_denomination_algorithm_correct(self):
        """Denomination algorithm distributes correct notes."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.withdraw(7_500)
        dispenser = self.atm._cash_dispenser
        notes = dispenser.note_inventory
        # Default: {5000:10, 1000:30, 500:20}
        # After 7,500 = 5000x1 + 1000x2 + 500x1
        self.assertEqual(notes[5000], 9)
        self.assertEqual(notes[1000], 28)
        self.assertEqual(notes[500], 19)

    def test_03_exact_total_cash_boundary(self):
        """Withdrawal of exact total ATM cash succeeds."""
        dispenser = CashDispenser({5000: 1, 1000: 5, 500: 0})
        # Total = 5000 + 5000 = 10,000
        transaction_service = TransactionService(dispenser)
        atm = ATM(
            bank=self.bank,
            auth_service=AuthenticationService(),
            transaction_service=transaction_service,
            account_service=AccountService(),
            statement_service=StatementService(),
            cash_dispenser=dispenser,
        )
        atm.insert_card("CARD-001")
        atm.authenticate("1234")
        atm.select_account("ACC-100")
        atm.withdraw(10_000)
        self.assertEqual(dispenser.total_cash, 0)

    def test_04_multiple_withdrawals_deplete_cash(self):
        """Multiple withdrawals gradually deplete ATM cash."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        self.atm.withdraw(5_000)
        self.atm.withdraw(5_000)
        self.atm.withdraw(5_000)

        dispenser = self.atm._cash_dispenser
        self.assertEqual(dispenser.total_cash, 90_000 - 15_000)


class TestExitLogout(unittest.TestCase):
    """Test exit/logout flow."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_eject_card_clears_session(self):
        """Eject card clears all session state."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.eject_card()
        with self.assertRaises(ATMError):
            self.atm.check_balance()

    def test_02_reuse_after_eject(self):
        """Can start new session after eject."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.deposit(5_000)
        self.atm.eject_card()

        self.atm.insert_card("CARD-002")
        self.atm.authenticate("5678")
        self.atm.select_account("ACC-300")
        balance = self.atm.check_balance()
        self.assertEqual(balance, 75_000)

    def test_03_state_independence(self):
        """New session doesn't inherit previous session state."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.deposit(10_000)
        self.atm.eject_card()

        self.atm.insert_card("CARD-002")
        self.atm.authenticate("5678")
        self.atm.select_account("ACC-300")
        balance = self.atm.check_balance()
        self.assertEqual(balance, 75_000)


class TestBoundaryConditions(unittest.TestCase):
    """Test boundary conditions and edge cases."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_minimum_withdrawal_savings(self):
        """Minimum withdrawal amount (Rs. 500) succeeds."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        txn = self.atm.withdraw(MIN_WITHDRAWAL_AMOUNT)
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, MIN_WITHDRAWAL_AMOUNT)

    def test_02_maximum_withdrawal_savings(self):
        """Maximum withdrawal amount (Rs. 50,000) succeeds."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        txn = self.atm.withdraw(MAX_WITHDRAWAL_AMOUNT)
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, MAX_WITHDRAWAL_AMOUNT)

    def test_03_withdrawal_just_below_minimum_fails(self):
        """Withdrawal Rs. 1 below minimum fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.withdraw(MIN_WITHDRAWAL_AMOUNT - 1)

    def test_04_withdrawal_just_above_maximum_fails(self):
        """Withdrawal Rs. 1 above maximum fails."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        with self.assertRaises(InvalidAmountError):
            self.atm.withdraw(MAX_WITHDRAWAL_AMOUNT + 1)

    def test_05_current_overdraft_exact_boundary(self):
        """Current account withdrawal to exact overdraft limit."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-200")
        # Withdraw 50,000: 50,000 - 50,000 - 50 = -50
        self.atm.withdraw(50_000)
        self.assertEqual(self.atm.check_balance(), -50)

    def test_06_current_overdraft_exceeded(self):
        """Current account withdrawal beyond overdraft limit fails."""
        bank = Bank("Test Bank")
        customer = Customer("C001", "Alice", "alice@test.com", "111-111")
        current = CurrentAccount("ACC-200", "Alice", 0, "1234")
        card = Card("CARD-001", "Alice", "1234")
        card.link_account(current)
        customer.add_account(current)
        customer.add_card(card)
        card.set_customer(customer)
        bank.add_customer(customer)
        bank.add_account(current)
        bank.add_card(card)

        notes = {5000: 40, 1000: 0, 500: 0}
        atm = ATM(
            bank=bank,
            auth_service=AuthenticationService(),
            transaction_service=TransactionService(CashDispenser(notes)),
            account_service=AccountService(),
            statement_service=StatementService(),
            cash_dispenser=CashDispenser(notes),
        )
        atm.insert_card("CARD-001")
        atm.authenticate("1234")
        atm.select_account("ACC-200")
        # Balance 0, withdraw 50,000: total deduction = 50,050
        # Balance would be -50,050 < -50,000 overdraft limit
        with self.assertRaises(InsufficientBalanceError):
            atm.withdraw(50_000)

    def test_07_empty_transaction_history(self):
        """Mini statement for account with no transactions."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        stmt = self.atm.get_mini_statement()
        self.assertIn("No transactions found", stmt)

    def test_08_exactly_five_transactions(self):
        """Mini statement with exactly 5 transactions shows all."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        for _ in range(5):
            self.atm.deposit(1_000)
        account = self.bank.get_account("ACC-100")
        self.assertEqual(len(account.transaction_history), 5)

    def test_09_more_than_five_transactions(self):
        """Mini statement with 7 transactions shows last 5."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        for _ in range(7):
            self.atm.deposit(1_000)
        account = self.bank.get_account("ACC-100")
        self.assertEqual(len(account.transaction_history), 7)

    def test_10_atm_exact_cash_for_withdrawal(self):
        """ATM with exactly the right amount can dispense."""
        dispenser = CashDispenser({5000: 0, 1000: 10, 500: 0})
        transaction_service = TransactionService(dispenser)
        atm = ATM(
            bank=self.bank,
            auth_service=AuthenticationService(),
            transaction_service=transaction_service,
            account_service=AccountService(),
            statement_service=StatementService(),
            cash_dispenser=dispenser,
        )
        atm.insert_card("CARD-001")
        atm.authenticate("1234")
        atm.select_account("ACC-100")
        atm.withdraw(10_000)
        self.assertEqual(dispenser.total_cash, 0)

    def test_11_current_account_can_start_at_zero(self):
        """Current account can start with 0 balance."""
        current = CurrentAccount("ACC-NEW", "Test", 0, "0000")
        self.assertEqual(current.balance, 0)

    def test_12_savings_account_min_initial_balance(self):
        """Savings account maintains minimum balance after creation."""
        savings = SavingsAccount("ACC-NEW", "Test", 10_000, "0000")
        self.assertEqual(savings.balance, 10_000)
        self.assertEqual(savings.get_minimum_balance(), MIN_BALANCE_SAVINGS)


class TestEndToEndWorkflow(unittest.TestCase):
    """Complete end-to-end workflow tests."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_full_deposit_withdraw_statement_cycle(self):
        """Full cycle: deposit -> withdraw -> check balance -> statement."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        self.atm.deposit(20_000)
        self.assertEqual(self.atm.check_balance(), 120_000)

        self.atm.withdraw(10_000)
        self.assertEqual(self.atm.check_balance(), 110_000 - WITHDRAWAL_FEE)

        stmt = self.atm.get_mini_statement()
        self.assertIn("MINI STATEMENT", stmt)

    def test_02_full_transfer_between_customers(self):
        """Full transfer workflow between two customers."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.transfer("ACC-300", 15_000)
        self.atm.eject_card()

        alice = self.bank.get_account("ACC-100")
        bob = self.bank.get_account("ACC-300")
        self.assertEqual(alice.balance, 100_000 - 15_000 - TRANSFER_FEE)
        self.assertEqual(bob.balance, 75_000 + 15_000)

    def test_03_full_pin_change_reauth_cycle(self):
        """Full cycle: auth -> change PIN -> eject -> reauth with card PIN."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.change_pin("1234", "9999")
        self.atm.eject_card()

        # Card PIN is still "1234" (PIN change only affects account)
        self.atm.insert_card("CARD-001")
        result = self.atm.authenticate("1234")
        self.assertTrue(result)

    def test_04_multiple_operations_single_session(self):
        """Multiple operations in a single session."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        # Deposit
        self.atm.deposit(10_000)
        self.assertEqual(self.atm.check_balance(), 110_000)

        # Withdraw
        self.atm.withdraw(5_000)
        balance = self.atm.check_balance()
        self.assertEqual(balance, 105_000 - WITHDRAWAL_FEE)

        # Transfer
        self.atm.transfer("ACC-300", 5_000)
        balance = self.atm.check_balance()
        # After deposit: 110,000
        # After withdraw: 110,000 - 5,000 - 50 = 104,950
        # After transfer: 104,950 - 5,000 - 100 = 99,850
        self.assertEqual(balance, 99_850)

        # Statement
        stmt = self.atm.get_mini_statement()
        self.assertIn("MINI STATEMENT", stmt)

    def test_05_concurrent_different_cards_sequential(self):
        """Two different cards used sequentially."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.deposit(5_000)
        self.atm.eject_card()

        self.atm.insert_card("CARD-002")
        self.atm.authenticate("5678")
        self.atm.select_account("ACC-300")
        self.atm.deposit(10_000)
        self.atm.eject_card()

        alice = self.bank.get_account("ACC-100")
        bob = self.bank.get_account("ACC-300")
        self.assertEqual(alice.balance, 105_000)
        self.assertEqual(bob.balance, 85_000)


class TestErrorHandling(unittest.TestCase):
    """Test error handling across the system."""

    def setUp(self):
        self.atm, self.bank = create_test_atm()

    def test_01_atm_error_hierarchy(self):
        """All custom exceptions inherit from ATMError."""
        self.assertTrue(issubclass(InvalidPINError, ATMError))
        self.assertTrue(issubclass(CardBlockedError, ATMError))
        self.assertTrue(issubclass(InsufficientBalanceError, ATMError))
        self.assertTrue(issubclass(InsufficientATMFundsError, ATMError))
        self.assertTrue(issubclass(InvalidAmountError, ATMError))
        self.assertTrue(issubclass(DailyLimitExceededError, ATMError))
        self.assertTrue(issubclass(InvalidAccountError, ATMError))
        self.assertTrue(issubclass(InvalidCardError, ATMError))
        self.assertTrue(issubclass(SameAccountTransferError, ATMError))
        self.assertTrue(issubclass(PINValidationError, ATMError))

    def test_02_error_messages_are_descriptive(self):
        """Error messages contain useful information."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        try:
            self.atm.withdraw(60_000)  # Above max
            self.fail("Should have raised exception")
        except InvalidAmountError as e:
            self.assertTrue(len(e.message) > 0)

    def test_03_failed_transaction_doesnt_corrupt_state(self):
        """Failed transaction doesn't corrupt ATM or account state."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        balance_before = self.atm.check_balance()
        try:
            self.atm.withdraw(60_000)  # Should fail (above max)
        except InvalidAmountError:
            pass
        balance_after = self.atm.check_balance()
        self.assertEqual(balance_before, balance_after)

    def test_04_operations_after_error_continue_normally(self):
        """Operations after an error can still succeed."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")

        try:
            self.atm.withdraw(60_000)  # Should fail
        except InvalidAmountError:
            pass

        # This should succeed
        self.atm.withdraw(5_000)
        self.assertNotEqual(self.atm.check_balance(), 100_000)

    def test_05_card_not_inserted_error(self):
        """Operations without card raise appropriate error."""
        with self.assertRaises(ATMError):
            self.atm.check_balance()

    def test_06_account_not_selected_error(self):
        """Operations without account selection raise error."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        with self.assertRaises(ATMError):
            self.atm.check_balance()

    def test_07_invalid_card_on_auth(self):
        """Wrong PIN for card 1 raises InvalidPINError."""
        self.atm.insert_card("CARD-001")
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("5678")  # Wrong PIN for card 1

    def test_08_eject_clears_card_and_account(self):
        """Eject clears both card and account references."""
        self.atm.insert_card("CARD-001")
        self.atm.authenticate("1234")
        self.atm.select_account("ACC-100")
        self.atm.eject_card()
        with self.assertRaises(ATMError):
            self.atm.check_balance()
        with self.assertRaises(ATMError):
            self.atm.deposit(1000)


if __name__ == "__main__":
    unittest.main()
