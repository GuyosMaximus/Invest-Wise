import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
import time

# --- הגדרת תצורת העמוד ---
st.set_page_config(page_title="ניהול תיק השקעות", layout="wide")


# --- מנגנון אבטחה וכניסה עם סיסמה ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        col_login, _ = st.columns([1, 2])
        with col_login:
            st.markdown("<h2 style='text-align: right; direction: rtl;'>כניסה מאובטחת</h2>", unsafe_allow_html=True)
            pwd = st.text_input("הזן סיסמה", type="password")

            # בדיקת סיסמה מול Secrets בענן או ברירת מחדל מקומית
            correct_pass = st.secrets.get("APP_PASSWORD", "123456") if hasattr(st,
                                                                               "secrets") and "APP_PASSWORD" in st.secrets else "123456"

            if st.button("כניסה"):
                if pwd == correct_pass:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("סיסמה שגויה")
        return False
    return True


if not check_password():
    st.stop()

# --- טעינה ושמירה מאובטחת ---
DATA_FILE = "portfolio_data.json"


def load_portfolio():
    # אם רצים ב-Streamlit Cloud והוגדרו נתונים ב-Secrets
    if hasattr(st, "secrets") and "INITIAL_PORTFOLIO" in st.secrets:
        try:
            return json.loads(st.secrets["INITIAL_PORTFOLIO"])
        except:
            pass
    # אם רצים מקומית במחשב
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_portfolio(portfolio_data):
    # שמירה מקומית בלבד
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(portfolio_data, f, ensure_ascii=False, indent=4)


# הגדרת תצורת העמוד
st.set_page_config(page_title="ניהול תיק השקעות", layout="wide")

# הזרקת CSS לעיצוב
st.markdown("""
<style>
[data-testid="stForm"] {
    background-color: #082920;
    border-radius: 12px;
    padding: 30px;
    border: none;
    direction: rtl;
    text-align: right;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
[data-testid="stFormSubmitButton"] button {
    background-color: white !important;
    color: #082920 !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    width: 100%;
    border: none !important;
    padding: 8px !important;
    transition: 0.3s;
}
[data-testid="stFormSubmitButton"] button:hover {
    background-color: #e0e0e0 !important;
}
button { direction: rtl; }
[data-testid="stForm"] label { color: #a4c9b9 !important; }

/* תיקון עיצוב לטקסטים כהים בכפתורי רדיו ושדות */
[data-testid="stForm"] p { color: white !important; }
div[role="radiogroup"] label p { color: white !important; font-size: 15px; }
.stRadio label p { color: #a4c9b9 !important; } /* כותרת הרדיו */

.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #143e32 !important;
    color: white !important;
    border: 1px solid #1f5746 !important;
    border-radius: 6px !important;
}
.stSelectbox svg { fill: white !important; }

/* עיצוב כפתורי פלוס ומינוס של שדה המספר */
.stNumberInput button {
    background-color: #1f5746 !important;
    color: white !important;
}
.stNumberInput button:hover {
    background-color: #2ab588 !important;
}

/* עיצוב הלשוניות (Tabs) */
.stTabs [data-baseweb="tab-list"] {
    direction: rtl;
    gap: 20px;
}
.stTabs [data-baseweb="tab"] {
    font-size: 18px;
    font-weight: 600;
}
/* תיקון צבע הטקסט בתוך כפתורי הטופס */
[data-testid="stFormSubmitButton"] button p {
    color: #082920 !important;
}
</style>
""", unsafe_allow_html=True)

# אתחול
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = load_portfolio()

# --- מנגנון תיקון אוטומטי למזומן ---
# אם יש CASH בטעות, נמיר אותו ל-$CASH ונאחד יתרות כדי למנוע כפילויות
if 'CASH' in st.session_state['portfolio']:
    cash_amount = st.session_state['portfolio'].pop('CASH')['quantity']
    if '$CASH' in st.session_state['portfolio']:
        st.session_state['portfolio']['$CASH']['quantity'] += cash_amount
    else:
        st.session_state['portfolio']['$CASH'] = {'quantity': cash_amount, 'manual_price': 1.0, 'name': 'מזומן'}
    save_portfolio(st.session_state['portfolio'])

