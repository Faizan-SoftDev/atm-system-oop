"""
Bank class for ATM System.

Purpose:
    Central registry that manages all customers, accounts, and cards.
    Acts as the single source of truth for entity management.

OOP Concept:
    AGGREGATION — Bank manages collections of Customer, Account, Card.
    These entities exist independently of the Bank but are organized by it.

    Single Responsibility — Bank only manages entity registration and lookup.
    It does NOT perform transactions (that's TransactionService's job).

Data Structure Design:
    THREE dictionaries for O(1) lookup by primary key:
    - _customers: dict[customer_id → Customer]
    - _accounts: dict[account_number → Account]
    - _cards: dict[card_number → Card]

    WHY dictionaries instead of lists:
        Primary use case is lookup by ID, not iteration.
        Average lookup: O(1) vs O(n) for lists.
        Space: O(n) extra for hash table overhead — acceptable tradeoff.
        Insert: O(1) average vs O(1) for list append (no difference).
        Delete: O(1) average vs O(n) for list remove.

    For iteration (e.g., printing all customers), lists are converted
    from dict values, which is O(n) — but this is infrequent.
"""

from typing import Dict, List, Optional

from atm_system.enums import AccountStatus, CardStatus
from atm_system.exceptions.exceptions import (
    CustomerNotFoundError,
    DuplicateAccountError,
    InvalidAccountError,
    InvalidCardError,
)
from atm_system.models.account import Account
from atm_system.models.card import Card
from atm_system.models.customer import Customer


class Bank:
    """Central registry for all banking entities.

    AGGREGATION:
        Bank manages collections of Customer, Account, Card.
        These entities can exist independently of the Bank
        (e.g., passed to services directly).

    Data Structures:
        _customers: Dict[str, Customer]  — O(1) by customer_id
        _accounts: Dict[str, Account]    — O(1) by account_number
        _cards: Dict[str, Card]          — O(1) by card_number
    """

    def __init__(self, name: str = "ATM Bank") -> None:
        """Initialize Bank with empty registries.

        Args:
            name: Name of the bank for display purposes.
        """
        self._name: str = name
        self._customers: Dict[str, Customer] = {}
        self._accounts: Dict[str, Account] = {}
        self._cards: Dict[str, Card] = {}

    @property
    def name(self) -> str:
        return self._name

    # ── Customer Management ──

    def add_customer(self, customer: Customer) -> None:
        """Register a customer in the bank.

        Time Complexity: O(1) average (dict insert)
        Space Complexity: O(1)
        """
        self._customers[customer.customer_id] = customer

    def find_customer(self, customer_id: str) -> Optional[Customer]:
        """Find a customer by ID.

        Time Complexity: O(1) average
        Space Complexity: O(1)
        """
        return self._customers.get(customer_id)

    def get_customer(self, customer_id: str) -> Customer:
        """Find a customer by ID, raise if not found.

        Time Complexity: O(1) average
        """
        customer = self._customers.get(customer_id)
        if customer is None:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")
        return customer

    def get_all_customers(self) -> List[Customer]:
        """Return list of all customers.

        Time Complexity: O(n) where n = number of customers
        Space Complexity: O(n)
        """
        return list(self._customers.values())

    @property
    def customer_count(self) -> int:
        """Return number of registered customers.

        Time Complexity: O(1)
        """
        return len(self._customers)

    # ── Account Management ──

    def add_account(self, account: Account) -> None:
        """Register an account in the bank.

        Business Rule:
            Account numbers must be unique.

        Raises:
            DuplicateAccountError: If account number already exists.

        Time Complexity: O(1) average
        """
        if account.account_number in self._accounts:
            raise DuplicateAccountError(
                f"Account {account.account_number} already exists"
            )
        self._accounts[account.account_number] = account

    def find_account(self, account_number: str) -> Optional[Account]:
        """Find an account by account number.

        Time Complexity: O(1) average
        Space Complexity: O(1)
        """
        return self._accounts.get(account_number)

    def get_account(self, account_number: str) -> Account:
        """Find an account, raise if not found.

        Time Complexity: O(1) average
        """
        account = self._accounts.get(account_number)
        if account is None:
            raise InvalidAccountError(f"Account {account_number} not found")
        return account

    def get_all_accounts(self) -> List[Account]:
        """Return list of all accounts.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """
        return list(self._accounts.values())

    def get_active_accounts(self) -> List[Account]:
        """Return list of all active accounts.

        Algorithm:
            Filter accounts where status == ACTIVE.

        Time Complexity: O(n)
        Space Complexity: O(n) in worst case
        """
        return [
            acc for acc in self._accounts.values()
            if acc.status == AccountStatus.ACTIVE
        ]

    @property
    def account_count(self) -> int:
        return len(self._accounts)

    # ── Card Management ──

    def add_card(self, card: Card) -> None:
        """Register a card in the bank.

        Time Complexity: O(1) average
        """
        self._cards[card.card_number] = card

    def find_card(self, card_number: str) -> Optional[Card]:
        """Find a card by card number.

        Time Complexity: O(1) average
        Space Complexity: O(1)
        """
        return self._cards.get(card_number)

    def get_card(self, card_number: str) -> Card:
        """Find a card, raise if not found.

        Time Complexity: O(1) average
        """
        card = self._cards.get(card_number)
        if card is None:
            raise InvalidCardError(f"Card {card_number} not found")
        return card

    def get_all_cards(self) -> List[Card]:
        """Return list of all cards.

        Time Complexity: O(n)
        """
        return list(self._cards.values())

    @property
    def card_count(self) -> int:
        return len(self._cards)

    def __repr__(self) -> str:
        return (
            f"Bank(name={self._name!r}, "
            f"customers={len(self._customers)}, "
            f"accounts={len(self._accounts)}, "
            f"cards={len(self._cards)})"
        )
