# ATM System — Complete OOP + DSA + Software Engineering Project

## 1. Project Overview

A console-based ATM System in Python demonstrating Object-Oriented Programming, Data Structures & Algorithms, business logic, and professional software engineering practices.

## 2. Project Goal

Demonstrate mastery of OOP concepts, DSA, algorithms, clean architecture, SOLID principles, testing, and professional Python — all within a realistic banking domain.

## 3. Features

- Savings and Current account types with different business rules
- ATM card authentication with 3-attempt blocking
- Deposit, Withdrawal, and Transfer transactions
- ATM cash management with denomination algorithm
- Daily limits with automatic reset
- Transaction fees
- Mini statement (last 5 transactions)
- Multiple accounts and cards per customer
- 194 automated test cases (82 unit/service + 112 integration/workflow)

## 4. Architecture

```
Console UI → ATM Service → Service Layer → Models
                         → CashDispenser
                         → Authentication
                         → Bank (Registry)
```

**Separation of Concerns**: UI, business logic, and data models are cleanly separated.

## 5. Folder Structure

```
atm_system/
├── __main__.py                # Module entry point (python -m atm_system)
├── main.py                    # Entry point, sample data, console menu
├── enums.py                   # All enumerations
├── models/
│   ├── account.py             # Abstract Account base class
│   ├── savings_account.py     # Savings account (min balance rules)
│   ├── current_account.py     # Current account (overdraft rules)
│   ├── customer.py            # Customer with O(1) lookups
│   ├── card.py                # ATM card with PIN verification
│   └── bank.py                # Entity registry (O(1) lookups)
├── transactions/
│   ├── transaction.py         # Abstract Transaction base class
│   ├── deposit.py             # Deposit transaction
│   ├── withdrawal.py          # Withdrawal transaction
│   └── transfer.py            # Atomic transfer transaction
├── services/
│   ├── atm_service.py         # ATM orchestrator (Facade pattern)
│   ├── authentication_service.py  # PIN verification
│   ├── account_service.py     # Balance, PIN change
│   ├── transaction_service.py # Transaction creation/execution
│   ├── statement_service.py   # Mini statement generation
│   └── cash_dispenser.py      # Cash inventory + denomination algo
├── exceptions/
│   └── exceptions.py          # 13 custom exception classes
├── utils/
│   ├── validators.py          # Input validation + business constants
│   └── transaction_id.py      # Unique ID generator
└── tests/
    ├── test_accounts.py       # 26 account unit tests
    ├── test_authentication.py # 10 authentication unit tests
    ├── test_transactions.py   # 16 transaction unit tests
    ├── test_atm.py            # 11 cash dispenser unit tests
    ├── test_services.py       # 19 service unit tests
    └── test_integration.py    # 112 integration/workflow tests
```

## 6. Class Diagram

```
                    ┌──────────────┐
                    │     Bank     │
                    │──────────────│
                    │ _customers{} │  ← O(1) dict lookup
                    │ _accounts{}  │  ← O(1) dict lookup
                    │ _cards{}     │  ← O(1) dict lookup
                    └──────┬───────┘
                           │ manages
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │ Customer │ │ Account  │ │   Card   │
       │──────────│ │ (ABC)    │ │──────────│
       │_accounts │ │──────────│ │_pin      │
       │_cards    │ │_balance  │ │_status   │
       └──────────┘ │_pin      │ │_customer │
                     └────┬─────┘ └──────────┘
                          ▲
              ┌───────────┴───────────┐
              │                       │
    ┌─────────────────┐   ┌─────────────────┐
    │ SavingsAccount  │   │ CurrentAccount  │
    │ min: Rs.5,000   │   │ overdraft:50,000│
    └─────────────────┘   └─────────────────┘

                    ┌──────────────┐
                    │ Transaction  │
                    │ (ABC)        │
                    │──────────────│
                    │ _id          │
                    │ _amount      │
                    │ _status      │
                    └──────┬───────┘
                           ▲
           ┌───────────────┼───────────────┐
           │               │               │
  ┌─────────────────┐ ┌────────────┐ ┌────────────┐
  │DepositTransaction│ │Withdrawal  │ │Transfer    │
  │                  │ │Transaction │ │Transaction │
  └─────────────────┘ └─────┬──────┘ └─────┬──────┘
                             │               │
                        ┌────┘          ┌────┘
                        ▼               ▼
                   ┌──────────┐   (two accounts)
                   │CashDispenser│
                   │_notes{}  │
                   └──────────┘

    ┌──────────┐
    │   ATM    │  ← Facade
    │──────────│
    │ HAS: Bank, Auth, Trans, Stmt, Cash
    └──────────┘
```

