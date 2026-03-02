from graph.state import ExpenseState
from langchain_openai import ChatOpenAI
from tools.excel_tool import update_expense_excel, read_expense_excel
import json

categories = ['Travel', 'Food', 'Groceries', 'Medical', 'Misc']
llm = ChatOpenAI(model="gpt-4o-mini")

# ─── Classifier ────────────────────────────────────────────────────────────────

CLASSIFIER_SYSTEM = """You are an expense tracking agent. The user's session expenses so far are:
{sessionExpenses}

There may also be PENDING expenses waiting for clarification (missing amounts):
{pendingExpenses}

Your tasks:
1. Decide which intent applies:
   - "chat"     → greeting, small talk, thanks, or anything NOT about expenses
   - "retrieve" → user wants to QUERY or VIEW expense info
   - "mutate"   → user is adding/updating/deleting expenses AND all amounts are known
   - "clarify"  → user mentions an expense item but NO amount is given (e.g. "I had 2 dosas", "I took an auto")

2. IMPORTANT: If there are pendingExpenses and the user's message looks like they are providing
   the missing amount (e.g. "it was 40", "50 rupees", "around 30"), set intent_type to "mutate"
   and fill in the pending item's category/context with the provided amount.

3. For mutate intents, classify each expense into: Travel, Food, Groceries, Medical, Misc.
4. Include a 1-word 'context' field for specifics (e.g. 'dosa' for dosa, 'auto' for auto-rickshaw).
5. Set 'intend' per item: "add", "update", "reduce", "delete", or "alter".
6. For clarify intents, still extract category and context but set amount to null.

Return ONLY valid JSON — no explanation, no markdown:
{{
  "intent_type": "chat" | "retrieve" | "mutate" | "clarify",
  "expenses": [
    {{"category": "<cat>", "amount": <number or null>, "intend": "<intend>", "context": "<ctx>"}}
  ]
}}

For "chat" and "retrieve" intents, expenses list should be [].
"""


def classifier(state: ExpenseState) -> ExpenseState:
    session = state.get("sessionExpenses", [])
    pending = state.get("pendingExpenses", [])

    messages = [
        {"role": "system", "content": CLASSIFIER_SYSTEM.format(
            sessionExpenses=session,
            pendingExpenses=pending
        )},
        {"role": "user", "content": state["userInput"]},
    ]

    response = llm.invoke(messages)
    print("Classifier raw:", response.content)

    parsed = json.loads(response.content)

    return {
        "intent_type": parsed.get("intent_type", "mutate"),
        "response": parsed.get("expenses", []),
    }


# ─── Route decision ────────────────────────────────────────────────────────────

def route_intent(state: ExpenseState) -> str:
    return state.get("intent_type", "mutate")


# ─── Clarification Node ───────────────────────────────────────────────────────

def clarification_node(state: ExpenseState) -> ExpenseState:
    """
    Store incomplete expenses as pending and ask user for the missing amount.
    """
    incomplete = state.get("response", [])

    # Merge with any already-pending expenses
    existing_pending = state.get("pendingExpenses", [])
    for item in incomplete:
        # Avoid duplicates
        already = any(
            p["category"] == item["category"] and p.get("context") == item.get("context")
            for p in existing_pending
        )
        if not already:
            existing_pending.append({
                "category": item["category"],
                "context": item.get("context", ""),
                "intend": item.get("intend", "add"),
            })

    # Build a natural question
    if len(existing_pending) == 1:
        p = existing_pending[0]
        label = p.get("context") or p["category"]
        question = f"How much did you spend on {label}? 💬"
    else:
        labels = [p.get("context") or p["category"] for p in existing_pending]
        question = f"How much did you spend on {', '.join(labels)}? 💬"

    return {
        "pendingExpenses": existing_pending,
        "systemOutput": question,
    }


# ─── Expense Manager (mutate path) ────────────────────────────────────────────

