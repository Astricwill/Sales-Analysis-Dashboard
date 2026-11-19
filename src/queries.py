"""All SQL for the BrightMart dashboard lives here.
Every query uses the sidebar filters: :start, :end, :region, :channel ('All' = no filter)."""

# Revenue after discount. IMPORTANT: this assumes discount_pct holds whole percents (e.g. 10.00 = 10%).
# If your data holds fractions (0.10 = 10%), change "/ 100.0" to "" in both lines below.
# Check with:  SELECT MAX(discount_pct) FROM order_items;   (max <= 1 means fractions)
REVENUE = "oi.quantity * p.unit_price * (1 - oi.discount_pct / 100.0)"
PROFIT = "oi.quantity * (p.unit_price * (1 - oi.discount_pct / 100.0) - p.unit_cost)"

FROM_JOINS = """
FROM orders o
JOIN order_items oi  ON oi.order_id = o.order_id
JOIN products p      ON p.product_id = oi.product_id
LEFT JOIN employees e ON e.employee_id = o.employee_id
"""

FILTER = """
    o.status = 'Completed'
    AND o.order_date BETWEEN :start AND :end
    AND (:region = 'All' OR e.region = :region)
    AND (:channel = 'All' OR o.channel = :channel)
"""

DATE_BOUNDS = "SELECT MIN(order_date) AS first_date, MAX(order_date) AS last_date FROM orders"
REGIONS = "SELECT DISTINCT region FROM employees WHERE region IS NOT NULL ORDER BY region"
CHANNELS = "SELECT DISTINCT channel FROM orders WHERE channel IS NOT NULL ORDER BY channel"
YEARS = "SELECT DISTINCT year FROM sales_targets ORDER BY year DESC"

KPIS = f"""
SELECT ROUND(SUM({REVENUE}), 2) AS revenue,
       ROUND(SUM({PROFIT}), 2)  AS profit,
       SUM(oi.quantity)              AS units,
       COUNT(DISTINCT o.order_id)    AS orders,
       COUNT(DISTINCT o.customer_id) AS customers
{FROM_JOINS}
WHERE {FILTER}
"""

# Share of orders that were returned (all statuses, same date/region/channel filters)
RETURN_RATE = """
SELECT ROUND(100.0 * SUM(CASE WHEN o.status = 'Returned' THEN 1 ELSE 0 END) / COUNT(*), 1) AS return_rate
FROM orders o
LEFT JOIN employees e ON e.employee_id = o.employee_id
WHERE o.order_date BETWEEN :start AND :end
  AND (:region = 'All' OR e.region = :region)
  AND (:channel = 'All' OR o.channel = :channel)
"""

MONTHLY = f"""
SELECT strftime('%Y-%m', o.order_date) AS month,
       ROUND(SUM({REVENUE}), 2) AS revenue,
       ROUND(SUM({PROFIT}), 2)  AS profit
{FROM_JOINS}
WHERE {FILTER}
GROUP BY month
ORDER BY month
"""

BY_CATEGORY = f"""
SELECT p.category,
       ROUND(SUM({REVENUE}), 2) AS revenue,
       ROUND(SUM({PROFIT}), 2)  AS profit
{FROM_JOINS}
WHERE {FILTER}
GROUP BY p.category
ORDER BY revenue DESC
"""

BY_CHANNEL = f"""
SELECT o.channel,
       ROUND(SUM({REVENUE}), 2) AS revenue
{FROM_JOINS}
WHERE {FILTER}
GROUP BY o.channel
ORDER BY revenue DESC
"""

TOP_CUSTOMERS = f"""
SELECT c.customer_name AS customer,
       ROUND(SUM({REVENUE}), 2) AS revenue
{FROM_JOINS}
JOIN customers c ON c.customer_id = o.customer_id
WHERE {FILTER}
GROUP BY c.customer_id
ORDER BY revenue DESC
LIMIT 10
"""

