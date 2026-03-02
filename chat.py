from langgraph.graph import StateGraph, START, END

from graph.state import ExpenseState
from graph.nodes import (
    classifier,
    expense_manager,
    excel_writer_node,
)

# ---------------- GRAPH SETUP ----------------

graph_builder = StateGraph[ExpenseState, None, ExpenseState, ExpenseState](ExpenseState)

graph_builder.add_node("classifier", classifier)
graph_builder.add_node("expense_manager", expense_manager)
graph_builder.add_node("excel_writer", excel_writer_node)

graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "expense_manager")
graph_builder.add_edge("expense_manager", "excel_writer")
graph_builder.add_edge("excel_writer", END)

agent = graph_builder.compile()

# ---------------- CHAT LOOP ----------------

def run_chat():
    print("\n💬 Expense Assistant Started")
    print("Type 'exit' to quit\n")

    # persistent memory
    state: ExpenseState = {
        "userInput": "",
        "sessionExpenses": [],
    }

    while True:
        user_text = input("You: ")

        if user_text.lower() in ["exit", "quit"]:
            print("👋 Bye!")
            break

        # update state input
        state["userInput"] = user_text

        # invoke graph with previous state
        state = agent.invoke(state)

        # show session summary
        print("\n📊 Current Session Expenses:")
        for e in state.get("sessionExpenses", []):
            print(f"  - {e['category']} ({e.get('context','')}): ₹{e['amount']}")

        print("\n✅ Saved to Excel\n")


if __name__ == "__main__":
    run_chat()
