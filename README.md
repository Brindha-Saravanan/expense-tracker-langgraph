# 💰 Expense Tracker Agent — Built with LangGraph

> A conversational AI agent that tracks your daily expenses, stores them in Excel, and handles natural language inputs — including corrections, queries, and incomplete entries.

---

## 🧠 What is this?

This is a **stateful, graph-based AI agent** built using [LangGraph](https://github.com/langchain-ai/langgraph) and [Gradio](https://gradio.app/). It lets you log expenses through natural conversation — no forms, no manual entry. Just talk to it.

```
You:   I had 2 dosas this morning
Bot:   How much did you spend on dosa? 💬
You:   Around 40
Bot:   Got it! Added ₹40 under Food (dosa). Your total so far is ₹40.
```

---

## ✨ Features

- 🗣️ **Natural language input** — say it how you think it
- 🔄 **Clarification loop** — asks for missing amounts instead of guessing
- ✏️ **Corrections** — update, reduce, delete, or replace any expense
- 🔍 **Retrieval** — ask "what did I spend on food?" or "show today's total"
- 💬 **Casual chat** — greet it, thank it, it responds like a real assistant
- 📊 **Excel output** — all expenses saved to a structured `.xlsx` file with date, category, total, and notes

---

## 🏗️ Architecture

The agent is built as a **LangGraph state machine** with 4 conditional paths:

```
START → classifier ──┬──["mutate"]──→ expense_manager → excel_writer → chat_responder → END
                     ├──["retrieve"]─→ retrieval ──────────────────────────────────────→ END
                     ├──["chat"]─────→ casual ─────────────────────────────────────────→ END
                     └──["clarify"]──→ clarify (ask for amount) ────────────────────────→ END
```

| Intent | Triggered when | Path |
|---|---|---|
| `mutate` | Expense with known amount | Update session + write Excel |
| `retrieve` | "How much did I spend?" | Read session + Excel, answer |
| `chat` | Greetings, small talk | Friendly response |
| `clarify` | Expense mentioned, no amount | Ask user, hold in pending state |

---

## 📁 Project Structure

```
expense_tracker/
├── app.py                  # Gradio chat interface
├── graph/
│   ├── build_graph.py      # LangGraph state machine
│   ├── state.py            # ExpenseState TypedDict
│   └── nodes.py            # All agent nodes
├── tools/
│   └── excel_tool.py       # Excel read/write logic
└── data/
    └── expense.xlsx        # Auto-created on first run
```

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/expense-tracker-langgraph.git
cd expense-tracker-langgraph
```

### 2. Create and activate a virtual environment (recommended)
```bash
# Mac / Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your OpenAI API key

Create a `.env` file in the root folder:
```
OPENAI_API_KEY=your_key_here
```

Or export it directly in your terminal:
```bash
# Mac / Linux
export OPENAI_API_KEY=your_key_here

# Windows
set OPENAI_API_KEY=your_key_here
```

### 5. Run
```bash
python app.py
```

Then open `http://localhost:7860` in your browser.

---

## 🗂️ Excel Output Format

| Date | Travel | Food | Groceries | Medical | Misc | Total | Miscellaneous_Notes |
|---|---|---|---|---|---|---|---|
| 02-03-2026 | 150 | 80 | 0 | 0 | 40 | 270 | chai:20, vada:20 |

---

## 💡 Example Conversations

```
# Adding expenses
"I spent 200 on an Uber and had lunch for 180"

# Partial input (triggers clarification)
"I took an auto to office"
→ "How much did you spend on auto? 💬"
"It was 55"

# Correction
"Actually the Uber was 220, not 200"

# Query
"What's my total for today?"
"How much did I spend on food?"

# Delete
"Remove the auto expense"
```

---

## 🔧 Tech Stack

| Tool | Purpose |
|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful agent graph |
| [LangChain + OpenAI](https://python.langchain.com/) | LLM calls (GPT-4o-mini) |
| [Gradio](https://gradio.app/) | Chat UI |
| [Pandas + openpyxl](https://pandas.pydata.org/) | Excel read/write |

---

## 🤝 Contributing

Feel free to open issues or PRs! Ideas welcome:
- Multi-day summary reports
- Category budget limits and alerts
- Voice input support
- Export to Google Sheets

---

## 📄 License

MIT
