from typing import TypedDict, List

class ExpenseState(TypedDict):
    userInput: str
    intent_type: str          # "mutate" | "retrieve" | "chat" | "clarify"
    response: list            # classifier output (list of dicts)
    sessionExpenses: List[dict]   # confirmed expenses
    pendingExpenses: List[dict]   # incomplete expenses waiting for amount clarification
    systemOutput: str