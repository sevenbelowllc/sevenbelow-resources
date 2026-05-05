"""
Assignment 1: The Context Overflow Tool — SOLUTION

What this fixes:
1. The lookup tool no longer dumps the full orders table into the LLM context.
2. The tool returns only records relevant to the query (order_id or email).
3. Returned records are trimmed to a small whitelist of necessary fields.
4. Protective middleware caps row count and serialized output size so oversized
   tool payloads cannot reach the LLM again.
5. The session layer answers simple follow-up questions directly from cached
   order context, avoiding unnecessary tool calls and token usage.
"""

import json
import os
import random
import re
import string
import uuid
from datetime import datetime, timedelta

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Simulated database — DO NOT MODIFY this section
# ---------------------------------------------------------------------------

def _generate_fake_orders(n=10000):
    """Generate a large fake orders table."""
    statuses = ["shipped", "delivered", "processing", "returned", "cancelled"]
    products = [
        "Wireless Mouse", "USB-C Hub", "Mechanical Keyboard", "Monitor Stand",
        "Webcam HD", "Desk Lamp", "Laptop Sleeve", "Cable Organizer",
        "Noise-Cancelling Headphones", "Portable Charger", "Ergonomic Chair",
        "Standing Desk Mat", "Blue Light Glasses", "Wireless Charger",
        "Smart Power Strip", "Document Scanner", "Label Printer",
    ]
    customers = [f"customer_{i:04d}" for i in range(500)]
    orders = []
    for i in range(n):
        order_date = datetime.now() - timedelta(days=random.randint(1, 365))
        items = random.sample(products, k=random.randint(1, 5))
        orders.append({
            "order_id": f"ORD-{i+1:06d}",
            "customer_id": random.choice(customers),
            "customer_email": f"user{random.randint(1,9999)}@example.com",
            "status": random.choice(statuses),
            "order_date": order_date.isoformat(),
            "delivery_date": (order_date + timedelta(days=random.randint(2, 14))).isoformat(),
            "items": items,
            "quantities": [random.randint(1, 3) for _ in items],
            "prices": [round(random.uniform(9.99, 299.99), 2) for _ in items],
            "shipping_address": {
                "street": f"{random.randint(1,9999)} {random.choice(['Main', 'Oak', 'Elm', 'Pine', 'Cedar'])} St",
                "city": random.choice(["Portland", "Austin", "Denver", "Seattle", "Chicago"]),
                "state": random.choice(["OR", "TX", "CO", "WA", "IL"]),
                "zip": f"{random.randint(10000, 99999)}",
            },
            "payment_method": random.choice(["credit_card", "debit_card", "paypal"]),
            "card_last_four": ''.join(random.choices(string.digits, k=4)),
            "internal_notes": f"Batch processed. Agent: auto-{random.randint(1,50)}. "
                              f"Priority: {''.join(random.choices(string.ascii_lowercase, k=200))}",
            "warehouse_log": f"Picked from aisle {random.randint(1,99)}, "
                             f"shelf {random.choice(string.ascii_uppercase)}{random.randint(1,20)}. "
                             f"Weight: {round(random.uniform(0.5, 25.0), 2)}kg. "
                             f"Dimensions: {random.randint(10,80)}x{random.randint(10,80)}x{random.randint(10,80)}cm. "
                             f"Tracking events: {'|'.join([f'event_{j}' for j in range(random.randint(5,20))])}",
        })
    return orders


ORDERS_DB = _generate_fake_orders(2000)

# Seed a known order so we can test with it
ORDERS_DB[0] = {
    "order_id": "ORD-000001",  # Need this
    "customer_id": "customer_0042",
    "customer_email": "alice@example.com",  # Need this
    "status": "shipped",  # Need this
    "order_date": "2026-03-15T10:30:00",
    "delivery_date": "2026-03-22T14:00:00",  # Need this
    "items": ["Mechanical Keyboard", "USB-C Hub"],  # Need this
    "quantities": [1, 2],
    "prices": [149.99, 34.99],
    "shipping_address": {
        "street": "742 Evergreen Terrace",
        "city": "Portland",
        "state": "OR",
        "zip": "97201",
    },
    "payment_method": "credit_card",
    "card_last_four": "4242",
    "internal_notes": "VIP customer, handle with care. Escalation history: ...",
    "warehouse_log": "Picked from aisle 12, shelf B7. Weight: 2.3kg. ...",
}

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_ORDER_ID_PATTERN = re.compile(r"ORD-\d{6}", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]+")

def extract_order_id(query: str) -> str | None:
    match = _ORDER_ID_PATTERN.search(query)
    return match.group(0).upper() if match else None

def extract_email(query: str) -> str | None:
    match = _EMAIL_PATTERN.search(query)
    return match.group(0).lower() if match else None

