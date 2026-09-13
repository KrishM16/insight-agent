"""Harder cases: multi-hop joins, windowed time logic, ratio denominators,
ambiguity, and unanswerable questions."""

HARD = [
    ("Which product category has the highest return rate by order count?",
     "SELECT p.category, ROUND(100.0*SUM(CASE WHEN o.status='returned' THEN 1 ELSE 0 END)/COUNT(*),2) r "
     "FROM orders o JOIN products p USING(product_id) GROUP BY p.category ORDER BY r DESC LIMIT 1"),

    ("What was completed-order revenue in the second half of 2025?",
     "SELECT ROUND(SUM(o.quantity*p.unit_price),2) FROM orders o JOIN products p USING(product_id) "
     "WHERE o.status='completed' AND o.order_date BETWEEN '2025-07-01' AND '2025-12-31'"),

    ("How many customers have never placed an order?",
     "SELECT COUNT(*) FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id=c.customer_id)"),

    ("Which month in 2025 had the highest number of completed orders?",
     "SELECT substr(order_date,1,7) m, COUNT(*) c FROM orders WHERE status='completed' "
     "AND order_date LIKE '2025%' GROUP BY m ORDER BY c DESC LIMIT 1"),

    ("What is the average revenue per completed order for Enterprise customers?",
     "SELECT ROUND(SUM(o.quantity*p.unit_price)/COUNT(DISTINCT o.order_id),2) "
     "FROM orders o JOIN customers c USING(customer_id) JOIN products p USING(product_id) "
     "WHERE o.status='completed' AND c.segment='Enterprise'"),

    ("Which three products generated the most completed revenue?",
     "SELECT p.name, ROUND(SUM(o.quantity*p.unit_price),2) r FROM orders o JOIN products p USING(product_id) "
     "WHERE o.status='completed' GROUP BY p.name ORDER BY r DESC LIMIT 3"),

    ("How many customers placed more than five completed orders?",
     "SELECT COUNT(*) FROM (SELECT customer_id FROM orders WHERE status='completed' "
     "GROUP BY customer_id HAVING COUNT(*)>5)"),

    ("For each region, what share of its orders were returned?",
     "SELECT c.region, ROUND(100.0*SUM(CASE WHEN o.status='returned' THEN 1 ELSE 0 END)/COUNT(*),2) r "
     "FROM orders o JOIN customers c USING(customer_id) GROUP BY c.region"),

    ("Which region has the highest revenue per customer, counting only customers who ordered?",
     "SELECT c.region, ROUND(SUM(o.quantity*p.unit_price)/COUNT(DISTINCT c.customer_id),2) r "
     "FROM orders o JOIN customers c USING(customer_id) JOIN products p USING(product_id) "
     "WHERE o.status='completed' GROUP BY c.region ORDER BY r DESC LIMIT 1"),

    ("How many orders came from customers who signed up in the same calendar year as the order?",
     "SELECT COUNT(*) FROM orders o JOIN customers c USING(customer_id) "
     "WHERE substr(o.order_date,1,4)=substr(c.signup_date,1,4)"),
]

# Questions the schema genuinely cannot answer. Correct behaviour is to refuse,
# not to invent a column. Scored separately.
UNANSWERABLE = [
    "What is our customer satisfaction score by region?",
    "Which marketing channel drove the most signups?",
    "What is the profit margin on each product?",
]
