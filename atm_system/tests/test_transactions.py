"""
Tests for Transaction types (Deposit, Withdrawal, Transfer).

Test Cases:
    1. Deposit transaction creation and execution
    2. Deposit transaction ID format
    3. Deposit transaction timestamp
    4. Deposit transaction status
    5. Withdrawal transaction execution
    6. Withdrawal with fee
    7. Transfer transaction execution
    8. Transfer creates two records
    9. Transfer fee deducted from sender only
    10. Transfer same account fails
    11. Transfer insufficient balance
    12. Transfer atomicity (rollback)
    """

import unittest

from atm_system.enums import TransactionStatus, TransactionType
from atm_system.exceptions.exceptions import (
    InsufficientBalanceError,
    InvalidAmountError,
    SameAccountTransferError,
)
from atm_system.models.current_account import CurrentAccount
from atm_system.models.savings_account import SavingsAccount
from atm_system.services.cash_dispenser import CashDispenser
from atm_system.transactions.deposit import DepositTransaction
from atm_system.transactions.withdrawal import WithdrawalTransaction
from atm_system.transactions.transfer import TransferTransaction


class TestDepositTransaction(unittest.TestCase):
    """Test DepositTransaction."""

    def setUp(self):
        self.account = SavingsAccount("ACC-001", "User", 50_000, "1234")
        self.txn = DepositTransaction(20_000, self.account)

    def test_01_deposit_execution(self):
        """Test 1: Deposit increases account balance."""
        self.txn.execute()
        self.assertEqual(self.account.balance, 70_000)

    def test_02_transaction_id_format(self):
        """Test 2: Transaction ID starts with TXN-."""
        self.assertTrue(self.txn.transaction_id.startswith("TXN-"))

    def test_03_timestamp_exists(self):
        """Test 3: Timestamp is set on creation."""
        self.assertIsNotNone(self.txn.timestamp)

    def test_04_status_pending_then_completed(self):
        """Test 4: Status transitions PENDING → COMPLETED."""
        self.assertEqual(self.txn.status, TransactionStatus.PENDING)
        self.txn.execute()
        self.assertEqual(self.txn.status, TransactionStatus.COMPLETED)

    def test_05_type_is_deposit(self):
        """Test 5: Transaction type is DEPOSIT."""
        self.assertEqual(self.txn.transaction_type, TransactionType.DEPOSIT)

    def test_06_amount_display_positive(self):
        """Test 6: Amount display has + prefix."""
        self.assertIn("+", self.txn.get_amount_display())

    def test_07_negative_deposit_fails(self):
        """Test 7: Negative deposit amount fails."""
        txn = DepositTransaction(-1000, self.account)
        with self.assertRaises(InvalidAmountError):
            txn.execute()


class TestWithdrawalTransaction(unittest.TestCase):
    """Test WithdrawalTransaction."""

    def setUp(self):
        self.account = SavingsAccount("ACC-002", "User", 100_000, "1234")
        self.dispenser = CashDispenser()

    def test_08_withdrawal_execution(self):
        """Test 8: Withdrawal decreases balance."""
        txn = WithdrawalTransaction(10_000, self.account, self.dispenser)
        txn.execute()
        self.assertEqual(self.account.balance, 89_950)  # 100,000 - 10,000 - 50 fee

    def test_09_withdrawal_fee(self):
        """Test 9: Withdrawal fee is charged."""
        txn = WithdrawalTransaction(10_000, self.account, self.dispenser)
        txn.execute()
        self.assertEqual(txn.total_deduction, 10_050)

    def test_10_insufficient_atm_funds(self):
        """Test 10: Withdrawal fails if ATM lacks cash."""
        dispenser = CashDispenser({5000: 0, 1000: 0, 500: 0})
        txn = WithdrawalTransaction(10_000, self.account, dispenser)
        with self.assertRaises(Exception):
            txn.execute()


class TestTransferTransaction(unittest.TestCase):
    """Test TransferTransaction."""

    def setUp(self):
        self.sender = SavingsAccount("ACC-003", "Sender", 100_000, "1234")
        self.receiver = SavingsAccount("ACC-004", "Receiver", 50_000, "5678")

    def test_11_transfer_execution(self):
        """Test 11: Transfer debits sender and credits receiver."""
        txn = TransferTransaction(20_000, self.sender, self.receiver)
        txn.execute()
        self.assertEqual(self.sender.balance, 79_900)  # 100,000 - 20,000 - 100 fee
        self.assertEqual(self.receiver.balance, 70_000)

    def test_12_transfer_two_records(self):
        """Test 12: Transfer creates transaction records on both accounts."""
        txn = TransferTransaction(10_000, self.sender, self.receiver)
        txn.execute()
        # Sender has 1 transaction (the transfer)
        self.assertEqual(len(self.sender.transaction_history), 1)
        # Receiver has 1 transaction (the deposit counterpart)
        self.assertEqual(len(self.receiver.transaction_history), 1)

    def test_13_transfer_fee(self):
        """Test 13: Fee is Rs. 100 for transfers."""
        txn = TransferTransaction(10_000, self.sender, self.receiver)
        txn.execute()
        self.assertEqual(txn.total_sender_deduction, 10_100)

    def test_14_same_account_transfer(self):
        """Test 14: Transfer to same account fails."""
        txn = TransferTransaction(5_000, self.sender, self.sender)
        with self.assertRaises(SameAccountTransferError):
            txn.execute()

    def test_15_insufficient_sender_balance(self):
        """Test 15: Transfer fails if sender lacks balance (via overdraft check)."""
        sender = CurrentAccount("ACC-003", "Sender", 40_000, "1234")
        receiver = SavingsAccount("ACC-004", "Receiver", 50_000, "5678")

        # Transfer 40,000 + 100 fee = 40,100
        # Available: 40,000 + 50,000 overdraft = 90,000. This works.
        TransferTransaction(40_000, sender, receiver).execute()
        self.assertEqual(sender.balance, -100)

        # Now try 49,900 transfer (49,900 + 100 fee = 50,000)
        # -100 - 50,000 = -50,100 which exceeds -50,000 overdraft
        txn2 = TransferTransaction(49_900, sender, receiver)
        with self.assertRaises(InsufficientBalanceError):
            txn2.execute()

    def test_16_atomicity_rollback(self):
        """Test 16: Failed transfer rolls back sender balance."""
        sender = CurrentAccount("ACC-003", "Sender", 40_000, "1234")
        receiver = SavingsAccount("ACC-004", "Receiver", 50_000, "5678")

        # First transfer: 40,000 + 100 fee = 40,100. sender: 40,000 - 40,100 = -100
        TransferTransaction(40_000, sender, receiver).execute()
        self.assertEqual(sender.balance, -100)
        self.assertEqual(receiver.balance, 90_000)

        # Second transfer: 49,900 + 100 fee = 50,000
        # -100 - 50,000 = -50,100 exceeds overdraft → should fail and rollback
        txn = TransferTransaction(49_900, sender, receiver)
        try:
            txn.execute()
        except InsufficientBalanceError:
            pass
        # Sender balance unchanged from -100
        self.assertEqual(sender.balance, -100)
        # Receiver unchanged from 90,000
        self.assertEqual(receiver.balance, 90_000)


if __name__ == "__main__":
    unittest.main()