def infer_requested_field(query: str) -> str | None:
    q = query.lower()
    if "status" in q:
        return "status"
    if "deliver" in q or "delivery date" in q or "when will" in q:
        return "delivery_date"
    if "item" in q:
        return "items"
    return None

def format_order_bundle(order: dict) -> str:
    items = ", ".join(order["items"]) if isinstance(order.get("items"), list) else str(order.get("items", ""))
    return f"{order['order_id']} | {order['status']} | {order['delivery_date']} | {items}"

def normalize_field_value(field: str, value):
    if value is None:
        return None
    if field == "items" and isinstance(value, list):
        return ", ".join(value)
    return str(value)

# ---------------------------------------------------------------------------
# Safe lookup implementation
# ---------------------------------------------------------------------------

_FIELDS_TO_KEEP = ["order_id", "customer_email", "status", "delivery_date", "items"]
MAX_TOOL_ROWS = 5
MAX_TOOL_OUTPUT_CHARS = 2000

def _trim(record: dict) -> dict:
    """Whitelist only the fields needed by support queries."""
    return {field: record.get(field) for field in _FIELDS_TO_KEEP}

def lookup_order_by_id(order_id: str) -> dict | None:
    """Direct lookup by order_id. Returns a single raw DB record or None."""
    for record in ORDERS_DB:
        if record["order_id"] == order_id:
            return record
    return None

def lookup_order_by_email(email: str) -> list[dict]:
    """Lookup all raw DB records matching an email."""
    email = email.lower()
    return [record for record in ORDERS_DB if record.get("customer_email", "").lower() == email]

def safe_lookup(order_id: str = "", email: str = "") -> dict:
    """
    Protective middleware for lookup results.

    Guarantees:
    - never returns the full database
    - trims fields
    - caps row count
    - caps serialized output size
    """
    if not order_id and not email:
        return {"ok": False, "error": "Provide an order_id or email."}

    if order_id:
        record = lookup_order_by_id(order_id.upper())
        if not record:
            return {"ok": True, "data": []}
        trimmed = [_trim(record)]
    else:
        matches = lookup_order_by_email(email)
        trimmed = [_trim(r) for r in matches]

    has_more = len(trimmed) > MAX_TOOL_ROWS
    paginated = trimmed[:MAX_TOOL_ROWS]

    serialized = json.dumps(paginated)
    if len(serialized) > MAX_TOOL_OUTPUT_CHARS:
        return {
            "ok": False,
            "error": (
                f"Serialized tool output exceeded safe limit of "
                f"{MAX_TOOL_OUTPUT_CHARS} chars."
            ),
        }

    return {
        "ok": True,
        "data": paginated,
        "has_more": has_more,
        "total_matches": len(trimmed),
        "all_data": trimmed,  # full result set for session caching
    }

@tool
def lookup_order_info(order_id: str = "", email: str = "") -> str:
    """
    Look up order information safely by order ID or customer email.

    Returns only relevant, trimmed information. If more results exist
    beyond the page limit, the response includes a has_more flag.
    """
    result = safe_lookup(order_id=order_id, email=email)
    if not result["ok"]:
        return result["error"]
    output = {"orders": result["data"]}
    if result.get("has_more"):
        output["has_more"] = True
        output["showing"] = len(result["data"])
        output["total"] = result["total_matches"]
        output["note"] = "More results available. Narrow by order_id for specific records."
    return json.dumps(output)

# ---------------------------------------------------------------------------
# Session-aware wrapper
# ---------------------------------------------------------------------------

