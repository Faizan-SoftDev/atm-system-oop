"""
Tests for authentication flow.

Test Cases:
    1. Valid PIN authentication
    2. Invalid PIN attempt
    3. One failed attempt (still active)
    4. Two failed attempts (still active)
    5. Three failed attempts (card blocked)
    6. Correct PIN after partial failures
    7. Blocked card cannot authenticate
    8. validate_card with active card
    9. validate_card with blocked card
    """

import unittest

from atm_system.enums import CardStatus
from atm_system.exceptions.exceptions import CardBlockedError
from atm_system.models.card import Card
from atm_system.services.authentication_service import AuthenticationService


class TestAuthentication(unittest.TestCase):
    """Test card authentication and PIN verification."""

    def setUp(self):
        self.auth = AuthenticationService()
        self.card = Card("CARD-001", "Test User", "1234")

    def test_01_valid_pin(self):
        """Test 1: Correct PIN authenticates successfully."""
        result = self.auth.authenticate_pin(self.card, "1234")
        self.assertTrue(result)

    def test_02_invalid_pin(self):
        """Test 2: Incorrect PIN fails authentication (returns False)."""
        result = self.auth.authenticate_pin(self.card, "0000")
        self.assertFalse(result)

    def test_03_one_failed_attempt(self):
        """Test 3: After one failure, card remains active."""
        try:
            self.auth.authenticate_pin(self.card, "0000")
        except CardBlockedError:
            pass
        self.assertEqual(self.card.status, CardStatus.ACTIVE)
        self.assertEqual(self.card.failed_pin_attempts, 1)

    def test_04_two_failed_attempts(self):
        """Test 4: After two failures, card remains active."""
        for _ in range(2):
            try:
                self.auth.authenticate_pin(self.card, "0000")
            except CardBlockedError:
                pass
        self.assertEqual(self.card.status, CardStatus.ACTIVE)
        self.assertEqual(self.card.failed_pin_attempts, 2)

    def test_05_three_failed_attempts_blocks_card(self):
        """Test 5: Three failures block the card."""
        for _ in range(3):
            try:
                self.auth.authenticate_pin(self.card, "0000")
            except CardBlockedError:
                pass
        self.assertEqual(self.card.status, CardStatus.BLOCKED)
        self.assertTrue(self.card.is_blocked)

    def test_06_correct_pin_after_partial_failures(self):
        """Test 6: Correct PIN works after failed attempts."""
        try:
            self.auth.authenticate_pin(self.card, "0000")
        except CardBlockedError:
            pass
        try:
            self.auth.authenticate_pin(self.card, "0000")
        except CardBlockedError:
            pass
        # Reset on correct PIN
        result = self.auth.authenticate_pin(self.card, "1234")
        self.assertTrue(result)
        self.assertEqual(self.card.failed_pin_attempts, 0)

    def test_07_blocked_card_fails(self):
        """Test 7: Blocked card raises error immediately."""
        self.card.block()
        with self.assertRaises(CardBlockedError):
            self.auth.authenticate_pin(self.card, "1234")

    def test_08_validate_active_card(self):
        """Test 8: validate_card passes for active card."""
        self.auth.validate_card(self.card)  # Should not raise

    def test_09_validate_blocked_card(self):
        """Test 9: validate_card raises for blocked card."""
        self.card.block()
        with self.assertRaises(CardBlockedError):
            self.auth.validate_card(self.card)

    def test_10_remaining_attempts(self):
        """Test 10: get_remaining_attempts returns correct count."""
        self.assertEqual(self.auth.get_remaining_attempts(self.card), 3)
        try:
            self.auth.authenticate_pin(self.card, "0000")
        except CardBlockedError:
            pass
        self.assertEqual(self.auth.get_remaining_attempts(self.card), 2)


if __name__ == "__main__":
    unittest.main()