BY_SEGMENT = f"""
SELECT c.segment,
       ROUND(SUM({REVENUE}), 2) AS revenue
{FROM_JOINS}
JOIN customers c ON c.customer_id = o.customer_id
WHERE {FILTER}
GROUP BY c.segment
ORDER BY revenue DESC
"""

EMPLOYEE_PERFORMANCE = f"""
SELECT e.first_name || ' ' || e.last_name AS employee,
       d.department_name AS department,
       e.region,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM({REVENUE}), 2) AS revenue,
       ROUND(SUM({REVENUE}) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p     ON p.product_id = oi.product_id
JOIN employees e    ON e.employee_id = o.employee_id
LEFT JOIN departments d ON d.department_id = e.department_id
WHERE {FILTER}
GROUP BY e.employee_id
ORDER BY revenue DESC
"""

# Actual revenue vs sales target for one year (year filter is separate from the date range)
TARGET_ATTAINMENT = f"""
WITH actual AS (
    SELECT o.employee_id, SUM({REVENUE}) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p     ON p.product_id = oi.product_id
    WHERE o.status = 'Completed'
      AND CAST(strftime('%Y', o.order_date) AS INTEGER) = :year
    GROUP BY o.employee_id
),
tgt AS (
    SELECT employee_id, SUM(target_amount) AS target
    FROM sales_targets
    WHERE year = :year
    GROUP BY employee_id
)
SELECT e.first_name || ' ' || e.last_name AS employee,
       e.region,
       t.target AS target,
       ROUND(COALESCE(a.revenue, 0), 0) AS actual,
       ROUND(100.0 * COALESCE(a.revenue, 0) / NULLIF(t.target, 0), 1) AS pct_of_target
FROM employees e
JOIN tgt t ON t.employee_id = e.employee_id
LEFT JOIN actual a ON a.employee_id = e.employee_id
WHERE (:region = 'All' OR e.region = :region)
ORDER BY pct_of_target DESC
"""


def trend(fmt: str = "%Y-%m") -> str:
    """Revenue and profit over time. fmt: '%Y-%m' (month), '%Y-W%W' (week), '%Y-%m-%d' (day)."""
    return f"""
SELECT strftime('{fmt}', o.order_date) AS period,
       ROUND(SUM({REVENUE}), 2) AS revenue,
       ROUND(SUM({PROFIT}), 2)  AS profit,
       SUM(oi.quantity) AS units,
       COUNT(DISTINCT o.order_id) AS orders
{FROM_JOINS}
WHERE {FILTER}
GROUP BY period
ORDER BY period
"""

BY_PRODUCT = f"""
SELECT p.category, p.product_name AS product,
       ROUND(SUM({REVENUE}), 2) AS revenue
{FROM_JOINS}
WHERE {FILTER}
GROUP BY p.product_id
HAVING revenue > 0
"""

ORDERS_DETAIL = f"""
SELECT o.order_id, o.order_date, c.customer_name AS customer, o.channel,
       p.category, p.product_name AS product, oi.quantity,
       ROUND({REVENUE}, 2) AS revenue
{FROM_JOINS}
JOIN customers c ON c.customer_id = o.customer_id
WHERE {FILTER}
ORDER BY o.order_date DESC
LIMIT 2000
"""


BY_REGION = f"""
SELECT COALESCE(e.region, 'Unassigned') AS region,
       ROUND(SUM({REVENUE}), 2) AS revenue,
       COUNT(DISTINCT o.order_id) AS orders
{FROM_JOINS}
WHERE {FILTER}
GROUP BY region
ORDER BY revenue DESC
"""

PRODUCT_MONTHLY = f"""
SELECT strftime('%Y-%m', o.order_date) AS month, p.product_name AS product,
       ROUND(SUM({REVENUE}), 2) AS revenue
{FROM_JOINS}
WHERE {FILTER}
GROUP BY month, p.product_id
"""