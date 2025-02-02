import streamlit as st
import pandas as pd
import gspread
import datetime
import json
from oauth2client.service_account import ServiceAccountCredentials

# 🔥 Set Page Config
st.set_page_config(page_title="Personal Finance Tracker", layout="wide")

# 🔥 Full Path of credentials.json
CREDENTIALS_PATH = "D:/Projects/Expense Tracker/credentials.json"
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# 🔥 Google Sheets API Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # 📊 Google Sheets Connection
    SHEET_NAME = "Expense Tracker"
    sheet = client.open(SHEET_NAME).sheet1

    # Initialize headers if Google Sheet is blank
    if not sheet.get_all_records():
        headers = ["Date", "Type of Transact", "Category", "Amount", "Account", "Notes"]
        sheet.append_row(headers)

except Exception as e:
    st.error("❌ Google Sheets access failed. Check credentials or permissions!")
    st.stop()

# 🔹 File to Store Accounts and Categories
ACCOUNTS_FILE = "accounts.csv"
CATEGORY_FILE = "categories.csv"

# 🔹 Default Categories
default_expense_categories = ["Food", "Shopping", "Bills", "Transport", "Other"]
default_income_categories = ["Salary", "Freelancing", "Investments", "Other"]

# 🔹 Load or Initialize Accounts
def load_accounts():
    try:
        accounts_df = pd.read_csv(ACCOUNTS_FILE)
    except FileNotFoundError:
        # Initialize CSV file if it doesn't exist
        data = {"Account Name": [], "Opening Balance": [], "Current Balance": []}
        accounts_df = pd.DataFrame(data)
        accounts_df.to_csv(ACCOUNTS_FILE, index=False)
    return accounts_df

def save_accounts(accounts_df):
    accounts_df.to_csv(ACCOUNTS_FILE, index=False)

accounts_df = load_accounts()

# 🔹 Load Custom Categories
def load_categories():
    try:
        categories_df = pd.read_csv(CATEGORY_FILE)
    except FileNotFoundError:
        # Initialize CSV file if it doesn't exist
        data = {"Category Type": ["Expense", "Income"], "Category Name": ["Other", "Other"]}
        categories_df = pd.DataFrame(data)
        categories_df.to_csv(CATEGORY_FILE, index=False)
    return categories_df

def save_categories(categories_df):
    categories_df.to_csv(CATEGORY_FILE, index=False)

categories_df = load_categories()

# 📌 Streamlit App UI
st.title("💰 Personal Finance Tracker")

# 📌 Sidebar for Navigation (Collapsible on Mobile)
with st.sidebar:
    is_mobile = st.session_state.get("is_mobile", False)
    if is_mobile:
        st.header("📌 Navigation", anchor="top")
        st.markdown("Swipe right to open the menu →", unsafe_allow_html=True)
    tabs = st.radio("Select Section:", ["Add Transaction", "Manage Accounts", "Manage Categories", "Dashboard"])


if tabs == "Add Transaction":
    # 🌟 Transaction Entry Section
    st.sidebar.header("➕ Add Transaction")

    # 🟢 Transaction Type Selection
    transaction_type = st.sidebar.radio("Transaction Type:", ["Expense", "Income"])

    # 🔹 Filter Categories Based on Transaction Type
    filtered_categories = categories_df[categories_df["Category Type"] == transaction_type]["Category Name"].tolist()
    if transaction_type == "Expense":
        filtered_categories = default_expense_categories + filtered_categories
    else:
        filtered_categories = default_income_categories + filtered_categories

    # 🔹 Input Fields for Transaction
    date = st.sidebar.date_input("Date")
    category = st.sidebar.selectbox("Category", filtered_categories)
    amount = st.sidebar.number_input("Amount (₹)", min_value=0.0, format="%.2f")
    account = st.sidebar.selectbox("Select Account", accounts_df["Account Name"] if not accounts_df.empty else ["No Accounts"])
    note = st.sidebar.text_area("Notes (Optional)")

    # 🔹 Save Transaction
    if st.sidebar.button("Save Transaction"):
        if not accounts_df.empty:
            new_transaction = [str(date), transaction_type, category, amount, account, note]
            try:
                # Save transaction to Google Sheets
                sheet.append_row(new_transaction)

                # Update Account Balance in real-time
                if transaction_type == "Expense":
                    accounts_df.loc[accounts_df["Account Name"] == account, "Current Balance"] -= amount
                else:
                    accounts_df.loc[accounts_df["Account Name"] == account, "Current Balance"] += amount
                
                save_accounts(accounts_df)  # Save updated balance to CSV

                # Display updated balance immediately
                st.sidebar.success("✅ Transaction Added Successfully!")
                st.experimental_rerun()  # Refresh the app for real-time update
            except Exception as e:
                st.sidebar.error("❌ Failed to save transaction. Check Google Sheets API access!")
        else:
            st.sidebar.error("❌ Please add an account first!")

elif tabs == "Manage Accounts":
    # 🌟 Manage Accounts Section
    st.sidebar.header("🏦 Manage Accounts")
    new_account_name = st.sidebar.text_input("New Account Name")
    opening_balance = st.sidebar.number_input("Opening Balance (₹)", min_value=0.0, format="%.2f")
    if st.sidebar.button("Add Account"):
        if new_account_name:
            # Add new account
            new_account = {"Account Name": new_account_name, "Opening Balance": opening_balance, "Current Balance": opening_balance}
            new_account_df = pd.DataFrame([new_account])
            accounts_df = pd.concat([accounts_df, new_account_df], ignore_index=True)
            save_accounts(accounts_df)
            st.sidebar.success("✅ New Account Added!")
        else:
            st.sidebar.error("❌ Please enter a valid account name!")

    st.header("🏦 Account Balances")
    if not accounts_df.empty:
        st.table(accounts_df)
    else:
        st.info("No accounts found. Add your first account!")

