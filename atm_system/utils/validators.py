"""
Validators for ATM System.

Purpose:
    Centralizes all input validation logic.
    Ensures data integrity before business operations.

OOP Concept:
    Single Responsibility — validation is isolated from business logic.
    Reusability — validators are called from multiple services.

Business Rule:
    All user inputs must be validated BEFORE any business operation
    modifies system state.
"""

from atm_system.exceptions.exceptions import InvalidAmountError, PINValidationError


# Constants for business rules
MIN_DEPOSIT_AMOUNT = 1.0
MIN_WITHDRAWAL_AMOUNT = 500.0
MAX_WITHDRAWAL_AMOUNT = 50_000.0
DAILY_WITHDRAWAL_LIMIT = 100_000.0
DAILY_TRANSFER_LIMIT = 500_000.0
MIN_BALANCE_SAVINGS = 5_000.0
OVERDRAFT_LIMIT_CURRENT = 50_000.0
WITHDRAWAL_FEE = 50.0
TRANSFER_FEE = 100.0
PIN_LENGTH = 4
MAX_FAILED_PIN_ATTEMPTS = 3


def validate_amount(amount: float, context: str = "transaction") -> None:
    """Validate that an amount is a positive number.

    Args:
        amount: The amount to validate.
        context: Description for error message.

    Raises:
        InvalidAmountError: If amount is not positive.

    Algorithm:
        1. Check if amount is numeric (float/int).
        2. Check if amount > 0.
        3. Raise if either check fails.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    if not isinstance(amount, (int, float)):
        raise InvalidAmountError(f"{context}: Amount must be a number")
    if amount <= 0:
        raise InvalidAmountError(f"{context}: Amount must be positive (got {amount})")


def validate_pin(pin: str) -> None:
    """Validate PIN format against security rules.

    Rules:
        - Must not be empty.
        - Must be exactly 4 characters.
        - Must contain only digits.

    Args:
        pin: The PIN string to validate.

    Raises:
        PINValidationError: If PIN fails any validation rule.

    Algorithm:
        1. Check non-empty.
        2. Check length == 4.
        3. Check all characters are digits.

    Time Complexity: O(1) — PIN is fixed length (4 chars)
    Space Complexity: O(1)
    """
    if not pin:
        raise PINValidationError("PIN cannot be empty")
    if len(pin) != PIN_LENGTH:
        raise PINValidationError(
            f"PIN must be exactly {PIN_LENGTH} digits (got {len(pin)})"
        )
    if not pin.isdigit():
        raise PINValidationError("PIN must contain only numeric digits")


def validate_withdrawal_amount(amount: float) -> None:
    """Validate withdrawal amount against all business rules.

    Checks:
        1. Amount is positive.
        2. Amount >= minimum withdrawal (Rs. 500).
        3. Amount <= maximum withdrawal (Rs. 50,000).

    Args:
        amount: The withdrawal amount.

    Raises:
        InvalidAmountError: If any withdrawal rule is violated.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    validate_amount(amount, "Withdrawal")
    if amount < MIN_WITHDRAWAL_AMOUNT:
        raise InvalidAmountError(
            f"Withdrawal amount must be at least Rs. {MIN_WITHDRAWAL_AMOUNT:,.0f} "
            f"(got Rs. {amount:,.0f})"
        )
    if amount > MAX_WITHDRAWAL_AMOUNT:
        raise InvalidAmountError(
            f"Withdrawal amount cannot exceed Rs. {MAX_WITHDRAWAL_AMOUNT:,.0f} "
            f"(got Rs. {amount:,.0f})"
        )


def validate_deposit_amount(amount: float) -> None:
    """Validate deposit amount.

    Args:
        amount: The deposit amount.

    Raises:
        InvalidAmountError: If amount is not positive.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    if amount <= 0:
        raise InvalidAmountError(
            f"Deposit amount must be positive (got Rs. {amount:,.0f})"
        )
