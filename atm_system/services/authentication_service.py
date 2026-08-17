"""
Authentication Service for ATM System.

Purpose:
    Handles card validation and PIN verification flow.

OOP Concept:
    Single Responsibility — Only handles authentication.
    Separation of Concerns — ATM delegates auth to this service.

Business Rule:
    Flow: Insert Card → Validate Card → Enter PIN → Verify PIN → Menu

    Maximum incorrect PIN attempts: 3
    After 3 failures: Card is BLOCKED permanently for the session.
"""

from atm_system.enums import CardStatus
from atm_system.exceptions.exceptions import (
    CardBlockedError,
    InvalidCardError,
    InvalidPINError,
)
from atm_system.models.card import Card


class AuthenticationService:
    """Handles card authentication and PIN verification.

    WHY this class exists:
        Authentication is a distinct concern from transactions,
        account management, or ATM operations. Separating it
        follows Single Responsibility Principle.

    Dependencies:
        Takes a Card object — doesn't need Bank because
        the ATM already resolves the card before calling.
    """

    def __init__(self) -> None:
        """Initialize authentication service."""
        self._max_attempts: int = 3

    def validate_card(self, card: Card) -> None:
        """Validate that a card is usable.

        Business Rule:
            Card must exist and be in ACTIVE status.

        Args:
            card: The card to validate.

        Raises:
            InvalidCardError: If card is None.
            CardBlockedError: If card is BLOCKED or EXPIRED.

        Time Complexity: O(1)
        """
        if card is None:
            raise InvalidCardError("No card provided")
        if card.status == CardStatus.BLOCKED:
            raise CardBlockedError(
                f"Card {card.card_number} is blocked. "
                "Please contact your bank."
            )
        if card.status == CardStatus.EXPIRED:
            raise CardBlockedError(
                f"Card {card.card_number} has expired. "
                "Please contact your bank."
            )

    def authenticate_pin(self, card: Card, pin: str) -> bool:
        """Authenticate a card with the given PIN.

        Algorithm:
            1. Validate card status.
            2. Delegate to card.verify_pin(pin).
            3. card.verify_pin handles:
                a. Blocked check
                b. PIN comparison
                c. Failed attempt tracking
                d. Auto-blocking after 3 failures

        Args:
            card: The card to authenticate.
            pin: The PIN entered by the user.

        Returns:
            True if authentication succeeds.

        Raises:
            CardBlockedError: If card is already blocked or gets blocked.
            InvalidPINError: If PIN is incorrect (only on final attempt
                           when card gets blocked, since card.verify_pin
                           raises CardBlockedError).

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.validate_card(card)
        return card.verify_pin(pin)

    def get_remaining_attempts(self, card: Card) -> int:
        """Return remaining PIN attempts for a card.

        Algorithm:
            remaining = max_attempts - failed_pin_attempts

        Time Complexity: O(1)
        """
        return max(0, self._max_attempts - card.failed_pin_attempts)
