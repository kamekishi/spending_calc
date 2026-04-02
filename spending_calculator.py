import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(layout="wide")  # 👈 Add this line

# -----------------------------
# Helpers
# -----------------------------
def format_rm(value):
    return f"RM {value:,.2f}"

DATA_FILE = "data.json"

def get_recommended_budget(total_income):
    """
    Simple salary-based recommendation model.
    Returns recommended % split for Fixed / Variable / Savings.
    """
    if total_income < 3000:
        return {"Fixed": 55, "Variable": 30, "Savings": 15}
    elif total_income < 6000:
        return {"Fixed": 50, "Variable": 30, "Savings": 20}
    elif total_income < 10000:
        return {"Fixed": 45, "Variable": 30, "Savings": 25}
    else:
        return {"Fixed": 40, "Variable": 25, "Savings": 35}

def calculate_financial_score(total_income, fixed_total, variable_total, savings_total, debt_monthly_total):
    """
    Basic financial health score from 0–100.
    Higher savings, lower debt burden, and controlled spending improve score.
    """
    if total_income <= 0:
        return 0

    committed_ratio = (fixed_total + debt_monthly_total) / total_income
    lifestyle_ratio = variable_total / total_income
    savings_ratio = savings_total / total_income

    score = 100

    # Penalize high committed obligations
    if committed_ratio > 0.6:
        score -= 30
    elif committed_ratio > 0.5:
        score -= 20
    elif committed_ratio > 0.4:
        score -= 10

    # Penalize high variable spending
    if lifestyle_ratio > 0.35:
        score -= 20
    elif lifestyle_ratio > 0.25:
        score -= 10

    # Reward healthy savings
    if savings_ratio >= 0.25:
        score += 10
    elif savings_ratio >= 0.15:
        score += 5
    elif savings_ratio < 0.05:
        score -= 20

    # Penalize overspending
    net_balance = total_income - (fixed_total + variable_total + savings_total + debt_monthly_total)
    if net_balance < 0:
        score -= 30
    elif net_balance < total_income * 0.05:
        score -= 10

    return max(0, min(100, round(score)))