## 7. Class Responsibilities

| Class | Responsibility |
|-------|---------------|
| `Account` (ABC) | Abstract base: balance, PIN, status, daily limits |
| `SavingsAccount` | Min balance Rs. 5,000, max withdrawal Rs. 50,000 |
| `CurrentAccount` | Overdraft Rs. 50,000, no min balance |
| `Customer` | Owns accounts and cards, O(1) lookup |
| `Card` | PIN verification, attempt tracking, blocking |
| `Bank` | Entity registry, O(1) dictionary lookups |
| `Transaction` (ABC) | Abstract: ID, amount, status, timestamp |
| `DepositTransaction` | Credits amount to account |
| `WithdrawalTransaction` | Debits amount, checks ATM cash |
| `TransferTransaction` | Atomic debit+credit, rollback support |
| `CashDispenser` | Cash inventory, denomination algorithm |
| `ATM` | Orchestrator (Facade pattern) |
| `AuthenticationService` | Card validation, PIN verification |
| `AccountService` | Balance check, PIN change |
| `TransactionService` | Creates and executes transactions |
| `StatementService` | Mini statement generation |

## 8. OOP Concepts Demonstrated

| Concept | Where |
|---------|-------|
| **Abstraction** | `Account` (ABC), `Transaction` (ABC) — enforce interface contracts |
| **Encapsulation** | `_balance`, `_pin`, `_status` — protected via properties |
| **Inheritance** | `SavingsAccount → Account`, `DepositTransaction → Transaction` |
| **Polymorphism** | `calculate_withdrawal_limit()` returns different values per account type |
| **Composition** | `Account HAS [Transaction]`, `Customer HAS [Account, Card]` |
| **Association** | `Card BELONGS TO Customer`, `Account ASSOCIATED WITH Bank` |
| **Aggregation** | `Bank MANAGES collections` — entities exist independently |

## 9. SOLID Principles

| Principle | Implementation |
|-----------|---------------|
| **S** — Single Responsibility | Each class has one clear job |
| **O** — Open/Closed | New account/transaction types added without modifying existing code |
| **L** — Liskov Substitution | `SavingsAccount` and `CurrentAccount` work wherever `Account` is expected |
| **I** — Interface Segregation | No unnecessary large interfaces |
| **D** — Dependency Inversion | ATM receives all services via constructor injection |

## 10. Business Rules

| Rule | Value |
|------|-------|
| Min withdrawal | Rs. 500 |
| Max per transaction | Rs. 50,000 |
| Daily withdrawal limit | Rs. 100,000 |
| Daily transfer limit | Rs. 500,000 |
| Savings min balance | Rs. 5,000 |
| Current overdraft | Rs. 50,000 |
| Withdrawal fee | Rs. 50 |
| Transfer fee | Rs. 100 |
| Max PIN attempts | 3 |
| PIN format | Exactly 4 digits |

## 11. ATM Denomination Algorithm

**Algorithm**: Greedy Strategy

**Why Correct**: Our denominations (500, 1000, 5000) are canonical — each is a multiple of the next smaller one. Greedy is provably optimal for canonical systems.

