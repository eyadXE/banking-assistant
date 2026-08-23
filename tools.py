"""
tools.py — Stages 2-3: Give It Hands / Reach the Real World
Banking Assistant · Exology Pioneer Program Week 2

Tool functions + their OpenAI-style function-calling declarations.
The guards (limit checks, unknown-account handling) live in CODE here,
never in a prompt — assistant.py's system prompt states the rule too, but
this file is what actually enforces it.
"""

import datetime
import requests

import bank


# ---------------------------------------------------------------------------
# 2b — Read-only tools
# ---------------------------------------------------------------------------

def get_account(account_id):
    """Returns balance, currency, daily_limit for an account.
    Unknown id returns an error value (dict with 'error'), never raises."""
    acc = bank.get_customer(account_id)
    if acc is None:
        return {"error": f"No account found with id '{account_id}'."}
    return {
        "account_id": acc["account_id"],
        "name": acc["name"],
        "balance": acc["balance"],
        "currency": acc["currency"],
        "daily_limit": acc["daily_limit"],
    }


def get_recent_transactions(account_id):
    """Returns the customer's recent transactions.
    Unknown id returns an error value, never raises."""
    acc = bank.get_customer(account_id)
    if acc is None:
        return {"error": f"No account found with id '{account_id}'."}
    return {
        "account_id": account_id,
        "transactions": acc["transactions"],
    }


# ---------------------------------------------------------------------------
# 2c — The guarded transfer (the guard lives in code, not the prompt)
# ---------------------------------------------------------------------------

def transfer_money(from_account, to_account, amount):
    """
    Transfers `amount` from from_account to to_account.

    Guards, enforced in code:
      - unknown from_account -> rejected
      - amount above from_account's daily_limit (single transfer OR
        cumulative same-day total) -> refused, tells the model to escalate
      - amount above available balance -> refused
      - otherwise -> executes: balance changes + new transaction recorded
    """
    acc = bank.get_customer(from_account)
    if acc is None:
        return {"status": "rejected", "reason": f"Unknown account '{from_account}'."}

    if amount <= 0:
        return {"status": "rejected", "reason": "Transfer amount must be positive."}

    today = datetime.date.today().isoformat()
    already_sent_today = bank._daily_transferred.get((from_account, today), 0.0)
    projected_total = already_sent_today + amount

    # Per-transfer AND cumulative daily cap (stretch goal) — both checked in code.
    if amount > acc["daily_limit"] or projected_total > acc["daily_limit"]:
        return {
            "status": "escalate",
            "reason": (
                f"Transfer of {amount} exceeds the daily limit of "
                f"{acc['daily_limit']} for account {from_account} "
                f"(already sent {already_sent_today} today). "
                f"This must be escalated to a human agent for approval."
            ),
        }

    if amount > acc["balance"]:
        return {
            "status": "rejected",
            "reason": f"Insufficient balance: {acc['balance']} available, {amount} requested.",
        }

    # Execute: balance changes and a new transaction is recorded.
    acc["balance"] -= amount
    acc["transactions"].append({
        "date": today,
        "description": f"Transfer to {to_account}",
        "amount": -amount,
    })
    bank._daily_transferred[(from_account, today)] = projected_total

    return {
        "status": "executed",
        "from_account": from_account,
        "to_account": to_account,
        "amount": amount,
        "new_balance": acc["balance"],
    }


# ---------------------------------------------------------------------------
# Stage 3 — Live currency conversion (Frankfurter API, no key needed)
# ---------------------------------------------------------------------------

def convert_currency(amount, from_currency, to_currency):
    """
    Converts `amount` from from_currency to to_currency using the live
    Frankfurter API. Returns at most 3 fields. Never raises — an unknown
    currency code returns an error value instead.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    try:
        response = requests.get(
            "https://api.frankfurter.dev/v1/latest",
            params={"base": from_currency, "symbols": to_currency},
            timeout=10,
        )
        data = response.json()

        if "rates" not in data or to_currency not in data.get("rates", {}):
            return {"error": f"Could not find exchange rate for {from_currency} -> {to_currency}."}

        rate = data["rates"][to_currency]
        converted = round(amount * rate, 2)
        return {
            "converted_amount": converted,
            "rate": rate,
            "target_currency": to_currency,
        }
    except requests.RequestException as e:
        return {"error": f"Currency conversion service unavailable: {e}"}
    except (KeyError, ValueError, TypeError) as e:
        return {"error": f"Unexpected response from currency service: {e}"}


# ---------------------------------------------------------------------------
# Tool declarations (OpenAI / OpenRouter function-calling format)
# ---------------------------------------------------------------------------

TOOL_DECLARATIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_account",
            "description": (
                "Look up a customer's account details: balance, currency, and "
                "daily transfer limit. Use this whenever the customer asks "
                "about their balance or account info."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "The customer's account id, e.g. 'A-1'.",
                    }
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_transactions",
            "description": (
                "Look up a customer's recent transactions. Use this whenever "
                "the customer asks to see their transaction history or "
                "recent activity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "The customer's account id, e.g. 'A-1'.",
                    }
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_money",
            "description": (
                "Transfer money from one account to another. This tool "
                "enforces the account's daily transfer limit and available "
                "balance in code — it will refuse or escalate automatically "
                "if the request is over-limit; never attempt to bypass this "
                "or promise the customer an over-limit transfer will go through."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "from_account": {"type": "string", "description": "Source account id, e.g. 'A-1'."},
                    "to_account": {"type": "string", "description": "Destination account id, e.g. 'A-2'."},
                    "amount": {"type": "number", "description": "Amount to transfer."},
                },
                "required": ["from_account", "to_account", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": (
                "Convert an amount from one currency to another using live "
                "exchange rates. Use this whenever the customer asks for a "
                "balance or amount in a different currency, or asks about "
                "an exchange rate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "The amount to convert."},
                    "from_currency": {"type": "string", "description": "3-letter source currency code, e.g. 'USD'."},
                    "to_currency": {"type": "string", "description": "3-letter target currency code, e.g. 'EUR'."},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
]

# Maps tool name -> actual Python function, used by assistant.py's loop.
TOOL_FUNCTIONS = {
    "get_account": get_account,
    "get_recent_transactions": get_recent_transactions,
    "transfer_money": transfer_money,
    "convert_currency": convert_currency,
}


if __name__ == "__main__":
    print("get_account('A-1'):", get_account("A-1"))
    print("get_account('Z-9999'):", get_account("Z-9999"))
    print("get_recent_transactions('A-1'):", get_recent_transactions("A-1"))
    print("transfer_money('A-1','A-2',50):", transfer_money("A-1", "A-2", 50))
    print("transfer_money('A-1','A-2',5000):", transfer_money("A-1", "A-2", 5000))
    print("convert_currency(100,'USD','EUR'):", convert_currency(100, "USD", "EUR"))
    print("convert_currency(100,'USD','XYZ'):", convert_currency(100, "USD", "XYZ"))
