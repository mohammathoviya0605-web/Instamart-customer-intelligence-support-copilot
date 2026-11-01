import sqlite3
from datetime import datetime, timedelta

connection = sqlite3.connect("data/instamart.db")

order_id = "ORD-100048"

row = connection.execute(
    "SELECT order_id, order_ts, delivery_minutes FROM orders WHERE order_id = ?",
    (order_id,)
).fetchone()

print("Order details:", row)

order_time = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
delivery_time = order_time + timedelta(minutes=row[2])

print("Order time:", order_time)
print("Estimated delivery time:", delivery_time)
print("Example request date:", delivery_time + timedelta(days=1))

connection.close()