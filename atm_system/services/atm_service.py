"""
ATM Service for ATM System.

Purpose:
    Central orchestrator that ties together all services.
    Represents the physical ATM machine's software controller.

OOP Concept:
    Composition — ATM HAS a Bank, AuthenticationService, TransactionService,
    StatementService, CashDispenser.
    Dependency Injection — all dependencies are injected, not created internally.
    Facade Pattern — provides a simplified interface to complex subsystems.
"""

from typing import Optional

from atm_system.enums import ATMMenuItem
from atm_system.exceptions.exceptions import ATMError
from atm_system.models.account import Account
from atm_system.models.bank import Bank
from atm_system.models.card import Card
from atm_system.services.account_service import AccountService
from atm_system.services.authentication_service import AuthenticationService
from atm_system.services.cash_dispenser import CashDispenser
from atm_system.services.statement_service import StatementService
from atm_system.services.transaction_service import TransactionService


class ATM:
    """ATM controller — orchestrates all ATM operations.

    Composition:
        ATM HAS a Bank
        ATM HAS an AuthenticationService
        ATM HAS a TransactionService
        ATM HAS a StatementService
        ATM HAS a CashDispenser

    Dependency Injection:
        All dependencies are passed via constructor.
        This makes ATM testable — mock any dependency.

    State:
        _current_card: Card currently inserted (if any)
        _authenticated: Whether PIN verification succeeded
        _selected_account: Account currently selected for operations
    """

    def __init__(
        self,
        bank: Bank,
        auth_service: AuthenticationService,
        transaction_service: TransactionService,
        account_service: AccountService,
        statement_service: StatementService,
        cash_dispenser: CashDispenser,
    ) -> None:
        """Initialize ATM with all required services.

        Args:
            bank: The bank registry.
            auth_service: Authentication service.
            transaction_service: Transaction service.
            account_service: Account service.
            statement_service: Statement service.
            cash_dispenser: Cash dispenser.
        """
        self._bank: Bank = bank
        self._auth_service: AuthenticationService = auth_service
        self._transaction_service: TransactionService = transaction_service
        self._account_service: AccountService = account_service
        self._statement_service: StatementService = statement_service
        self._cash_dispenser: CashDispenser = cash_dispenser

        # Session state
        self._current_card: Optional[Card] = None
        self._current_account: Optional[Account] = None
        self._authenticated: bool = False

    # ── Session Management ──

    def insert_card(self, card_number: str) -> Card:
        """Insert a card into the ATM.

        Args:
            card_number: The card number to look up.

        Returns:
            The Card object if found.

        Raises:
            InvalidCardError: If card not found.
            CardBlockedError: If card is blocked.
        """
        card = self._bank.get_card(card_number)
        self._auth_service.validate_card(card)
        self._current_card = card
        self._authenticated = False
        self._current_account = None
        return card

    def authenticate(self, pin: str) -> bool:
        """Authenticate with PIN.

        Args:
            pin: The PIN entered.

        Returns:
            True if authentication succeeded.

        Raises:
            CardBlockedError: If card is blocked.
            InvalidPINError: If PIN is wrong (and card not yet blocked).
        """
        if self._current_card is None:
            from atm_system.exceptions.exceptions import InvalidCardError
            raise InvalidCardError("No card inserted")

        result = self._auth_service.authenticate_pin(self._current_card, pin)
        if not result:
            from atm_system.exceptions.exceptions import InvalidPINError
            raise InvalidPINError("Invalid PIN entered")
        self._authenticated = True
        return True

    def select_account(self, account_number: str) -> Account:
        """Select an account for operations.

        Args:
            account_number: Account number to select.

        Returns:
            The selected Account.

        Raises:
            InvalidAccountError: If account not found.
        """
        self._require_authentication()

        if self._current_card is None:
            raise ATMError("No card inserted")

        # Verify the account is linked to this card
        linked_accounts = self._current_card.get_linked_accounts()
        for acc in linked_accounts:
            if acc.account_number == account_number:
                self._current_account = acc
                return acc

        from atm_system.exceptions.exceptions import InvalidAccountError
        raise InvalidAccountError(
            f"Account {account_number} is not linked to this card"
        )

    def get_linked_accounts(self):
        """Return accounts linked to the current card."""
        self._require_authentication()
        if self._current_card is None:
            return []
        return self._current_card.get_linked_accounts()

    def _require_authentication(self) -> None:
        """Raise if not authenticated."""
        if not self._authenticated:
            raise ATMError("Not authenticated. Please enter PIN first.")

    def _require_account(self) -> Account:
        """Raise if no account selected, else return it."""
        self._require_authentication()
        if self._current_account is None:
            raise ATMError("No account selected")
        return self._current_account

    # ── Operations ──

    def check_balance(self) -> float:
        """Check balance of selected account.

        Time Complexity: O(1)
        """
        account = self._require_account()
        return self._account_service.check_balance(account)

    def deposit(self, amount: float):
        """Deposit into selected account.

        Time Complexity: O(1)
        """
        account = self._require_account()
        return self._transaction_service.deposit(account, amount)

    def withdraw(self, amount: float):
        """Withdraw from selected account.

        Time Complexity: O(d) for denomination
        """
        account = self._require_account()
        return self._transaction_service.withdraw(account, amount)

    def transfer(self, receiver_account_number: str, amount: float):
        """Transfer from selected account to another.

        Time Complexity: O(1)
        """
        sender = self._require_account()
        receiver = self._bank.get_account(receiver_account_number)
        return self._transaction_service.transfer(sender, receiver, amount)

    def change_pin(self, old_pin: str, new_pin: str) -> None:
        """Change PIN for the card's owner account.

        Time Complexity: O(1)
        """
        account = self._require_account()
        self._account_service.change_pin(account, old_pin, new_pin)

    def get_mini_statement(self) -> str:
        """Get mini statement for selected account.

        Time Complexity: O(N) where N = transaction count
        """
        account = self._require_account()
        return self._statement_service.format_mini_statement(account)

    def get_atm_status(self) -> str:
        """Return formatted ATM cash status.

        Time Complexity: O(d)
        """
        return self._cash_dispenser.get_note_display()

    def eject_card(self) -> None:
        """Eject the card and reset session."""
        self._current_card = None
        self._current_account = None
        self._authenticated = False

    def __repr__(self) -> str:
        return (
            f"ATM(bank={self._bank.name!r}, "
            f"authenticated={self._authenticated})"
        )
