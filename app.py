import gradio as gr
from graph.build_graph import build_agent
from IPython.display import Image
agent = build_agent()

state_memory = {
    "userInput": "",
    "intent_type": "chat",
    "response": [],
    "sessionExpenses": [],
    "pendingExpenses": [],   # holds items waiting for amount clarification
    "systemOutput": "",
}


def chat(message: str, history: list) -> str:
    global state_memory

    state_memory["userInput"] = message

    result = agent.invoke(state_memory)
    state_memory.update(result)

    return state_memory.get("systemOutput", "Done.")


demo = gr.ChatInterface(
    fn=chat,
    title="💰 Expense Tracker Agent",
    description=(
        "Track expenses naturally. Examples:\n"
        "• 'I spent 200 on food and 150 on auto'\n"
        "• 'Update food to 180'\n"
        "• 'How much did I spend today?'\n"
        "• 'Delete the auto expense'"
    ),
)
Image(agent.get_graph().draw_mermaid_png())

if __name__ == "__main__":
    demo.launch()