```
Input: amount = 7,500
Denoms: 5000×10, 1000×30, 500×20

Step 1: 5000 → 7500//5000 = 1 note → remaining = 2500
Step 2: 1000 → 2500//1000 = 2 notes → remaining = 500
Step 3: 500  → 500//500 = 1 note → remaining = 0 ✓

Result: {5000:1, 1000:2, 500:1}
```

## 12. Complexity Analysis (Big-O)

### Data Structure Operations

| Operation | Data Structure | Time | Space | Notes |
|-----------|---------------|------|-------|-------|
| Account lookup (Bank) | `Dict[str, Account]` | **O(1)** avg | O(1) | Hash map by account number |
| Customer lookup (Bank) | `Dict[str, Customer]` | **O(1)** avg | O(1) | Hash map by customer ID |
| Card lookup (Bank) | `Dict[str, Card]` | **O(1)** avg | O(1) | Hash map by card number |
| Account lookup (Customer) | `Dict[str, Account]` | **O(1)** avg | O(1) | **OPTIMIZED** from O(n) |
| Card lookup (Customer) | `Dict[str, Card]` | **O(1)** avg | O(1) | **OPTIMIZED** from O(n) |
| PIN verification | String compare | **O(1)** | O(1) | Fixed 4-char string |
| Deposit | Single addition | **O(1)** | O(1) | Balance += amount |
| Withdrawal | Single subtraction | **O(1)** | O(1) | Balance -= amount |
| Balance check | Property access | **O(1)** | O(1) | Direct field read |

### Algorithm Operations

| Operation | Algorithm | Time | Space | Notes |
|-----------|-----------|------|-------|-------|
| Denomination calculation | Greedy | **O(d)** | O(d) | d=3 denominations |
| Daily limit reset | Date comparison | **O(1)** | O(1) | String compare |
| Transaction history (last 5) | Manual selection | **O(N)** | O(N) | N = total transactions (copy) |
| Transaction append | List append | **O(1)** amortized | O(1) | Python list |
| Mini statement formatting | String formatting | **O(5)** | O(5) | Bounded to 5 items |
| Transfer atomicity | Rollback | **O(1)** | O(1) | Save/restore balance |
| Daily limit calculation | Accumulation | **O(1)** | O(1) | Single counter lookup |
| Transaction ID generation | Counter | **O(1)** | O(1) | Date + increment |
| Fee calculation | Lookup | **O(1)** | O(1) | Switch on type |

### Optimization History

| Location | Before | After | Improvement |
|----------|--------|-------|-------------|
| `Customer.get_account()` | O(n) linear scan | **O(1)** dict lookup | n× faster |
| `Customer.get_card()` | O(n) linear scan | **O(1)** dict lookup | n× faster |
| `Bank` lookups | N/A (new) | **O(1)** dict lookup | Designed O(1) |
| `CashDispenser` | N/A (new) | **O(d)** greedy | Optimal for canonical denoms |

### Overall Complexity Summary

| Scenario | Dominant Operation | Total Complexity |
|----------|-------------------|-----------------|
| Authentication | PIN verify | **O(1)** |
| Single transaction | Balance update | **O(1)** |
| Transfer | Two balance updates | **O(1)** |
| Withdrawal with cash check | Denomination calc | **O(d)** ≈ O(1) |
| Mini statement | History copy | **O(N)** where N = total txns |
| Full ATM session (m operations) | Sum of operations | **O(m)** |

### Amortized Analysis

- **Transaction ID generation**: O(1) per call, O(1) amortized (date string caching)
- **Daily limit reset**: O(1) per access, triggered at most once per day per account
- **Cash dispenser total**: O(d) per call with d=3, effectively O(1)

### Why Dictionaries Over Lists

| Operation | List | Dict |
|-----------|------|------|
| Lookup by key | O(n) | **O(1)** avg |
| Insert | O(1) | O(1) avg |
| Delete by key | O(n) | **O(1)** avg |
| Iterate all | O(n) | O(n) |

