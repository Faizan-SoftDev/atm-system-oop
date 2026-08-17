"""
Main entry point for ATM System.

Purpose:
    Initializes all components, creates sample data, and runs
    the console-based ATM menu loop.

OOP Concept:
    Dependency Injection — all components are wired together here.
    Separation of Concerns — main.py only handles initialization
    and UI; all business logic is in services/models.
"""

from typing import Optional

from atm_system.enums import ATMMenuItem
from atm_system.exceptions.exceptions import ATMError
from atm_system.models.bank import Bank
from atm_system.services.account_service import AccountService
from atm_system.services.atm_service import ATM
from atm_system.services.authentication_service import AuthenticationService
from atm_system.services.cash_dispenser import CashDispenser
from atm_system.services.statement_service import StatementService
from atm_system.services.transaction_service import TransactionService


def create_sample_data(bank: Bank) -> None:
    """Create demonstration data for the ATM system.

    Sample Data:
        Customer 1: Muhammad Ali (CUS-001)
            Savings: ACC-1001, Balance Rs. 100,000
            Current: ACC-1002, Balance Rs. 50,000
            Card: CARD-10001, PIN: 1234

        Customer 2: Ahmed Khan (CUS-002)
            Savings: ACC-2001, Balance Rs. 75,000
            Card: CARD-20001, PIN: 5678
    """
    from atm_system.models.card import Card
    from atm_system.models.current_account import CurrentAccount
    from atm_system.models.customer import Customer
    from atm_system.models.savings_account import SavingsAccount

    # ── Customer 1: Muhammad Ali ──
    customer1 = Customer(
        customer_id="CUS-001",
        name="Muhammad Ali",
        email="muhammad.ali@bank.com",
        phone="+92-300-1234567",
    )

    savings1 = SavingsAccount(
        account_number="ACC-1001",
        account_holder="Muhammad Ali",
        initial_balance=100_000,
        pin="1234",
    )

    current1 = CurrentAccount(
        account_number="ACC-1002",
        account_holder="Muhammad Ali",
        initial_balance=50_000,
        pin="1234",
    )

    card1 = Card(
        card_number="CARD-10001",
        card_holder="Muhammad Ali",
        pin="1234",
    )

    # Link card to accounts
    card1.link_account(savings1)
    card1.link_account(current1)

    # Link card and accounts to customer
    customer1.add_account(savings1)
    customer1.add_account(current1)
    customer1.add_card(card1)
    card1.set_customer(customer1)

    # Register in bank
    bank.add_customer(customer1)
    bank.add_account(savings1)
    bank.add_account(current1)
    bank.add_card(card1)

    # ── Customer 2: Ahmed Khan ──
    customer2 = Customer(
        customer_id="CUS-002",
        name="Ahmed Khan",
        email="ahmed.khan@bank.com",
        phone="+92-321-7654321",
    )

    savings2 = SavingsAccount(
        account_number="ACC-2001",
        account_holder="Ahmed Khan",
        initial_balance=75_000,
        pin="5678",
    )

    card2 = Card(
        card_number="CARD-20001",
        card_holder="Ahmed Khan",
        pin="5678",
    )

    card2.link_account(savings2)
    customer2.add_account(savings2)
    customer2.add_card(card2)
    card2.set_customer(customer2)

    bank.add_customer(customer2)
    bank.add_account(savings2)
    bank.add_card(card2)


def create_atm(bank: Bank) -> ATM:
    """Create and wire up all ATM services.

    Dependency Injection:
        Each service receives only the dependencies it needs.

    Time Complexity: O(1) — initialization
    """
    auth_service = AuthenticationService()
    cash_dispenser = CashDispenser()
    transaction_service = TransactionService(cash_dispenser)
    account_service = AccountService()
    statement_service = StatementService()

    atm = ATM(
        bank=bank,
        auth_service=auth_service,
        transaction_service=transaction_service,
        account_service=account_service,
        statement_service=statement_service,
        cash_dispenser=cash_dispenser,
    )

    return atm


def print_header() -> None:
    """Print the ATM header."""
    print()
    print("=" * 44)
    print("          WELCOME TO ATM SYSTEM")
    print("=" * 44)


def print_menu() -> None:
    """Print the main ATM menu.

    Options correspond to ATMMenuItem enum.
    """
    print()
    print("-" * 44)
    print("              MAIN MENU")
    print("-" * 44)
    print("  1. Check Balance")
    print("  2. Deposit")
    print("  3. Withdraw")
    print("  4. Transfer Money")
    print("  5. Change PIN")
    print("  6. Mini Statement")
    print("  7. Exit")
    print("-" * 44)


def get_account_choice(atm: ATM) -> Optional[str]:
    """If multiple accounts, let user select one.

    Returns:
        Selected account number or None.
    """
    accounts = atm.get_linked_accounts()

    if len(accounts) == 0:
        print("  No accounts linked to this card.")
        return None

    if len(accounts) == 1:
        return accounts[0].account_number

    print()
    print("  Select Account:")
    print("  " + "-" * 36)
    for i, acc in enumerate(accounts, 1):
        print(
            f"  {i}. {acc.account_type.value.title():<10} — "
            f"{acc.account_number}"
        )
    print("  " + "-" * 36)

    while True:
        try:
            choice = int(input("  Enter choice (number): "))
            if 1 <= choice <= len(accounts):
                return accounts[choice - 1].account_number
            print(f"  Please enter 1 to {len(accounts)}")
        except ValueError:
            print("  Invalid input. Enter a number.")


