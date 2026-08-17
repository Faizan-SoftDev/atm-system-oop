"""
Custom exceptions for ATM System.

Purpose:
    Provides meaningful, specific exception types instead of generic Exception.
    Each exception represents a distinct business error condition.

OOP Concept:
    Abstraction — hides implementation details while communicating intent.
    Inheritance — all exceptions extend ATMError for unified catching.

Business Rule:
    Every business validation failure raises a specific exception,
    enabling the service layer to handle errors appropriately.
"""


class ATMError(Exception):
    """Base exception for all ATM system errors.

    WHY: Allows catching all ATM-specific errors with a single handler,
    while still allowing granular handling of specific error types.
    """

    def __init__(self, message: str = "An ATM error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class InvalidPINError(ATMError):
    """Raised when a PIN is incorrect.

    Business Rule: PIN must match the stored hash exactly.
    """

    def __init__(self, message: str = "Invalid PIN entered") -> None:
        super().__init__(message)


class CardBlockedError(ATMError):
    """Raised when a blocked card is used for any operation.

    Business Rule: After 3 incorrect PIN attempts, card is permanently
    blocked for the session. Even correct PIN cannot bypass this.
    """

    def __init__(self, message: str = "Card is blocked. Please contact your bank.") -> None:
        super().__init__(message)


class InsufficientBalanceError(ATMError):
    """Raised when account balance is insufficient for a transaction.

    Business Rule: Balance cannot go below minimum (Savings) or
    beyond overdraft limit (Current).
    """

    def __init__(self, message: str = "Insufficient balance for this transaction") -> None:
        super().__init__(message)


class InsufficientATMFundsError(ATMError):
    """Raised when ATM cannot dispense the requested amount.

    Business Rule: ATM must have enough cash AND correct denominations.
    Account balance is NOT deducted if ATM cannot physically dispense.
    """

    def __init__(self, message: str = "ATM has insufficient funds to complete this transaction") -> None:
        super().__init__(message)


class InvalidAmountError(ATMError):
    """Raised when a transaction amount violates business rules.

    Business Rule: Amounts must be positive, within min/max limits,
    and must be valid numbers.
    """

    def __init__(self, message: str = "Invalid transaction amount") -> None:
        super().__init__(message)


class AccountInactiveError(ATMError):
    """Raised when an operation is attempted on a frozen/closed account.

    Business Rule: Only ACTIVE accounts can perform transactions.
    """

    def __init__(self, message: str = "Account is not active. Cannot perform transaction.") -> None:
        super().__init__(message)


class DailyLimitExceededError(ATMError):
    """Raised when daily withdrawal or transfer limit is exceeded.

    Business Rule: Daily withdrawal limit = Rs. 100,000
                    Daily transfer limit = Rs. 500,000
    """

    def __init__(self, message: str = "Daily transaction limit exceeded") -> None:
        super().__init__(message)


class InvalidAccountError(ATMError):
    """Raised when an account number does not exist in the system.

    Business Rule: All account operations require a valid, registered account.
    """

    def __init__(self, message: str = "Account not found in the system") -> None:
        super().__init__(message)


class DuplicateAccountError(ATMError):
    """Raised when attempting to add an account that already exists."""

    def __init__(self, message: str = "Account already exists in the system") -> None:
        super().__init__(message)


class InvalidCardError(ATMError):
    """Raised when a card number is not recognized."""

    def __init__(self, message: str = "Card not found in the system") -> None:
        super().__init__(message)


class CustomerNotFoundError(ATMError):
    """Raised when a customer ID is not found."""

    def __init__(self, message: str = "Customer not found in the system") -> None:
        super().__init__(message)


class SameAccountTransferError(ATMError):
    """Raised when a user tries to transfer to the same account."""

    def __init__(self, message: str = "Cannot transfer to the same account") -> None:
        super().__init__(message)


class DenominationError(ATMError): 
    """Raised when the requested amount cannot be dispensed with available denominations.

    Business Rule: Even if ATM total cash >= requested amount,
    dispensing fails if exact denomination combination is unavailable.
    """

    def __init__(self, message: str = "Cannot dispense exact amount with available denominations") -> None:
        super().__init__(message)


class PINValidationError(ATMError):
    """Raised when a new PIN does not meet security requirements.

    Business Rule: PIN must be exactly 4 digits, numeric only, not empty.
    """

    def __init__(self, message: str = "PIN does not meet security requirements") -> None:
        super().__init__(message)
