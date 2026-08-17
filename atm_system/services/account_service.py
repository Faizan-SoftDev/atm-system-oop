"""
Account Service for ATM System.

Purpose:
    Handles account-level operations that don't belong to TransactionService.

OOP Concept:
    Single Responsibility — account queries and PIN management.
    Service Layer — separates presentation from business logic.
"""

from typing import List, Optional

from atm_system.enums import AccountStatus
from atm_system.exceptions.exceptions import (
    AccountInactiveError,
    InvalidPINError,
)
from atm_system.models.account import Account
from atm_system.utils.validators import validate_pin


class AccountService:
    """Service for account-level operations."""

    def __init__(self) -> None:
        pass

    def check_balance(self, account: Account) -> float:
        """Return the current balance of an account.

        Args:
            account: The account to check.

        Returns:
            Current balance.

        Raises:
            AccountInactiveError: If account is not active.

        Time Complexity: O(1)
        """
        account._check_active()
        return account.balance

    def change_pin(
        self, account: Account, old_pin: str, new_pin: str
    ) -> None:
        """Change the PIN for an account.

        Algorithm:
            1. Validate new PIN format.
            2. Verify old PIN matches.
            3. Update to new PIN.

        Args:
            account: The account whose PIN to change.
            old_pin: Current PIN.
            new_pin: New PIN (must be 4 digits).

        Raises:
            InvalidPINError: If old PIN is incorrect.
            PINValidationError: If new PIN format is invalid.

        Time Complexity: O(1)
        """
        validate_pin(new_pin)
        account.change_pin(old_pin, new_pin)

    def get_account_info(self, account: Account) -> dict:
        """Return account information as a dictionary.

        WHY dict: Useful for display and serialization without
        exposing internal object state directly.

        Time Complexity: O(1)
        """
        return {
            "account_number": account.account_number,
            "account_holder": account.account_holder,
            "balance": account.balance,
            "account_type": account.account_type.value,
            "status": account.status.value,
        }