def run_atm() -> None:
    """Main ATM loop."""
    # Initialize
    bank = Bank("ATM Bank Pakistan")
    create_sample_data(bank)
    atm = create_atm(bank)

    print_header()
    print()
    print("  Demo Credentials:")
    print("  Card: CARD-10001 | PIN: 1234")
    print("  Card: CARD-20001 | PIN: 5678")
    print()

    while True:
        try:
            # ── Step 1: Card Insertion ──
            print()
            card_num = input("  Enter card number (or 'quit' to exit): ").strip()
            if card_num.lower() == "quit":
                print("\n  Thank you for using ATM. Goodbye!")
                break

            card = atm.insert_card(card_num)
            print(f"\n  Welcome, {card.card_holder}!")

            # ── Step 2: PIN Authentication ──
            max_attempts = 3
            for attempt in range(max_attempts):
                pin = input(f"  Enter PIN (attempt {attempt + 1}/{max_attempts}): ").strip()
                try:
                    atm.authenticate(pin)
                    print("  Authentication successful!")
                    break
                except ATMError as e:
                    print(f"  Error: {e.message}")
                    if attempt < max_attempts - 1:
                        remaining = max_attempts - attempt - 1
                        print(f"  {remaining} attempt(s) remaining.")
                    else:
                        print("  Card has been blocked.")
                        atm.eject_card()
                        break
            else:
                continue

            # ── Step 3: Account Selection ──
            account_number = get_account_choice(atm)
            if account_number is None:
                atm.eject_card()
                continue

            atm.select_account(account_number)
            print(f"  Selected: {account_number}")

            # ── Step 4: Main Menu Loop ──
            while True:
                print_menu()
                choice = input("  Enter your choice (1-7): ").strip()

                try:
                    if choice == "1":
                        # Check Balance
                        balance = atm.check_balance()
                        print(f"\n  Current Balance: Rs. {balance:,.0f}")

                    elif choice == "2":
                        # Deposit
                        amount = float(input("  Enter deposit amount: Rs. "))
                        txn = atm.deposit(amount)
                        print(f"\n  Deposit Successful!")
                        print(f"  Transaction ID: {txn.transaction_id}")
                        print(f"  Amount: Rs. {txn.amount:,.0f}")
                        print(f"  New Balance: Rs. {atm.check_balance():,.0f}")

                    elif choice == "3":
                        # Withdraw
                        amount = float(input("  Enter withdrawal amount: Rs. "))
                        txn = atm.withdraw(amount)
                        print(f"\n  Withdrawal Successful!")
                        print(f"  Transaction ID: {txn.transaction_id}")
                        print(f"  Amount: Rs. {txn.amount:,.0f}")
                        fee = txn.total_deduction - txn.amount
                        if fee > 0:
                            print(f"  Fee: Rs. {fee:,.0f}")
                            print(f"  Total Deducted: Rs. {txn.total_deduction:,.0f}")
                        print(f"  New Balance: Rs. {atm.check_balance():,.0f}")

                    elif choice == "4":
                        # Transfer
                        receiver = input("  Enter receiver account number: ").strip()
                        amount = float(input("  Enter transfer amount: Rs. "))
                        txn = atm.transfer(receiver, amount)
                        print(f"\n  Transfer Successful!")
                        print(f"  Transaction ID: {txn.transaction_id}")
                        print(f"  Amount: Rs. {txn.amount:,.0f}")
                        print(f"  Fee: Rs. 100")
                        print(f"  Total Deducted: Rs. {txn.total_sender_deduction:,.0f}")
                        print(f"  New Balance: Rs. {atm.check_balance():,.0f}")

                    elif choice == "5":
                        # Change PIN
                        old_pin = input("  Enter current PIN: ").strip()
                        new_pin = input("  Enter new PIN: ").strip()
                        confirm = input("  Confirm new PIN: ").strip()
                        if new_pin != confirm:
                            print("  PINs do not match. Try again.")
                        else:
                            atm.change_pin(old_pin, new_pin)
                            print("  PIN changed successfully!")

                    elif choice == "6":
                        # Mini Statement
                        statement = atm.get_mini_statement()
                        print(statement)

                    elif choice == "7":
                        # Exit
                        print("\n  Session ended. Card ejected.")
                        atm.eject_card()
                        break

                    else:
                        print("  Invalid choice. Enter 1-7.")

                except ATMError as e:
                    print(f"\n  Transaction Failed: {e.message}")
                except ValueError:
                    print("  Invalid amount. Please enter a number.")

        except ATMError as e:
            print(f"  Error: {e.message}")
        except KeyboardInterrupt:
            print("\n\n  ATM session terminated. Goodbye!")
            break
        except Exception as e:
            print(f"  Unexpected error: {e}")


if __name__ == "__main__":
    run_atm()