elif tabs == "Manage Categories":
    # 🌟 Manage Categories Section
    st.sidebar.header("⚙ Manage Categories")
    
    # Input for new category
    new_category_type = st.sidebar.radio("Category Type:", ["Expense", "Income"], key="category_type")
    new_category_name = st.sidebar.text_input("New Category Name")

    if st.sidebar.button("Add Category"):
        if new_category_name:
            # Add new category to the DataFrame
            new_row = {"Category Type": new_category_type, "Category Name": new_category_name}
            new_row_df = pd.DataFrame([new_row])  
            categories_df = pd.concat([categories_df, new_row_df], ignore_index=True)  
            save_categories(categories_df)  
            st.sidebar.success("✅ New Category Added!")
        else:
            st.sidebar.error("❌ Please enter a valid category name!")

    # 📋 Display all categories
    st.header("📋 All Categories")
    if not categories_df.empty:
        st.table(categories_df)
    else:
        st.info("No categories found. Add some categories to get started!")


elif tabs == "Dashboard":
    # 📊 Dashboard Section
    st.header("📊 Dashboard")

    try:
        # Fetch data from Google Sheets
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty and "Type of Transact" in df.columns and "Amount" in df.columns:
            # Convert 'Date' and 'Amount' to proper formats
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

            # 🔹 Date Filter
            st.sidebar.header("📅 Filter by Date")
            start_date = st.sidebar.date_input("Start Date", df["Date"].min())
            end_date = st.sidebar.date_input("End Date", df["Date"].max())

            # Filter transactions by date range
            filtered_df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

            import matplotlib.pyplot as plt
            import seaborn as sns
            import io

            # 🔹 Detect if user is on mobile
            is_mobile = st.session_state.get("is_mobile", False)
            graph_size = (8, 4) if is_mobile else (10, 6)

            # 🔹 Daily Trends: Income vs Expense
            st.subheader("📅 Daily Trends: Income vs Expense")
            daily_summary = filtered_df.groupby(["Date", "Type of Transact"])["Amount"].sum().unstack().fillna(0)

            if not daily_summary.empty:
                fig, ax = plt.subplots(figsize=graph_size)
                daily_summary.plot(kind="line", marker="o", ax=ax)

                for line in ax.lines:
                    for x, y in zip(line.get_xdata(), line.get_ydata()):
                        ax.annotate(f"{y:.0f}", (x, y), textcoords="offset points", xytext=(0,5), ha='center')

                ax.set_title("Daily Trends: Income vs Expense")
                ax.set_ylabel("Amount (₹)")
                ax.set_xlabel("Date")
                st.pyplot(fig)

            # 🔹 Monthly Trends: Income vs Expense
            st.subheader("📈 Monthly Trends: Income vs Expense")
            filtered_df["Month"] = filtered_df["Date"].dt.strftime("%b %Y") # Format as 'Jan 2025'
            monthly_summary = filtered_df.groupby(["Month", "Type of Transact"])["Amount"].sum().unstack().fillna(0)

            if not monthly_summary.empty:
                fig, ax = plt.subplots(figsize=graph_size)
                monthly_summary.plot(kind="bar", ax=ax)

                for container in ax.containers:
                    ax.bar_label(container, fmt="₹%.0f", padding=3)

                ax.set_title("Monthly Trends: Income vs Expense")
                ax.set_ylabel("Amount (₹)")
                ax.set_xlabel("Month")
                st.pyplot(fig)

            # 🔹 Category-Wise Spending Heatmap
            st.subheader("🌡️ Category-Wise Spending Heatmap")
            heatmap_data = filtered_df[filtered_df["Type of Transact"] == "Expense"].pivot_table(
                index="Category",
                columns=filtered_df["Date"].dt.strftime('%b %Y'),
                values="Amount",
                aggfunc="sum"
            ).fillna(0)

            if not heatmap_data.empty:
                fig, ax = plt.subplots(figsize=graph_size)
                sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="YlGnBu", linewidths=.5, ax=ax)
                ax.set_title("Category-Wise Spending Heatmap", fontsize=14)
                st.pyplot(fig)
            else:
                st.info("No expense data available for the heatmap!")

            # 🔹 Transaction Table (Scrollable on Mobile)
            st.subheader("📋 All Transactions")
            st.dataframe(filtered_df, height=300 if is_mobile else 500)

            # 🔹 Export Transactions to CSV
            st.subheader("⬇ Export Transactions to CSV")

            if not filtered_df.empty:
                # Convert DataFrame to CSV format
                csv_buffer = io.StringIO()
                filtered_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()

                # File Name Format
                today_date = datetime.datetime.today().strftime('%Y-%m-%d')
                file_name = f"transactions_{today_date}.csv"

                # Download Button
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=file_name,
                    mime="text/csv",
                )
            else:
                st.info("No transactions available to export.")

        else:
            st.warning("No valid transactions found!")

    except Exception as e:
        st.error(f"Error: {e}")