def expense_manager(state: ExpenseState) -> ExpenseState:
    session = list(state.get("sessionExpenses", []))
    pending = list(state.get("pendingExpenses", []))
    actions = state.get("response", [])

    # If there were pending expenses and user just gave an amount,
    # the classifier would have filled in the pending item — merge pending into actions
    if pending and actions:
        for act in actions:
            # If amount is present but category/context matches a pending item, clear that pending
            pending = [
                p for p in pending
                if not (p["category"] == act.get("category") and p.get("context") == act.get("context"))
            ]

    for act in actions:
        cat = act.get("category", "Misc")
        amt = act.get("amount", 0)
        ctx = act.get("context", "")
        intent = act.get("intend", "add")

        # Skip if amount is still missing
        if amt is None:
            continue

        if intent == "add":
            found = False
            for e in session:
                if e["category"] == cat and e.get("context") == ctx:
                    e["amount"] += amt
                    found = True
                    break
            if not found:
                session.append({"category": cat, "amount": amt, "context": ctx})

        elif intent == "update":
            matched = False
            for e in reversed(session):
                if e["category"] == cat and e.get("context") == ctx:
                    e["amount"] = amt
                    matched = True
                    break
            if not matched:
                session.append({"category": cat, "amount": amt, "context": ctx})

        elif intent == "reduce":
            for e in reversed(session):
                if e["category"] == cat and e.get("context") == ctx:
                    e["amount"] = max(0, e["amount"] - amt)
                    break
            else:
                session.append({"category": cat, "amount": amt, "context": ctx})

        elif intent == "delete":
            session = [e for e in session if not (e["category"] == cat and e.get("context") == ctx)]

        elif intent == "alter":
            session = [e for e in session if not (e["category"] == cat and e.get("context") == ctx)]
            session.append({"category": cat, "amount": amt, "context": ctx})

    print("Session after manager:", session)
    return {
        "sessionExpenses": session,
        "pendingExpenses": pending,  # clear resolved pending items
    }


# ─── Excel Writer ─────────────────────────────────────────────────────────────

def excel_writer_node(state: ExpenseState) -> ExpenseState:
    session = state.get("sessionExpenses", [])
    msg = update_expense_excel(session)
    print(msg)
    return state


# ─── Retrieval Node ───────────────────────────────────────────────────────────

def retrieval_node(state: ExpenseState) -> ExpenseState:
    excel_data = read_expense_excel()
    session = state.get("sessionExpenses", [])

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful expense assistant. Answer the user's question about their expenses.\n"
                f"Current session expenses: {session}\n"
                f"Historical Excel data:\n{excel_data}"
            ),
        },
        {"role": "user", "content": state.get("userInput", "")},
    ]

    response = llm.invoke(messages)
    return {"systemOutput": response.content}


# ─── Casual Chat Responder ────────────────────────────────────────────────────

CASUAL_SYSTEM = """You are a friendly expense tracking chatbot assistant.
If the user greets you or makes small talk, respond warmly and briefly introduce what you can do:
- Track expenses by category (Travel, Food, Groceries, Medical, Misc)
- Update or correct past entries
- Show spending summaries

Keep it short, friendly, and natural.
"""


def casual_responder(state: ExpenseState) -> ExpenseState:
    messages = [
        {"role": "system", "content": CASUAL_SYSTEM},
        {"role": "user", "content": state.get("userInput", "")},
    ]
    response = llm.invoke(messages)
    return {"systemOutput": response.content}


# ─── Chat Responder (mutate path) ─────────────────────────────────────────────

RESPONDER_SYSTEM = """You are a friendly expense tracking assistant.
Summarize what was added/updated/deleted. Show current totals clearly. Be short and conversational.

Current session expenses:
{session}
"""


def chat_responder(state: ExpenseState) -> ExpenseState:
    session = state.get("sessionExpenses", [])
    user_input = state.get("userInput", "")

    messages = [
        {"role": "system", "content": RESPONDER_SYSTEM.format(session=session)},
        {"role": "user", "content": user_input},
    ]

    response = llm.invoke(messages)
    return {"systemOutput": response.content}