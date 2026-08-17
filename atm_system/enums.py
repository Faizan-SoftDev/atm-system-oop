"""
Enums for ATM System.

Purpose:
    Centralizes all enumeration types used across the system.

OOP Concept:
    Encapsulation of constants — enums prevent invalid status values
    and provide self-documenting code.

Business Rule:
    All status fields must use enum values, not arbitrary strings.
"""

from enum import Enum, auto


class AccountStatus(Enum):
    """Status of a bank account."""
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class CardStatus(Enum):
    """Status of an ATM card."""
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"


class TransactionType(Enum):
    """Type of financial transaction."""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"


class TransactionStatus(Enum):
    """Status of a transaction."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AccountType(Enum):
    """Type of bank account."""
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"


class ATMMenuItem(Enum):
    """Menu options available after authentication."""
    CHECK_BALANCE = 1
    DEPOSIT = 2
    WITHDRAW = 3
    TRANSFER = 4
    CHANGE_PIN = 5
    MINI_STATEMENT = 6
    EXIT = 7
