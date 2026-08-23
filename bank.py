"""
bank.py — Stage 2a: The Bank Backend
Banking Assistant · Exology Pioneer Program Week 2

In-memory mock bank. No database, no file — exactly as required.
Exactly 3 customers (A-1, A-2, A-3), exactly 3 transactions each.
"""

from copy import deepcopy

_INITIAL_STATE = {
    "A-1": {
        "account_id": "A-1",
        "name": "Layla Hassan",
        "balance": 420.50,
        "currency": "USD",
        "daily_limit": 100.0,  # required: A-1 must have daily_limit = 100.0
        "transactions": [
            {"date": "2026-08-10", "description": "Grocery Mart",       "amount": -32.10},
            {"date": "2026-08-12", "description": "Salary deposit",     "amount": 500.00},
            {"date": "2026-08-14", "description": "Coffee Shop",        "amount": -4.75},
        ],
    },
    "A-2": {
        "account_id": "A-2",
        "name": "Omar Fathy",
        "balance": 1875.00,
        "currency": "USD",
        "daily_limit": 500.0,
        "transactions": [
            {"date": "2026-08-09", "description": "Rent payment",       "amount": -650.00},
            {"date": "2026-08-11", "description": "Freelance payment",  "amount": 900.00},
            {"date": "2026-08-15", "description": "Electronics Store",  "amount": -120.00},
        ],
    },
    "A-3": {
        "account_id": "A-3",
        "name": "Nour El-Sayed",
        "balance": 60.25,
        "currency": "USD",
        "daily_limit": 250.0,
        "transactions": [
            {"date": "2026-08-08", "description": "ATM withdrawal",     "amount": -40.00},
            {"date": "2026-08-13", "description": "Refund - Zara",      "amount": 25.00},
            {"date": "2026-08-15", "description": "Pharmacy",           "amount": -15.00},
        ],
    },
}

# Mutable in-memory store, seeded fresh each process start.
_accounts = deepcopy(_INITIAL_STATE)

# Tracks cumulative transferred-out amount per account per calendar day,
# used by the guarded transfer tool for the cumulative daily cap (stretch).
_daily_transferred = {}


def reset():
    """Reset the mock bank back to its initial state. Useful between test
    cases in tests.py so one test's transfer doesn't leak into the next."""
    global _accounts, _daily_transferred
    _accounts = deepcopy(_INITIAL_STATE)
    _daily_transferred = {}


def get_all_accounts():
    return _accounts


def get_customer(account_id):
    return _accounts.get(account_id)


if __name__ == "__main__":
    print("=== Mock Bank — All Customers ===\n")
    for acc_id, acc in _accounts.items():
        print(f"Account: {acc['account_id']}  ({acc['name']})")
        print(f"  Balance:      {acc['balance']:.2f} {acc['currency']}")
        print(f"  Daily limit:  {acc['daily_limit']}")
        print("  Recent transactions:")
        for tx in acc["transactions"]:
            print(f"    {tx['date']}  {tx['description']:<22} {tx['amount']:+.2f}")
        print()
