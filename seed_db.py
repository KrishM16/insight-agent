import sqlite3, random, datetime as dt

con = sqlite3.connect("retail.db")
c = con.cursor()
c.executescript("""
DROP TABLE IF EXISTS customers; DROP TABLE IF EXISTS orders; DROP TABLE IF EXISTS products;
CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT, region TEXT, signup_date TEXT, segment TEXT);
CREATE TABLE products  (product_id INTEGER PRIMARY KEY, name TEXT, category TEXT, unit_price REAL);
CREATE TABLE orders    (order_id INTEGER PRIMARY KEY, customer_id INT, product_id INT, quantity INT, order_date TEXT, status TEXT);
""")

regions  = ["West", "East", "South", "Midwest"]
segments = ["SMB", "Mid Market", "Enterprise"]
cats     = ["Electronics", "Apparel", "Home", "Grocery"]

for i in range(1, 501):
    c.execute("INSERT INTO customers VALUES (?,?,?,?,?)", (
        i, f"Customer {i}", random.choice(regions),
        (dt.date(2023,1,1) + dt.timedelta(days=random.randint(0,700))).isoformat(),
        random.choice(segments)))

for i in range(1, 61):
    c.execute("INSERT INTO products VALUES (?,?,?,?)", (
        i, f"Product {i}", random.choice(cats), round(random.uniform(5, 900), 2)))

for i in range(1, 8001):
    c.execute("INSERT INTO orders VALUES (?,?,?,?,?,?)", (
        i, random.randint(1,500), random.randint(1,60), random.randint(1,6),
        (dt.date(2024,1,1) + dt.timedelta(days=random.randint(0,600))).isoformat(),
        random.choices(["completed","returned","cancelled"], weights=[85,10,5])[0]))

con.commit(); con.close()
print("retail.db created")