class SessionAwareAgent:
    """
    Uses cached order context to answer obvious follow-ups without invoking
    the LLM or the tool again.
    """

    _REFINEMENT_WORDS = {"more", "additional", "other", "rest", "remaining", "next"}

    def __init__(self, agent_executor):
        self.agent_executor = agent_executor
        self.chat_history = []
        self.session = {
            "active_order_id": None,
            "active_order_data": None,  # trimmed single order only
            "active_email_orders": [],  # all orders for the last email lookup
            "answered_fields": {},      # e.g. ORD-000001:status -> shipped
        }

    def _write_turn(self, user_text: str, assistant_text: str) -> dict:
        self.chat_history.append(HumanMessage(content=user_text))
        self.chat_history.append(AIMessage(content=assistant_text))
        return {"output": assistant_text}

    def _set_active_order(self, trimmed_order: dict | None) -> None:
        if trimmed_order:
            self.session["active_order_id"] = trimmed_order["order_id"]
            self.session["active_order_data"] = trimmed_order
        else:
            self.session["active_order_id"] = None
            self.session["active_order_data"] = None

    def invoke(self, payload):
        query = payload["input"]

        requested_order_id = extract_order_id(query)
        requested_email = extract_email(query)
        requested_field = infer_requested_field(query)

        # Refresh active context from explicit order id
        if requested_order_id:
            record = lookup_order_by_id(requested_order_id)
            self._set_active_order(_trim(record) if record else None)

        # Refresh active context from email — cache ALL results
        elif requested_email:
            result = safe_lookup(email=requested_email)
            if result["ok"]:
                self.session["active_email_orders"] = result.get("all_data", result["data"])
                if len(result["data"]) == 1:
                    self._set_active_order(result["data"][0])

        active_order_id = self.session["active_order_id"]
        active_order_data = self.session["active_order_data"]

        # If the exact field was already answered for this active order, do not repeat work
        if active_order_id and requested_field:
            answered_key = f"{active_order_id}:{requested_field}"
            if answered_key in self.session["answered_fields"]:
                return self._write_turn(
                    query,
                    f"As previously provided, {self.session['answered_fields'][answered_key]}."
                )

        # Answer directly from cached context whenever possible
        if active_order_id and active_order_data and requested_field:
            raw_value = active_order_data.get(requested_field)
            normalized = normalize_field_value(requested_field, raw_value)

            if normalized is not None:
                answered_prefix = f"{active_order_id}:"

                # First field request for this order: proactively bundle all likely follow-up details.
                if not any(key.startswith(answered_prefix) for key in self.session["answered_fields"]):
                    bundle = format_order_bundle(active_order_data)

                    self.session["answered_fields"][f"{active_order_id}:status"] = active_order_data["status"]
                    self.session["answered_fields"][f"{active_order_id}:delivery_date"] = active_order_data["delivery_date"]
                    self.session["answered_fields"][f"{active_order_id}:items"] = ", ".join(active_order_data["items"])

                    return self._write_turn(query, bundle)

                self.session["answered_fields"][f"{active_order_id}:{requested_field}"] = normalized
                return self._write_turn(query, normalized)

        # Refinement queries ("more", "additional", "other") → answer from cached email results
        query_words = set(query.lower().split())
        if query_words & self._REFINEMENT_WORDS and self.session["active_email_orders"]:
            all_orders = self.session["active_email_orders"]
            # Show orders not yet surfaced as the active order
            unseen = [o for o in all_orders if o["order_id"] != active_order_id]
            if unseen:
                lines = [format_order_bundle(o) for o in unseen[:MAX_TOOL_ROWS]]
                remaining = len(unseen) - len(lines)
                text = "\n".join(lines)
                if remaining > 0:
                    text += f"\n({remaining} more — narrow by order_id)"
                return self._write_turn(query, text)
            return self._write_turn(query, "No additional orders found for this customer.")

        # Pass cached trimmed order context to the LLM only when needed
        cached_data_str = json.dumps(active_order_data) if active_order_data else "none"

        result = self.agent_executor.invoke(
            {
                "input": query,
                "order_data": cached_data_str,
                "chat_history": self.chat_history,
            }
        )

        #self.chat_history.append(HumanMessage(content=query))
        #self.chat_history.append(AIMessage(content=result["output"]))

        # keep only last 2 turns to limit token growth
        self.chat_history = (self.chat_history + [
            HumanMessage(content=query),
            AIMessage(content=result["output"])
        ])[-4:]

        
        return result

# ---------------------------------------------------------------------------
# Agent setup
# ---------------------------------------------------------------------------

def create_agent():
    session_id = str(uuid.uuid4())

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://www.dataexpert.io/api/v1/openai",
        streaming=True,
        default_headers={"X-Session-ID": session_id},
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a terse customer support agent.\n\n"
            "CACHED ORDER CONTEXT: {order_data}\n\n"
            "BEHAVIOR:\n"
            "- Always check Cached Order Context first. Use it when it answers the query.\n"
            "- Only call lookup_order_info when the cache is 'none' or missing the requested data.\n"
            "- When returning order details, always include the items list from cache unless the user explicitly asks for a single field only.\n"
            "\n"
            "OUTPUT FORMAT (plain text only):\n"
            "- Single order: <order_id> | <status> | <delivery_date> | <items>\n"
            "- Email lookup: same format per order, one line each\n"
            "- Single field requested: return just the value\n"
            "- Already answered: As previously provided, <value>.\n"
            "- Not found: Not found.\n"
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, [lookup_order_info], prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=[lookup_order_info],
        verbose=True,
    )
    return SessionAwareAgent(executor)

# ---------------------------------------------------------------------------
# Test queries — DO NOT MODIFY
# ---------------------------------------------------------------------------

TEST_QUERIES = [
    "What's the status of order ORD-000001?",
    "When will order ORD-000001 be delivered?",
    "What items are in order ORD-000001?",
    "Can you look up the order for customer alice@example.com?",
]

def main():
    agent = create_agent()

    for query in TEST_QUERIES:
        print(f"\n{'=' * 60}")
        print(f"QUERY: {query}")
        print(f"{'=' * 60}")
        try:
            result = agent.invoke({"input": query})
            print(f"\nRESPONSE: {result['output']}")
        except Exception as e:
            print(f"\nERROR: {e}")
        print()

if __name__ == "__main__":
    main()