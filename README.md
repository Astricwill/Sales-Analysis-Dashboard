# BrightMart Sales Analytics Dashboard

An interactive business intelligence dashboard built with **SQL, Python (Pandas), Plotly and Streamlit**, running on a relational retail database (BrightMart). It turns raw sales data into answers: how much revenue and profit is coming in, which customers, products and categories drive it, how each channel, region and employee performs, and who is on track for their sales targets.

## Business questions this dashboard answers

**Overview: is the business healthy?**

- How much revenue are we making, and is it growing or shrinking compared to the previous period?
- Are we selling more units, getting more orders, or just earning more per order?
- Are we gaining customers, and what is the average order worth?

**Revenue analysis: where does the money come from?**

- Which product categories earn the most revenue, and which earn the most profit?
- Which sales channel (Online, In-Store, Partner) brings in the most revenue?
- Is profit growing as fast as revenue, or are discounts and costs eating into it?

**Product analysis: what should we stock and promote?**

- What are the top 10 products, and how much revenue depends on them?
- Which categories dominate, and which products inside them drive that?
- Which products are declining and need a review of pricing, stock or promotion?

**Customer analysis: who are our best customers?**

- Who are the top 10 customers, and how much revenue do they bring in?
- Which customer segment (Retail, Corporate, SME) is the most valuable?
- Are we too dependent on a few customers?

**Regional analysis: where do we perform well?**

- Which region generates the most revenue?
- Which regions are underperforming and need attention?

**Sales performance: how is the team doing?**

- Which employees bring in the most revenue and orders?
- Who is on track to hit their sales target, and who is behind?
- Does performance differ by department or region?

**Sales trends: when do sales rise and fall?**

- Which month had the highest sales, and is there a seasonal pattern?
- When did revenue grow or drop month to month?

### Using the filters (date range, region, channel) to ask sharper questions

- Does the Online channel perform better than In-Store in a particular region?
- Did sales change in the last quarter compared to the one before?

## Features

- **Sidebar navigation** with eight pages: Overview, Sales performance, Revenue analysis, Product analysis, Customer analysis, Regional analysis, Sales trends, Settings
- **KPI cards** with change versus the previous period: revenue, units sold, orders, average order value, customers, sales growth
- **Interactive Plotly charts:** revenue and profit trends, monthly units sold, category, channel and segment donuts, product treemap, top products and customers, regional charts, growth rates
- **Automatically generated insights:** best product, top region, strongest month, latest month trend, declining products, and a data-driven recommendation
- **Sales target tracking:** actual revenue versus target for each employee, by year
- **Employee performance table** with orders, revenue and average order value
- **Filters** for date range, region and channel that apply to every page
- **SQL on display:** an expander showing the query behind the employee performance table
- **Searchable order table** with CSV download, and a currency setting, on the Settings page
- Works in light and dark mode, and adapts to laptop and tablet screens

## Tech stack

Python, SQL (SQLite), Pandas, Plotly, Streamlit

## Project structure

```text
Sales_Analytics_Dashboard/
├── app.py                 # Streamlit dashboard (layout, styling, charts, insights)
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml        # Theme settings
├── src/
│   ├── __init__.py
│   ├── queries.py         # All SQL queries
│   └── load_sql.py        # Builds data/sales.db from the .sql script
└── data/
    ├── brightmart_db.sql  # Database script
    └── sales.db           # SQLite database used by the app
```

## Database design

Seven tables: `departments`, `employees`, `customers`, `products`, `orders`, `order_items`, `sales_targets`.

- Orders link to customers and employees; `order_items` link orders to products.
- Revenue = `quantity * unit_price * (1 - discount)` for completed orders.
- Profit = revenue minus `quantity * unit_cost`.

## Run it locally

Run all commands from the project's main folder.

```bash
pip install -r requirements.txt
python src/load_sql.py                  # builds data/sales.db
streamlit run app.py
```

`load_sql.py` finds the `.sql` script inside the `data` folder. To name it yourself, run `python src/load_sql.py data/brightmart_db.sql`.

## Live demo

<https://sales-analysis-dashboard-5vv6k5pkdt3kgpdzm6tkqt.streamlit.app>
