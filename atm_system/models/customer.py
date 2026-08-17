"""
Customer model for ATM System.

Purpose:
    Represents a bank customer who owns accounts and cards.

OOP Concept:
    COMPOSITION — Customer HAS accounts (list of Account objects).
    COMPOSITION — Customer HAS cards (list of Card objects).
    ASSOCIATION — Customer is ASSOCIATED with Bank.

Business Rule:
    A customer may have:
    - One or more bank accounts (Savings, Current)
    - One or more ATM cards
    - Each card may be linked to specific accounts

OPTIMIZATION v2:
    Added internal dictionaries (_accounts_by_number, _cards_by_number)
    for O(1) lookup by ID, alongside the list for ordered iteration.
    This is a classic space-time tradeoff: O(n) extra space for O(1) lookup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from atm_system.models.account import Account
    from atm_system.models.card import Card


class Customer:
    """Represents a bank customer.

    WHY this class exists:
        Customers are the primary actors in the system.
        They own accounts and hold cards. Separating Customer from
        Account/Card follows Single Responsibility Principle.

    COMPOSITION:
        Customer OWNS its accounts and cards.
        When a customer is deleted, their associations are removed.

    ATTRIBUTES:
        _customer_id: Unique identifier
        _name: Full name
        _email: Email address
        _phone: Phone number
        _accounts: List of Account objects (ordered iteration)
        _accounts_by_number: Dict for O(1) lookup (OPTIMIZATION)
        _cards: List of Card objects (ordered iteration)
        _cards_by_number: Dict for O(1) lookup (OPTIMIZATION)
    """

    def __init__(
        self,
        customer_id: str,
        name: str,
        email: str = "",
        phone: str = "",
    ) -> None:
        """Initialize a Customer.

        Args:
            customer_id: Unique customer identifier.
            name: Full name of the customer.
            email: Email address (optional).
            phone: Phone number (optional).
        """
        self._customer_id: str = customer_id
        self._name: str = name
        self._email: str = email
        self._phone: str = phone
        self._accounts: List[Account] = []
        self._accounts_by_number: Dict[str, Account] = {}
        self._cards: List[Card] = []
        self._cards_by_number: Dict[str, Card] = {}

    # ── Properties ──

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def accounts(self) -> List[Account]:
        """Return a copy of accounts list."""
        return list(self._accounts)

    @property
    def cards(self) -> List[Card]:
        """Return a copy of cards list."""
        return list(self._cards)

    # ── Account Management ──

    def add_account(self, account: Account) -> None:
        """Add an account to this customer's portfolio.

        Args:
            account: Account object to add.

        Business Rule:
            A customer can have multiple accounts but no duplicates.

        Time Complexity: O(1) average (dict insert + list append)
        """
        if account.account_number not in self._accounts_by_number:
            self._accounts.append(account)
            self._accounts_by_number[account.account_number] = account

    def remove_account(self, account: Account) -> None:
        """Remove an account from this customer's portfolio.

        Time Complexity: O(n) for list removal, O(1) for dict removal.
        """
        if account.account_number in self._accounts_by_number:
            del self._accounts_by_number[account.account_number]
            self._accounts.remove(account)

    def get_account(self, account_number: str) -> Optional[Account]:
        """Find an account by account number.

        OPTIMIZATION:
            Changed from O(n) linear search to O(1) dictionary lookup.

        Algorithm (OLD): Linear scan through list — O(n)
        Algorithm (NEW): Dictionary lookup by key — O(1) average

        Args:
            account_number: The account number to find.

        Returns:
            Account if found, None otherwise.

        Time Complexity: O(1) average, O(n) worst case (hash collision)
        Space Complexity: O(1)
        """
        return self._accounts_by_number.get(account_number)

    def get_all_account_numbers(self) -> List[str]:
        """Return list of all account numbers for this customer.

        Time Complexity: O(n) where n = number of accounts
        Space Complexity: O(n)
        """
        return list(self._accounts_by_number.keys())

    def has_accounts(self) -> bool:
        """Check if customer has any accounts.

        Time Complexity: O(1)
        """
        return len(self._accounts) > 0

    # ── Card Management ──

    def add_card(self, card: Card) -> None:
        """Add a card to this customer.

        Time Complexity: O(1) average
        """
        if card.card_number not in self._cards_by_number:
            self._cards.append(card)
            self._cards_by_number[card.card_number] = card

    def remove_card(self, card: Card) -> None:
        """Remove a card from this customer.

        Time Complexity: O(n) for list, O(1) for dict
        """
        if card.card_number in self._cards_by_number:
            del self._cards_by_number[card.card_number]
            self._cards.remove(card)

    def get_card(self, card_number: str) -> Optional[Card]:
        """Find a card by card number.

        OPTIMIZATION:
            Changed from O(n) linear search to O(1) dictionary lookup.

        Time Complexity: O(1) average
        Space Complexity: O(1)
        """
        return self._cards_by_number.get(card_number)

    def has_active_card(self) -> bool:
        """Check if customer has at least one active card.

        Business Rule:
            Multiple cards are allowed but at least one must be active
            to perform transactions.

        Time Complexity: O(n) where n = number of cards (typically 1-3)
        """
        from atm_system.enums import CardStatus
        for card in self._cards:
            if card.status == CardStatus.ACTIVE:
                return True
        return False

    def __repr__(self) -> str:
        return (
            f"Customer(id={self._customer_id!r}, name={self._name!r}, "
            f"accounts={len(self._accounts)}, cards={len(self._cards)})"
        )
