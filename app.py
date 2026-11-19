import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src import queries as q

DB_PATH = str(Path(__file__).resolve().parent / "Data/sales.db")
NAVY, BLUE, TEAL, PURPLE, RED, SLATE, BG, LINE = "#101828", "#3B82F6", "#14B8A6", "#8B5CF6", "#EF4444", "#CBD5E1", "#0B1220", "#263449"
PALETTE = [BLUE, TEAL, PURPLE, "#F59E0B", RED, "#64748B"]
PAGES = ["📊  Overview", "🎯  Sales performance", "💰  Revenue analysis", "📦  Product analysis",
         "👥  Customer analysis", "🌍  Regional analysis", "📈  Sales trends", "⚙️  Settings"]

st.set_page_config(page_title="Sales Analytics Dashboard", page_icon="📊", layout="wide")
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, label {{ font-family: 'Inter', sans-serif !important; }}
#MainMenu, footer {{ visibility: hidden; }} header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding: 1.6rem 2.2rem 3rem; max-width: 1400px; }}
[data-testid="stSidebar"] {{ background: {NAVY}; min-width: 290px; border-right: 1px solid rgba(255,255,255,.08); }}
[data-testid="stSidebar"] [role="radiogroup"] {{ gap: 4px; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ padding: .7rem .95rem; border-radius: 10px; width: 100%; cursor: pointer; transition: background .15s; }}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: rgba(255,255,255,.09); }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background: {BLUE}; }}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{ display: none; }}
[data-testid="stSidebar"] [role="radiogroup"] label p {{ color: #F2F4F7 !important; font-size: 1rem; font-weight: 600; }}
.logo {{ color: #fff; font-size: 1.45rem; font-weight: 800; letter-spacing: -.02em; padding: .4rem .4rem 0; }}
.logo span {{ color: {BLUE}; }} .logo-sub {{ color: #98A2B3; font-size: .85rem; padding: 0 .4rem 1.2rem; }}
.title {{ font-size: 2.1rem; font-weight: 800; color: inherit; letter-spacing: -.03em; line-height: 1.15; }}
.subtitle {{ color: inherit; opacity: .8; font-size: 1.02rem; margin-top: .25rem; }}
.pill {{ display: inline-block; background: rgba(127,127,127,.09); border: 1px solid rgba(127,127,127,.30); color: inherit; border-radius: 999px; padding: .4rem .9rem; font-size: .88rem; font-weight: 600; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; margin: .6rem 0 1.2rem; }}
.kpi {{ background: rgba(127,127,127,.09); border: 1px solid rgba(127,127,127,.30); border-radius: 16px; padding: 1.1rem 1.2rem; box-shadow: 0 1px 3px rgba(16,24,40,.06); transition: transform .15s, box-shadow .15s; }}
.kpi:hover {{ transform: translateY(-3px); box-shadow: 0 10px 24px rgba(16,24,40,.10); }}
.kpi .top {{ display: flex; justify-content: space-between; align-items: center; color: inherit; opacity: .85; font-weight: 600; font-size: .95rem; }}
.kpi .ico {{ background: rgba(59,130,246,.18); border-radius: 10px; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; font-size: 1.15rem; }}
.kpi .val {{ font-size: 2.1rem; font-weight: 800; color: inherit; letter-spacing: -.03em; margin: .5rem 0 .2rem; }}
.kpi .d {{ font-weight: 700; font-size: .9rem; }} .up {{ color: #14B8A6; }} .down {{ color: #EF4444; }} .flat {{ color: #667085; }}
.ptitle {{ font-weight: 700; font-size: 1.1rem; color: inherit; margin-bottom: .2rem; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background: rgba(127,127,127,.09); border-radius: 16px; border-color: rgba(127,127,127,.30); box-shadow: 0 1px 3px rgba(16,24,40,.05); }}
.ins {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(270px, 1fr)); gap: 16px; }}
.insight {{ background: rgba(127,127,127,.09); border: 1px solid rgba(127,127,127,.30); border-left: 5px solid {BLUE}; border-radius: 14px; padding: 1rem 1.2rem; }}
.insight.good {{ border-left-color: {TEAL}; }} .insight.warn {{ border-left-color: {RED}; }} .insight.tip {{ border-left-color: {PURPLE}; }}
.insight b {{ color: inherit; font-size: 1rem; }} .insight p {{ color: inherit; opacity: .85; margin: .35rem 0 0; font-size: .96rem; line-height: 1.5; }}
.empty {{ text-align: center; padding: 2.5rem 1rem; color: inherit; opacity: .8; font-weight: 500; background: rgba(127,127,127,.09); border: 1px dashed rgba(127,127,127,.30); border-radius: 14px; }}
@media (max-width: 900px) {{ .block-container {{ padding: 1rem; }} .title {{ font-size: 1.6rem; }} .kpi .val {{ font-size: 1.7rem; }} }}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def run_query(sql, params=None):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params or {})


CUR = st.session_state.get("cur", "₦")


def compact(x):
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(x) >= div:
            return f"{CUR}{x / div:,.1f}{suf}"
    return f"{CUR}{x:,.0f}"


def pct(new, old):
    return None if not old else (new - old) / old * 100


def style(fig, h=340, legend=False, xt=None, yt=None):
    fig.update_layout(height=h, margin=dict(l=0, r=0, t=10, b=0), showlegend=legend, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", size=13),
                      hoverlabel=dict(bgcolor="#0B1220", font_color="#fff", bordercolor=BLUE),
                      legend=dict(orientation="h", y=1.12, x=0, title=None))
    fig.update_xaxes(showgrid=False, linecolor="rgba(127,127,127,.4)", title=xt)
    fig.update_yaxes(gridcolor="rgba(127,127,127,.2)", zeroline=False, title=yt)
    return fig


def panel(title, fig=None):
    with st.container(border=True):
        st.markdown(f'<div class="ptitle">{title}</div>', unsafe_allow_html=True)
        if fig is None:
            st.markdown('<div class="empty">No data for the selected filters.<br>Try a wider date range.</div>', unsafe_allow_html=True)
        else:
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def kpi(icon, label, value, d):
    cls, txt = ("flat", "No earlier period") if d is None else (("up", f"▲ {d:+.1f}%") if d >= 0 else ("down", f"▼ {d:+.1f}%"))
    return (f'<div class="kpi"><div class="top">{label}<div class="ico">{icon}</div></div>'
            f'<div class="val">{value}</div><div class="d {cls}">{txt} <span class="flat">vs previous period</span></div></div>')


# ---------- Sidebar navigation ----------
with st.sidebar:
    st.markdown('<div class="logo">Bright<span>Mart</span></div><div class="logo-sub">Sales intelligence</div>', unsafe_allow_html=True)
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")

# ---------- Header + filters ----------
updated = datetime.fromtimestamp(os.path.getmtime(DB_PATH)).strftime("%d %b %Y, %H:%M")
h1, h2 = st.columns([3, 1])
h1.markdown(f'<div class="title">Sales Analytics Dashboard</div><div class="subtitle">Revenue, products, customers and team performance in one place. '
            f'Figures count completed orders only.</div>', unsafe_allow_html=True)
h2.markdown(f'<div style="text-align:right;padding-top:.6rem"><span class="pill">🕒 Updated {updated}</span></div>', unsafe_allow_html=True)

bounds = run_query(q.DATE_BOUNDS).iloc[0]
try:
    default_range = (date.fromisoformat(bounds["first_date"]), date.fromisoformat(bounds["last_date"]))
except (TypeError, ValueError):
    default_range = (date(2024, 1, 1), date.today())
with st.container(border=True):
    f1, f2, f3 = st.columns(3)
    date_range = f1.date_input("Date range", value=default_range)
    region = f2.selectbox("Region", ["All"] + run_query(q.REGIONS)["region"].tolist())
    channel = f3.selectbox("Channel", ["All"] + run_query(q.CHANNELS)["channel"].tolist())
if len(date_range) != 2:
    st.info("Pick both a start and an end date.")
    st.stop()

start, end = date_range
P = {"start": str(start), "end": str(end), "region": region, "channel": channel}
span = (end - start).days + 1
PREV = {**P, "start": str(start - timedelta(days=span)), "end": str(start - timedelta(days=1))}
st.write("")

with st.spinner("Loading data..."):
    cur = run_query(q.KPIS, P).iloc[0].fillna(0)
    old = run_query(q.KPIS, PREV).iloc[0].fillna(0)
    monthly = run_query(q.trend("%Y-%m"), P)
    prod = run_query(q.BY_PRODUCT, P)
    reg = run_query(q.BY_REGION, P)

revenue, orders, units, custs = float(cur["revenue"]), int(cur["orders"]), int(cur["units"]), int(cur["customers"])
aov = revenue / orders if orders else 0
old_aov = float(old["revenue"]) / int(old["orders"]) if int(old["orders"]) else 0
growth = pct(revenue, float(old["revenue"]))

if page.endswith("Overview"):
    st.markdown('<div class="kpis">' + "".join([
        kpi("💰", "Total revenue", compact(revenue), growth),
        kpi("🛒", "Total sales (units)", f"{units:,}", pct(units, int(old["units"]))),
        kpi("🧾", "Total orders", f"{orders:,}", pct(orders, int(old["orders"]))),
        kpi("🏷️", "Average order value", compact(aov), pct(aov, old_aov)),
        kpi("👥", "Total customers", f"{custs:,}", pct(custs, int(old["customers"]))),
        kpi("📈", "Sales growth", "n/a" if growth is None else f"{growth:+.1f}%", growth)]) + "</div>", unsafe_allow_html=True)


def line_revenue(df):
    fig = px.line(df.melt("period", ["revenue", "profit"], "Measure", "Amount"), x="period", y="Amount", color="Measure",
                  markers=True, color_discrete_map={"revenue": BLUE, "profit": TEAL})
    fig.update_traces(line_width=3, hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>")
    return style(fig, 340, True, "Period", f"Amount ({CUR})")


def bar_units(df):
    fig = px.bar(df, x="period", y="units", color_discrete_sequence=[BLUE])
    fig.update_traces(hovertemplate="%{x}<br>%{y:,.0f} units<extra></extra>")
    return style(fig, 340, False, "Month", "Units sold")


def donut(df, names, values):
    fig = px.pie(df, names=names, values=values, hole=0.62, color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent", hovertemplate="%{label}<br>%{value:,.0f}<extra></extra>")
    return style(fig, 340, True)


def hbar(df, x, y, color=BLUE, h=340, xt=None):
    d = df.sort_values(x)
    fig = px.bar(d, x=x, y=y, orientation="h", color_discrete_sequence=[color])
    fig.update_traces(hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>")
    return style(fig, h, False, xt, None)


def growth_chart(df):
    g = df.assign(growth=df["revenue"].pct_change() * 100).dropna(subset=["growth"])
    if g.empty:
        return None
    g["tone"] = g["growth"].apply(lambda v: "Growth" if v >= 0 else "Decline")
    fig = px.bar(g, x="period", y="growth", color="tone", color_discrete_map={"Growth": TEAL, "Decline": RED})
    fig.update_traces(hovertemplate="%{x}<br>%{y:+.1f}%<extra></extra>")
    return style(fig, 340, True, "Period", "Change vs previous period (%)")


def insight_cards():
    pm = run_query(q.PRODUCT_MONTHLY, P)
    items = []
    if not prod.empty:
        b = prod.sort_values("revenue").iloc[-1]
        items.append(("good", "🏆 Best-performing product", f"{b['product']} leads with {compact(b['revenue'])} ({b['revenue'] / prod['revenue'].sum():.0%} of revenue)."))
    if not reg.empty:
        r = reg.iloc[0]
        items.append(("", "🌍 Top region", f"{r['region']} generates {compact(r['revenue'])}, {r['revenue'] / reg['revenue'].sum():.0%} of the total."))
    if not monthly.empty:
        m = monthly.sort_values("revenue").iloc[-1]
        items.append(("", "📅 Strongest month", f"{m['period']} had the highest revenue at {compact(m['revenue'])}."))
    if len(monthly) >= 2:
        g = pct(monthly["revenue"].iloc[-1], monthly["revenue"].iloc[-2])
        if g is not None:
            items.append(("good" if g >= 0 else "warn", "📈 Latest month trend", f"Revenue in {monthly['period'].iloc[-1]} is {g:+.1f}% versus the month before."))
    decl = pd.Series(dtype=float)
    months = sorted(pm["month"].unique())
    if len(months) >= 4:
        half = months[len(months) // 2]
        a = pm[pm["month"] < half].groupby("product")["revenue"].sum()
        b2 = pm[pm["month"] >= half].groupby("product")["revenue"].sum()
        ch = ((b2 - a) / a).dropna()
        decl = ch[ch < -0.10].sort_values().head(3)
    if len(decl):
        txt = ", ".join(f"{n} ({v:+.0%})" for n, v in decl.items())
        items.append(("warn", "⚠️ Declining products", f"Second half of the period vs the first: {txt}."))
        items.append(("tip", "💡 Recommendation", f"Review pricing, stock and promotions for {decl.index[0]}, and put more marketing behind the best seller."))
    elif items:
        items.append(("tip", "💡 Recommendation", "No product shows a sharp decline. Keep stock of the best seller high and test promotions on slower products."))
    if items:
        st.markdown('<div class="ptitle" style="margin:1.2rem 0 .6rem;font-size:1.3rem">Insights</div><div class="ins">' + "".join(
            f'<div class="insight {c}"><b>{t}</b><p>{x}</p></div>' for c, t, x in items) + "</div>", unsafe_allow_html=True)


# ---------- Pages ----------
if page.endswith("Overview"):
    a, b = st.columns([3, 2])
    with a: panel("Revenue and profit over time", line_revenue(monthly) if not monthly.empty else None)
    with b: panel("Sales by product category", donut(run_query(q.BY_CATEGORY, P), "category", "revenue") if not prod.empty else None)
    a, b = st.columns(2)
    with a: panel("Monthly sales performance", bar_units(monthly) if not monthly.empty else None)
    with b: panel("Top-performing products", hbar(prod.nlargest(8, "revenue"), "revenue", "product", TEAL, 340, f"Revenue ({CUR})") if not prod.empty else None)
    insight_cards()

elif page.endswith("Sales performance"):
    emp = run_query(q.EMPLOYEE_PERFORMANCE, P)
    years = run_query(q.YEARS)["year"].tolist()
    a, b = st.columns(2)
    with a:
        panel("Revenue by employee", hbar(emp, "revenue", "employee", BLUE, 430, f"Revenue ({CUR})") if not emp.empty else None)
    with b:
        fig, tgt = None, pd.DataFrame()
        yr = st.selectbox("Target year", years) if years else None
        if yr:
            tgt = run_query(q.TARGET_ATTAINMENT, {"year": int(yr), "region": region})
            if not tgt.empty:
                tgt["status"] = tgt["pct_of_target"].apply(lambda v: "On or above target" if v >= 100 else "Below target")
                fig = px.bar(tgt.sort_values("pct_of_target"), x="pct_of_target", y="employee", orientation="h", color="status",
                             color_discrete_map={"On or above target": TEAL, "Below target": RED})
                fig.add_vline(x=100, line_dash="dash", line_color="rgba(127,127,127,.9)")
                style(fig, 380, True, "% of annual target", None)
        panel(f"Progress to sales target ({yr})", fig)
    with st.expander("Tables and the SQL behind them"):
        st.dataframe(emp, hide_index=True, use_container_width=True)
        st.code(q.EMPLOYEE_PERFORMANCE, language="sql")

elif page.endswith("Revenue analysis"):
    cat = run_query(q.BY_CATEGORY, P)
    a, b = st.columns(2)
    with a:
        f = None
        if not cat.empty:
            f = px.bar(cat.melt("category", var_name="Measure", value_name="Amount"), x="category", y="Amount", color="Measure",
                       barmode="group", color_discrete_map={"revenue": BLUE, "profit": TEAL})
            style(f, 380, True, "Category", f"Amount ({CUR})")
        panel("Revenue and profit by category", f)
    with b:
        ch = run_query(q.BY_CHANNEL, P)
        panel("Revenue by sales channel", donut(ch, "channel", "revenue") if not ch.empty else None)
    panel("Revenue and profit over time", line_revenue(monthly) if not monthly.empty else None)

elif page.endswith("Product analysis"):
    a, b = st.columns([3, 2])
    with a:
        f = None
        if not prod.empty:
            f = px.treemap(prod, path=[px.Constant("All"), "category", "product"], values="revenue", color_discrete_sequence=PALETTE)
            f.update_traces(hovertemplate="%{label}<br>%{value:,.0f}<extra></extra>", marker_cornerradius=4)
            style(f, 440)
        panel("Revenue by category and product (click to zoom)", f)
    with b:
        panel("Top 10 products", hbar(prod.nlargest(10, "revenue"), "revenue", "product", BLUE, 440, f"Revenue ({CUR})") if not prod.empty else None)

elif page.endswith("Customer analysis"):
    top, seg = run_query(q.TOP_CUSTOMERS, P), run_query(q.BY_SEGMENT, P)
    a, b = st.columns([3, 2])
    with a: panel("Top 10 customers", hbar(top, "revenue", "customer", PURPLE, 420, f"Revenue ({CUR})") if not top.empty else None)
    with b: panel("Revenue by customer segment", donut(seg, "segment", "revenue") if not seg.empty else None)

elif page.endswith("Regional analysis"):
    a, b = st.columns([3, 2])
    with a:
        f = None
        if not reg.empty:
            f = px.bar(reg, x="region", y="revenue", color_discrete_sequence=[BLUE], hover_data={"orders": True})
            style(f, 400, False, "Region", f"Revenue ({CUR})")
        panel("Revenue by region", f)
    with b: panel("Regional share of revenue", donut(reg, "region", "revenue") if not reg.empty else None)

elif page.endswith("Sales trends"):
    grain = st.radio("Group by", ["Month", "Week", "Day"], horizontal=True)
    tr = run_query(q.trend({"Month": "%Y-%m", "Week": "%Y-W%W", "Day": "%Y-%m-%d"}[grain]), P)
    panel(f"Revenue and profit by {grain.lower()}", line_revenue(tr) if not tr.empty else None)
    panel(f"Sales growth by {grain.lower()}", growth_chart(tr) if not tr.empty else None)

else:
    with st.container(border=True):
        st.markdown('<div class="ptitle">Settings</div>', unsafe_allow_html=True)
        opts = ["₦", "$", "€", "£", ""]
        c = st.selectbox("Currency symbol", opts, index=opts.index(CUR) if CUR in opts else 0)
        if c != CUR:
            st.session_state["cur"] = c
            st.rerun()
        if st.button("Refresh data (clear cache)"):
            st.cache_data.clear()
            st.rerun()
    with st.container(border=True):
        st.markdown('<div class="ptitle">Order lines for the current filters</div>', unsafe_allow_html=True)
        detail = run_query(q.ORDERS_DETAIL, P)
        s = st.text_input("Search customer or product")
        if s:
            detail = detail[detail["customer"].str.contains(s, case=False) | detail["product"].str.contains(s, case=False)]
        st.dataframe(detail, hide_index=True, use_container_width=True)
        st.download_button("Download as CSV", detail.to_csv(index=False), "orders.csv", "text/csv")