from langgraph.graph import StateGraph, START, END

from graph.state import ExpenseState
from graph.nodes import (
    classifier,
    expense_manager,
    excel_writer_node,
    chat_responder,
    retrieval_node,
    casual_responder,
    clarification_node,
    route_intent,
)


def build_agent():
    builder = StateGraph(ExpenseState)

    builder.add_node("classifier", classifier)
    builder.add_node("expense_manager", expense_manager)
    builder.add_node("excel_writer", excel_writer_node)
    builder.add_node("chat_responder", chat_responder)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("casual", casual_responder)
    builder.add_node("clarify", clarification_node)   # NEW: ask for missing amount

    builder.add_edge(START, "classifier")

    builder.add_conditional_edges(
        "classifier",
        route_intent,
        {
            "mutate":   "expense_manager",
            "retrieve": "retrieval",
            "chat":     "casual",
            "clarify":  "clarify",            # missing amount → ask user
        },
    )

    # Mutate path
    builder.add_edge("expense_manager", "excel_writer")
    builder.add_edge("excel_writer", "chat_responder")
    builder.add_edge("chat_responder", END)

    # Other paths
    builder.add_edge("retrieval", END)
    builder.add_edge("casual", END)
    builder.add_edge("clarify", END)          # waits for user's next message

    return builder.compile()