**Tradeoff**: O(n) extra space for hash table overhead, justified by frequent lookups.

## 13. Testing

194 automated test cases across 6 test files.

| File | Tests | Type | Coverage |
|------|-------|------|----------|
| `test_accounts.py` | 26 | Unit | Savings, Current, polymorphism, PIN |
| `test_authentication.py` | 10 | Unit | PIN attempts, blocking, validation |
| `test_transactions.py` | 16 | Unit | Deposit, withdrawal, transfer, atomicity |
| `test_atm.py` | 11 | Unit | Cash dispenser, denomination algorithm |
| `test_services.py` | 19 | Unit | Statements, Bank lookups, Customer optimization |
| `test_integration.py` | 112 | Integration | Full ATM workflow end-to-end |

### Requirement Traceability Matrix

| Requirement | Test Class | Tests |
|-------------|-----------|-------|
| Card insertion & authentication | `TestAuthenticationWorkflow` | 11 tests |
| Account selection (multi-account) | `TestAccountSelection` | 6 tests |
| Balance inquiry | `TestBalanceInquiry` | 5 tests |
| Deposit workflow | `TestDepositWorkflow` | 6 tests |
| Withdrawal workflow | `TestWithdrawalWorkflow` | 17 tests |
| Transfer workflow | `TestTransferWorkflow` | 9 tests |
| PIN change | `TestChangePINWorkflow` | 6 tests |
| Mini statement | `TestMiniStatementWorkflow` | 4 tests |
| Daily limit tracking | `TestDailyLimitTracking` | 3 tests |
| Transaction fees | `TestTransactionFees` | 6 tests |
| Multiple accounts per customer | `TestMultipleAccounts` | 4 tests |
| Multiple cards per customer | `TestMultipleCards` | 3 tests |
| ATM cash management | `TestATMCashManagement` | 4 tests |
| Exit / logout | `TestExitLogout` | 3 tests |
| Boundary conditions | `TestBoundaryConditions` | 12 tests |
| End-to-end workflows | `TestEndToEndWorkflow` | 5 tests |
| Error handling | `TestErrorHandling` | 8 tests |

### Run Tests

```bash
# Run all tests
python3 -m pytest -v

# Run only unit/service tests
python3 -m pytest atm_system/tests/ --ignore=atm_system/tests/test_integration.py -v

# Run only integration tests
python3 -m pytest atm_system/tests/test_integration.py -v

# Run with coverage report
python3 -m pytest --cov=atm_system --cov-report=term-missing -v
```

## 14. Sample Usage

```bash
# Run as module (recommended)
python3 -m atm_system

# Or run main.py directly
python3 -m atm_system.main
```

**Demo Credentials:**
- Card: `CARD-10001` | PIN: `1234` (Muhammad Ali — Savings + Current)
- Card: `CARD-20001` | PIN: `5678` (Ahmed Khan — Savings only)

## 15. Educational vs Production

| Aspect | This Project | Production |
|--------|-------------|------------|
| Storage | In-memory | Database (PostgreSQL) |
| PIN | Plaintext compare | Bcrypt hash |
| Auth | Single factor | MFA + OTP |
| Concurrency | None | Database transactions + locks |
| Logging | Print statements | Structured logging (ELK) |
| Audit | None | Full audit trail |
| Fraud detection | None | ML-based monitoring |
| Encryption | None | TLS + encryption at rest |

## 16. Production Considerations

This project is an educational implementation. A production ATM system would additionally require:

- Secure credential storage (bcrypt/argon2 hashing)
- TLS encryption for all communications
- Database transactions with ACID guarantees
- Concurrency control (optimistic/pessimistic locking)
- Comprehensive audit logging
- Fraud detection algorithms
- Hardware integration (card reader, cash dispenser, receipt printer)
- Network connectivity to bank core systems
- Compliance with PCI-DSS standards

**Do NOT use this code as-is for any production banking system.**