# כותרת
st.markdown("<h1 style='text-align: center; direction: rtl;'>Invest Wise</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- חלוקה ללשוניות ---
tab1, tab2 = st.tabs(["➕ הוספת נכס ראשוני לתיק", "💱 מסחר וניהול מזומן"])

# לשונית 1: הוספה ראשונית
with tab1:
    with st.form(key='add_position_form', clear_on_submit=True):
        st.markdown("<h2 style='color: white; text-align: right; margin-bottom: 0px;'>הוספת פוזיציה חדשה</h2>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p style='color: #2ab588; font-size: 16px; text-align: right; margin-bottom: 25px;'>הזינו את פרטי ההחזקה להקמה ראשונית של התיק</p>",
            unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col2:
            ticker_input = st.text_input("סימול, לדוגמה AAPL", placeholder="למשל TSLA")
            quantity_input = st.number_input("כמות", min_value=0, step=1)
            asset_type = st.selectbox("סוג נכס", options=["מניות", "אופציות", "מזומן", "קריפטו"],
                                      label_visibility="collapsed")

        with col1:
            asset_name = st.text_input("שם הנכס (אופציונלי)")
            manual_price = st.number_input("מחיר ליחידה ($)", min_value=0.0, step=0.1,
                                           help="השאר 0.0 כדי למשוך מחיר אוטומטית בזמן אמת")
            st.markdown("<br>", unsafe_allow_html=True)
            submit_add = st.form_submit_button(label="➕ הוספה לתיק")

        if submit_add and ticker_input:
            ticker = ticker_input.upper()
            if ticker == 'CASH':  # אכיפת שם אחיד למזומן כבר בהזנה
                ticker = '$CASH'

            if ticker in st.session_state['portfolio']:
                st.session_state['portfolio'][ticker]['quantity'] += quantity_input
            else:
                st.session_state['portfolio'][ticker] = {
                    'quantity': quantity_input,
                    'manual_price': manual_price if manual_price > 0 else None,
                    'name': asset_name
                }
            save_portfolio(st.session_state['portfolio'])
            st.rerun()

# לשונית 2: מסחר וניהול מזומן
with tab2:
    available_tickers = [t for t in st.session_state['portfolio'].keys() if
                         t not in ['CASH', '$CASH'] and st.session_state['portfolio'][t].get('name') != 'מזומן']

    # טופס מסחר מניות
    with st.form(key='trade_form', clear_on_submit=True):
        st.markdown("<h2 style='color: white; text-align: right; margin-bottom: 0px;'>ביצוע פעולה במניה</h2>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p style='color: #2ab588; font-size: 16px; text-align: right; margin-bottom: 25px;'>בחרו מניה מתוך התיק. המערכת תסנכרן את הכמות ואת שווי המזומן אוטומטית.</p>",
            unsafe_allow_html=True)

        col_t1, col_t2, col_t3 = st.columns([1, 1, 1.5])

        with col_t3:
            trade_ticker = st.selectbox("בחר מניה מהתיק", options=available_tickers)
        with col_t2:
            trade_action = st.radio("סוג פעולה", options=["קנייה (הגדלת פוזיציה)", "מכירה (הקטנת פוזיציה)"])
        with col_t1:
            trade_quantity = st.number_input("כמות מניות", min_value=1, step=1)
            st.markdown("<br>", unsafe_allow_html=True)
            submit_trade = st.form_submit_button(label="⚡ בצע פעולה במניה")

        if submit_trade and trade_ticker:
            try:
                stock = yf.Ticker(trade_ticker)
                current_price = float(stock.history(period="1d")['Close'].iloc[-1])
                cash_impact = current_price * trade_quantity

                if '$CASH' not in st.session_state['portfolio']:
                    st.session_state['portfolio']['$CASH'] = {'quantity': 0, 'manual_price': 1.0, 'name': 'מזומן'}

                if trade_action == "מכירה (הקטנת פוזיציה)":
                    if trade_quantity <= st.session_state['portfolio'][trade_ticker]['quantity']:
                        st.session_state['portfolio'][trade_ticker]['quantity'] -= trade_quantity
                        st.session_state['portfolio']['$CASH']['quantity'] += cash_impact
                        st.success(
                            f"נמכרו {trade_quantity} מניות של {trade_ticker}. התווספו ${cash_impact:,.2f} למזומן.")
                        if st.session_state['portfolio'][trade_ticker]['quantity'] <= 0:
                            del st.session_state['portfolio'][trade_ticker]
                    else:
                        st.error("שגיאה: אין מספיק מניות למכירה.")

                elif trade_action == "קנייה (הגדלת פוזיציה)":
                    st.session_state['portfolio'][trade_ticker]['quantity'] += trade_quantity
                    st.session_state['portfolio']['$CASH']['quantity'] -= cash_impact
                    st.success(f"נרכשו {trade_quantity} מניות של {trade_ticker}. יתרת המזומן עודכנה.")

                save_portfolio(st.session_state['portfolio'])
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error("שגיאה במשיכת נתוני המניה. נסה שוב.")

    # טופס ניהול מזומן ישיר
    with st.form(key='cash_form', clear_on_submit=True):
        st.markdown("<h2 style='color: white; text-align: right; margin-bottom: 0px;'>הפקדה / משיכת מזומן ($CASH)</h2>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p style='color: #2ab588; font-size: 16px; text-align: right; margin-bottom: 25px;'>עדכן את יתרת המזומן החופשי בחשבון ללא קשר לפעולות מסחר.</p>",
            unsafe_allow_html=True)

        col_c1, col_c2, col_c3 = st.columns([1, 1, 1.5])

        with col_c3:
            cash_action = st.radio("פעולה במזומן", options=["הפקדה לחשבון", "משיכה מהחשבון"])
        with col_c2:
            cash_amount = st.number_input("סכום בדולרים ($)", min_value=1.0, step=100.0)
        with col_c1:
            st.markdown("<br>", unsafe_allow_html=True)
            submit_cash = st.form_submit_button(label="💵 עדכן מזומן")

        if submit_cash:
            if '$CASH' not in st.session_state['portfolio']:
                st.session_state['portfolio']['$CASH'] = {'quantity': 0, 'manual_price': 1.0, 'name': 'מזומן'}

            if cash_action == "הפקדה לחשבון":
                st.session_state['portfolio']['$CASH']['quantity'] += cash_amount
                st.success(f"הופקדו ${cash_amount:,.2f} למזומן בהצלחה.")
            elif cash_action == "משיכה מהחשבון":
                st.session_state['portfolio']['$CASH']['quantity'] -= cash_amount
                st.success(f"נמשכו ${cash_amount:,.2f} מיתרת המזומן בהצלחה.")

            save_portfolio(st.session_state['portfolio'])
            time.sleep(1.5)
            st.rerun()

# כפתור מחיקת התיק
if st.session_state['portfolio']:
    col_clear, _ = st.columns([1, 8])
    with col_clear:
        if st.button("🗑️ נקה את כל התיק", use_container_width=True):
            st.session_state['portfolio'] = {}
            save_portfolio(st.session_state['portfolio'])
            st.rerun()

st.divider()

# --- לוגיקה וחישובים להצגת התיק ---
if st.session_state['portfolio']:
    data = []

    for ticker_key, info in st.session_state['portfolio'].items():
        quantity = info['quantity']
        manual_price = info.get('manual_price')

        if ticker_key in ['CASH', '$CASH'] or info.get('name') == 'מזומן':
            price = 1.0
            ticker_display = "$CASH"
        else:
            ticker_display = ticker_key
            if manual_price is not None:
                price = manual_price
            else:
                try:
                    stock = yf.Ticker(ticker_key)
                    price = float(stock.history(period="1d")['Close'].iloc[-1])
                except:
                    price = 0.0

        value = price * quantity
        data.append({
            "Original_Key": ticker_key,
            "Ticker": ticker_display,
            "Quantity": quantity,
            "Price": price,
            "Value": value
        })

    df = pd.DataFrame(data)

    total_value = df['Value'].sum()
    if total_value > 0:
        df['Percentage'] = (df['Value'] / total_value) * 100
    else:
        df['Percentage'] = 0

    df = df.sort_values(by='Percentage', ascending=False).reset_index(drop=True)

    # --- תצוגה ויזואלית ---
    col_chart, col_total = st.columns([3, 1])

    with col_total:
        st.markdown(f"""
        <div style="background-color: #082920; padding: 20px; border-radius: 12px; text-align: center; margin-top: 100px; border: 1px solid #1f5746;">
            <div style="color: #a4c9b9; font-size: 16px;">שווי תיק כולל</div>
            <div style="color: white; font-size: 28px; font-weight: 900;">${total_value:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_chart:
        fig = px.pie(
            df,
            values='Value',
            names='Ticker',
            hole=0.55,
            color_discrete_sequence=['#0d6e4f', '#209e74', '#16b87d', '#1abc9c', '#6f7e8c', '#8cc63f']
        )
        fig.update_traces(
            textinfo='label',
            textfont=dict(color='white', size=13),
            hovertemplate="<b>%{label}</b> : $%{value:,.1f} · %{percent:.1%}<extra></extra>"
        )
        fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=0, r=0), height=450)
        st.plotly_chart(fig, use_container_width=True)

    cols = st.columns(3)
    for index, row in df.iterrows():
        card_html = f"""
        <div style="background-color: #ffffff; padding: 12px 20px; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05); display: flex;
                    justify-content: space-between; align-items: center; margin-bottom: 15px;
                    border: 1px solid #f0f0f0; direction: ltr;">
            <div style="font-weight: bold; color: #16b87d; font-size: 14px;">{row['Percentage']:.1f}%</div>
            <div style="text-align: right; flex-grow: 1; padding-right: 15px;">
                <div style="font-weight: 800; font-size: 16px; color: #1e2b3c;">{row['Ticker']}</div>
                <div style="color: #8c9ba5; font-size: 13px;">${row['Value']:,.2f}</div>
            </div>
            <div style="width: 8px; height: 35px; background-color: #16b87d; border-radius: 4px;"></div>
        </div>
        """
        cols[2 - (index % 3)].markdown(card_html, unsafe_allow_html=True)

    st.divider()

    # --- טבלת פוזיציות בתיק ---
    st.markdown("<h2 style='text-align: right; direction: rtl;'>פוזיציות בתיק</h2>", unsafe_allow_html=True)

    df_table_data = []
    for i, row in df.iterrows():
        df_table_data.append({
            "Original_Key": row['Original_Key'],
            "#": i + 1,
            "נכס": row['Ticker'],
            "כמות": row['Quantity'],
            "מחיר ($)": row['Price'],
            "שווי ($)": row['Value'],
            "נתח (%)": row['Percentage'],
            "מחיקה": False
        })

    df_table = pd.DataFrame(df_table_data)
    df_table.set_index("Original_Key", inplace=True)

    edited_df = st.data_editor(
        df_table,
        column_config={
            "#": st.column_config.NumberColumn("#", disabled=True),
            "נכס": st.column_config.TextColumn("נכס", disabled=True),
            "כמות": st.column_config.NumberColumn("כמות", disabled=True),
            "מחיר ($)": st.column_config.NumberColumn("מחיר ($)", format="$%.2f", disabled=True),
            "שווי ($)": st.column_config.NumberColumn("שווי ($)", format="$%.2f", disabled=True),
            "נתח (%)": st.column_config.NumberColumn("נתח (%)", format="%.1f%%", disabled=True),
            "מחיקה": st.column_config.CheckboxColumn("🗑️ מחיקה מהירה", default=False)
        },
        use_container_width=True,
        key="portfolio_table"
    )

    needs_rerun = False

    for key, row in edited_df.iterrows():
        to_delete = row['מחיקה']
        if key in st.session_state['portfolio'] and to_delete:
            del st.session_state['portfolio'][key]
            needs_rerun = True

    if needs_rerun:
        save_portfolio(st.session_state['portfolio'])
        if 'portfolio_table' in st.session_state:
            del st.session_state['portfolio_table']
        st.rerun()

else:
    st.info("התיק שלך ריק. הוסף מניות באמצעות הטופס למעלה.")