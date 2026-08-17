"""
Card model for ATM System.

Purpose:
    Represents an ATM card linked to a customer and accounts.

OOP Concept:
    ENCAPSULATION — Card status and failed attempts are protected.
    ASSOCIATION — Card is ASSOCIATED with Customer and Account(s).

Business Rule:
    A card belongs to ONE customer but may access MULTIPLE accounts.
    After 3 failed PIN attempts, card status changes to BLOCKED.
    PIN is NEVER stored or displayed in plain text during output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from atm_system.enums import CardStatus
from atm_system.exceptions.exceptions import CardBlockedError
from atm_system.utils.validators import MAX_FAILED_PIN_ATTEMPTS

if TYPE_CHECKING:
    from atm_system.models.account import Account
    from atm_system.models.customer import Customer


class Card:
    """Represents an ATM card.

    ENCAPSULATION:
        _status: Only modifiable through internal methods.
        _failed_pin_attempts: Counter is private.
        _pin: PIN is never exposed in __repr__ or str.

    ASSOCIATION:
        A Card BELONGS TO one Customer.
        A Card can ACCESS multiple Accounts.

    ATTRIBUTES:
        _card_number: Unique card number
        _card_holder: Name printed on card
        _status: ACTIVE, BLOCKED, or EXPIRED
        _failed_pin_attempts: Counter for incorrect PINs
        _max_pin_attempts: Maximum allowed failures (3)
        _customer: Associated Customer (ASSOCIATION)
        _linked_accounts: Accounts accessible by this card (AGGREGATION)
    """

    def __init__(self, card_number: str, card_holder: str, pin: str) -> None:
        """Initialize a Card.

        Args:
            card_number: Unique card identifier.
            card_holder: Name printed on the card.
            pin: The 4-digit PIN (stored internally, never exposed).
        """
        self._card_number: str = card_number
        self._card_holder: str = card_holder
        self._pin: str = pin
        self._status: CardStatus = CardStatus.ACTIVE
        self._failed_pin_attempts: int = 0
        self._max_pin_attempts: int = MAX_FAILED_PIN_ATTEMPTS
        self._customer: Optional["Customer"] = None
        self._linked_accounts: List["Account"] = []

    # ── Properties ──

    @property
    def card_number(self) -> str:
        return self._card_number

    @property
    def card_holder(self) -> str:
        return self._card_holder

    @property
    def status(self) -> CardStatus:
        return self._status

    @property
    def failed_pin_attempts(self) -> int:
        return self._failed_pin_attempts

    @property
    def is_blocked(self) -> bool:
        """Check if card is blocked."""
        return self._status == CardStatus.BLOCKED

    # ── PIN Verification ──

    def verify_pin(self, pin: str) -> bool:
        """Verify PIN and manage failed attempt counter.

        Business Rule:
            - If card is already blocked, raise CardBlockedError immediately.
            - If PIN is correct, reset counter and return True.
            - If PIN is wrong, increment counter.
            - If counter reaches 3, block the card.

        Args:
            pin: The PIN to verify.

        Returns:
            True if PIN is correct.

        Raises:
            CardBlockedError: If card is already blocked.

        Algorithm:
            1. Check if card is blocked → raise error.
            2. Compare pin with stored _pin.
            3. If match → reset attempts, return True.
            4. If no match → increment attempts.
            5. If attempts >= 3 → block card, raise error.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if self._status == CardStatus.BLOCKED:
            raise CardBlockedError(
                f"Card {self._card_number} is blocked. "
                "Please contact your bank for a replacement."
            )

        if pin == self._pin:
            self._failed_pin_attempts = 0
            return True
        else:
            self._failed_pin_attempts += 1
            if self._failed_pin_attempts >= self._max_pin_attempts:
                self._status = CardStatus.BLOCKED
                raise CardBlockedError(
                    f"Card {self._card_number} has been blocked after "
                    f"{self._max_pin_attempts} incorrect PIN attempts. "
                    "Please contact your bank."
                )
            return False

    # ── Customer Association ──

    def set_customer(self, customer: "Customer") -> None:
        """Associate this card with a customer.

        ASSOCIATION: Card → Customer (many-to-one).
        """
        self._customer = customer

    def get_customer(self) -> Optional["Customer"]:
        """Return the associated customer."""
        return self._customer

    # ── Account Linking (AGGREGATION) ──

    def link_account(self, account: "Account") -> None:
        """Link an account to this card.

        AGGREGATION: Card can access accounts, but accounts
        exist independently of the card.

        Business Rule:
            A card can access multiple accounts.
            After authentication, the user selects which account to use.
        """
        if account not in self._linked_accounts:
            self._linked_accounts.append(account)

    def unlink_account(self, account: "Account") -> None:
        """Remove an account link from this card."""
        if account in self._linked_accounts:
            self._linked_accounts.remove(account)

    def get_linked_accounts(self) -> List["Account"]:
        """Return list of accounts linked to this card."""
        return list(self._linked_accounts)

    # ── Status Management ──

    def block(self) -> None:
        """Manually block this card."""
        self._status = CardStatus.BLOCKED

    def activate(self) -> None:
        """Activate this card (e.g., after unblocking)."""
        self._status = CardStatus.ACTIVE
        self._failed_pin_attempts = 0

    def expire(self) -> None:
        """Mark card as expired."""
        self._status = CardStatus.EXPIRED

    # ── Representation (SECURITY: PIN never exposed) ──

    def __repr__(self) -> str:
        """String representation — NOTE: PIN is NEVER included."""
        return (
            f"Card(number={self._card_number!r}, "
            f"holder={self._card_holder!r}, "
            f"status={self._status.value})"
        )
