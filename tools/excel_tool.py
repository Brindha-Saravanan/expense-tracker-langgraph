import os
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_FILE = os.path.join(BASE_DIR, "data", "expense.xlsx")
COLUMNS = ["Date", "Travel", "Food", "Groceries", "Medical", "Misc", "Total", "Miscellaneous_Notes"]
CATEGORY_COLS = ["Travel", "Food", "Groceries", "Medical", "Misc"]


def _load_or_create_df() -> pd.DataFrame:
    os.makedirs(os.path.dirname(EXCEL_FILE), exist_ok=True)
    try:
        df = pd.read_excel(EXCEL_FILE)
        # Ensure all expected columns exist
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = "" if col in ("Date", "Miscellaneous_Notes") else 0
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)


def update_expense_excel(sessionExpenses: list[dict]) -> str:
    """
    Overwrite today's row with the full session state.
    FIX: Previously reset all categories to 0 but then accumulated from sessionExpenses,
         which was correct in isolation — however it was double-adding because prev_val
         was read after reset. Now logic is clean: reset → accumulate from session.
    """
    df = _load_or_create_df()
    today_str = datetime.today().strftime("%d-%m-%Y")

    if today_str in df["Date"].values:
        row_idx = df.index[df["Date"] == today_str][0]
    else:
        row_idx = len(df)
        new_row = {col: 0 for col in COLUMNS}
        new_row["Date"] = today_str
        new_row["Miscellaneous_Notes"] = ""
        df.loc[row_idx] = new_row

    for cat in CATEGORY_COLS:
        df.at[row_idx, cat] = 0
    df.at[row_idx, "Miscellaneous_Notes"] = ""

    misc_notes = []

    for expense in sessionExpenses:
        cat = expense.get("category", "Misc")
        amt = expense.get("amount", 0)
        ctx = expense.get("context", "")

        if cat not in CATEGORY_COLS:
            cat = "Misc"

        prev = df.at[row_idx, cat] or 0
        df.at[row_idx, cat] = prev + amt

        if cat == "Misc" and ctx:
            misc_notes.append(f"{ctx}:{amt}")

    df.at[row_idx, "Total"] = sum(df.at[row_idx, cat] or 0 for cat in CATEGORY_COLS)
    df.at[row_idx, "Miscellaneous_Notes"] = ", ".join(misc_notes)

    df.to_excel(EXCEL_FILE, index=False)
    return f"✅ Expenses saved to {EXCEL_FILE}"


def read_expense_excel() -> str:
    """Return the Excel contents as a readable string for the retrieval node."""
    df = _load_or_create_df()
    if df.empty:
        return "No expense data recorded yet."
    return df.to_string(index=False)