def estimate_debt_months_left(balance_remaining, monthly_payment):
    if monthly_payment <= 0:
        return None
    if balance_remaining <= 0:
        return 0
    return int((balance_remaining + monthly_payment - 1) // monthly_payment)

# -----------------------------
# Load / Save
# -----------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.users, f, indent=4)

# -----------------------------
# Init State
# -----------------------------
if "users" not in st.session_state:
    st.session_state.users = load_data()

# Ensure older saved users get the new debts field
for username in st.session_state.users:
    st.session_state.users[username].setdefault("debts", {})

if "selected_user" not in st.session_state:
    st.session_state.selected_user = None

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("👤 User Management")

user_names = list(st.session_state.users.keys())

selected_user = st.sidebar.selectbox(
    "Select User",
    user_names,
    index=user_names.index(st.session_state.selected_user) if st.session_state.selected_user in user_names else 0 if user_names else None
)

if selected_user:
    st.session_state.selected_user = selected_user

st.sidebar.subheader("➕ Create User")
new_name = st.sidebar.text_input("Name")
basic_income = st.sidebar.number_input("Basic Monthly Income", min_value=0.0)
annual_increment = st.sidebar.number_input("Annual Increment (RM)", min_value=0.0)

if st.sidebar.button("Create User"):
    if new_name:
        st.session_state.users[new_name] = {
            "basic_income": basic_income,
            "annual_increment": annual_increment,
            "allowances": {},
            "extra_income": {},
            "fixed": {},
            "variable": {},
            "savings": {},
            "debts": {}
        }
        save_data()
        st.session_state.selected_user = new_name
        st.rerun()

# -----------------------------
# UI Styling (Premium Cards)
# -----------------------------
st.markdown("""
<style>
.card {
    background-color: #1e1e1e;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    margin-bottom: 10px;
    color: white;
}
.metric {
    font-size: 24px;
    font-weight: bold;
    color: white;
}
.metric {
    font-size: 24px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Main
# -----------------------------
st.title("💰 Personal Finance Dashboard")

if st.session_state.selected_user:
    user = st.session_state.users[st.session_state.selected_user]
    user.setdefault("debts", {})

    tabs = st.tabs(["Dashboard", "Income", "Fixed", "Variable", "Savings", "Debts", "Forecast"])

    # ---------------- Dashboard ----------------
    with tabs[0]:
        total_income = user["basic_income"] + sum(user["allowances"].values()) + sum(user["extra_income"].values())
        fixed_total = sum(user["fixed"].values())
        variable_total = sum(user["variable"].values())
        savings_total = sum(user["savings"].values())
        debt_monthly_total = sum(
            debt.get("monthly_payment", 0) for debt in user["debts"].values()
        )
        net = total_income - (fixed_total + variable_total + savings_total + debt_monthly_total)

        financial_score = calculate_financial_score(
            total_income,
            fixed_total,
            variable_total,
            savings_total,
            debt_monthly_total
        )

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        col1.markdown(
            f"<div class='card'><div>Income</div><div class='metric'>{format_rm(total_income)}</div></div>",
            unsafe_allow_html=True
        )
        col2.markdown(
            f"<div class='card'><div>Fixed</div><div class='metric'>{format_rm(fixed_total)}</div></div>",
            unsafe_allow_html=True
        )
        col3.markdown(
            f"<div class='card'><div>Variable</div><div class='metric'>{format_rm(variable_total)}</div></div>",
            unsafe_allow_html=True
        )
        col4.markdown(
            f"<div class='card'><div>Savings</div><div class='metric'>{format_rm(savings_total)}</div></div>",
            unsafe_allow_html=True
        )
        col5.markdown(
            f"<div class='card'><div>Net Balance</div><div class='metric'>{format_rm(net)}</div></div>",
            unsafe_allow_html=True
        )
        col6.markdown(
            f"<div class='card'><div>Financial Score</div><div class='metric'>{financial_score}/100</div></div>",
            unsafe_allow_html=True
        )

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("### Financial Summary")
            actual_data = pd.DataFrame({
                "Category": ["Fixed", "Variable", "Savings", "Debt Payment"],
                "Amount": [fixed_total, variable_total, savings_total, debt_monthly_total]
            })

            actual_data = actual_data[actual_data["Amount"] > 0]

            if not actual_data.empty:
                fig1 = actual_data.set_index("Category").plot.pie(
                    y="Amount",
                    autopct='%1.1f%%',
                    legend=False,
                    figsize=(5, 5)
                ).figure
                st.pyplot(fig1)
            else:
                st.info("No financial data available yet.")

        with chart_col2:
            st.markdown("### Recommendation")
            recommended_pct = get_recommended_budget(total_income)

            recommendation_data = pd.DataFrame({
                "Category": ["Fixed", "Variable", "Savings"],
                "Amount": [
                    total_income * recommended_pct["Fixed"] / 100,
                    total_income * recommended_pct["Variable"] / 100,
                    total_income * recommended_pct["Savings"] / 100
                ]
            })

            fig2 = recommendation_data.set_index("Category").plot.pie(
                y="Amount",
                autopct='%1.1f%%',
                legend=False,
                figsize=(5, 5)
            ).figure
            st.pyplot(fig2)

            st.caption(
                f"Suggested split based on current salary ({format_rm(total_income)}): "
                f"Fixed {recommended_pct['Fixed']}% · "
                f"Variable {recommended_pct['Variable']}% · "
                f"Savings {recommended_pct['Savings']}%"
            )

    # ---------------- Income ----------------
    with tabs[1]:
        user["basic_income"] = st.number_input("Basic Income", value=user["basic_income"])
        user["annual_increment"] = st.number_input("Annual Increment", value=user["annual_increment"])

        st.subheader("Allowances")
        for k in list(user["allowances"].keys()):
            val = st.number_input(k, value=user["allowances"][k], key=f"a_{k}")
            user["allowances"][k] = val
            if st.button("Delete", key=f"del_a_{k}"):
                del user["allowances"][k]

        new_a = st.text_input("New Allowance")
        new_a_val = st.number_input("Amount", key="new_a")
        if st.button("Add Allowance") and new_a:
            user["allowances"][new_a] = new_a_val

        st.subheader("Extra Income")
        for k in list(user["extra_income"].keys()):
            val = st.number_input(k, value=user["extra_income"][k], key=f"e_{k}")
            user["extra_income"][k] = val
            if st.button("Delete", key=f"del_e_{k}"):
                del user["extra_income"][k]

        new_e = st.text_input("New Extra Income")
        new_e_val = st.number_input("Amount", key="new_e")
        if st.button("Add Extra Income") and new_e:
            user["extra_income"][new_e] = new_e_val

        save_data()

    # ---------------- Spending ----------------
    def spending_tab(title, key):
        data = user[key]
        df = pd.DataFrame(list(data.items()), columns=["Item", "Amount"])

        col1, col2 = st.columns([2, 1])

        with col1:
            if not df.empty:
                st.dataframe(df, use_container_width=True)

                for item in list(data.keys()):
                    row_col1, row_col2, row_col3 = st.columns([4, 2, 1])

                    with row_col1:
                        st.text_input("Item", value=item, key=f"label_{key}_{item}", disabled=True, label_visibility="collapsed")

                    with row_col2:
                        val = st.number_input(
                            "Amount",
                            value=float(data[item]),
                            key=f"{key}_{item}",
                            label_visibility="collapsed"
                        )
                        data[item] = val

                    with row_col3:
                        if st.button("Delete", key=f"del_{key}_{item}", use_container_width=True):
                            del data[item]
                            st.rerun()

        with col2:
            if not df.empty and df["Amount"].sum() > 0:
                pie_fig = df.set_index("Item").plot.pie(
                    y="Amount",
                    autopct='%1.1f%%',
                    legend=False,
                    figsize=(5, 5)
                ).figure
                st.pyplot(pie_fig)

        st.markdown(f"### Add New {title}")
        add_col1, add_col2, add_col3 = st.columns([4, 2, 1])

        with add_col1:
            name = st.text_input(f"New {title} Name", key=f"name_{key}", label_visibility="collapsed", placeholder=f"New {title}")

        with add_col2:
            val = st.number_input("Amount", key=f"new_{key}", label_visibility="collapsed", min_value=0.0)

        with add_col3:
            if st.button("Add", key=f"add_{key}", use_container_width=True) and name:
                data[name] = val
                save_data()
                st.rerun()

        save_data()

    with tabs[2]:
        spending_tab("Fixed", "fixed")

    with tabs[3]:
        spending_tab("Variable", "variable")

    with tabs[4]:
        spending_tab("Savings", "savings")

    # ---------------- Forecast ----------------
    with tabs[6]:
        years = st.slider("Years", 1, 10, 5)

        base_income = user["basic_income"]
        increment = user["annual_increment"]
        monthly_spending = (
            sum(user["fixed"].values())
            + sum(user["variable"].values())
            + sum(debt.get("monthly_payment", 0) for debt in user["debts"].values())
        )

        forecast = []
        savings_accum = 0

        for y in range(1, years+1):
            annual_income = base_income * 12
            annual_spending = monthly_spending * 12
            yearly_saving = annual_income - annual_spending
            savings_accum += yearly_saving

            forecast.append({
                "Year": y,
                "Income": annual_income,
                "Spending": annual_spending,
                "Total Savings": savings_accum
            })

            base_income += increment

        df = pd.DataFrame(forecast)
        st.dataframe(df)
        st.line_chart(df.set_index("Year"))
    
    # ---------------- Debts ----------------
    with tabs[5]:
        st.subheader("Debt Tracker")

        debts = user["debts"]

        if debts:
            debt_rows = []
            for debt_name, debt_data in debts.items():
                total_amount = float(debt_data.get("total_amount", 0))
                paid_amount = float(debt_data.get("paid_amount", 0))
                monthly_payment = float(debt_data.get("monthly_payment", 0))
                remaining_balance = max(total_amount - paid_amount, 0)
                months_left = estimate_debt_months_left(remaining_balance, monthly_payment)

                debt_rows.append({
                    "Debt": debt_name,
                    "Total Amount": total_amount,
                    "Paid Amount": paid_amount,
                    "Remaining Balance": remaining_balance,
                    "Monthly Payment": monthly_payment,
                    "Months Left": "Paid Off" if months_left == 0 else ("N/A" if months_left is None else months_left)
                })

            debt_df = pd.DataFrame(debt_rows)
            st.dataframe(debt_df, use_container_width=True)

            st.markdown("### Edit Debts")

            for debt_name in list(debts.keys()):
                debt_data = debts[debt_name]

                row1, row2, row3, row4, row5 = st.columns([3, 2, 2, 2, 1])

                with row1:
                    st.text_input("Debt Name", value=debt_name, key=f"debt_label_{debt_name}", disabled=True, label_visibility="collapsed")

                with row2:
                    debt_data["total_amount"] = st.number_input(
                        "Total Amount",
                        min_value=0.0,
                        value=float(debt_data.get("total_amount", 0)),
                        key=f"debt_total_{debt_name}",
                        label_visibility="collapsed"
                    )

                with row3:
                    debt_data["paid_amount"] = st.number_input(
                        "Paid Amount",
                        min_value=0.0,
                        value=float(debt_data.get("paid_amount", 0)),
                        key=f"debt_paid_{debt_name}",
                        label_visibility="collapsed"
                    )

                with row4:
                    debt_data["monthly_payment"] = st.number_input(
                        "Monthly Payment",
                        min_value=0.0,
                        value=float(debt_data.get("monthly_payment", 0)),
                        key=f"debt_monthly_{debt_name}",
                        label_visibility="collapsed"
                    )

                with row5:
                    if st.button("Delete", key=f"delete_debt_{debt_name}", use_container_width=True):
                        del debts[debt_name]
                        save_data()
                        st.rerun()

        st.markdown("### Add New Debt")
        add1, add2, add3, add4, add5 = st.columns([3, 2, 2, 2, 1])

        with add1:
            new_debt_name = st.text_input("Debt Name", key="new_debt_name", label_visibility="collapsed", placeholder="Debt Name")

        with add2:
            new_debt_total = st.number_input("Total Debt", min_value=0.0, key="new_debt_total", label_visibility="collapsed")

        with add3:
            new_debt_paid = st.number_input("Paid Amount", min_value=0.0, key="new_debt_paid", label_visibility="collapsed")

        with add4:
            new_debt_monthly = st.number_input("Monthly Payment", min_value=0.0, key="new_debt_monthly", label_visibility="collapsed")

        with add5:
            if st.button("Add", key="add_debt_btn", use_container_width=True) and new_debt_name:
                debts[new_debt_name] = {
                    "total_amount": new_debt_total,
                    "paid_amount": new_debt_paid,
                    "monthly_payment": new_debt_monthly
                }
                save_data()
                st.rerun()

        save_data()

else:
    st.info("Create a user to begin")
