
from src.refund_agent import get_order

order_id = "ORD-100048"

# Request made one day after delivery
valid_result = get_order(
    order_id,
    request_date="2025-04-03T23:44:44"
)

# Request made nine days after delivery
invalid_result = get_order(
    order_id,
    request_date="2025-04-11T23:44:44"
)

print("Within 7 days:")
print(valid_result)

print("\nOutside 7 days:")
print(invalid_result)
