import pandas as pd

# Load raw orders
orders = pd.read_csv("data/raw/orders.csv")

# Make a copy
clean = orders.copy()

# Check original row count
print("Original rows:", len(clean))

# Remove exact duplicate rows
clean = clean.drop_duplicates()

print("Rows after removing duplicates:", len(clean))

# Check remaining duplicates
print("Remaining exact duplicates:", clean.duplicated().sum())
# Remove pending orders
clean = clean[clean["status"].str.lower() != "pending"]

print("Rows after removing pending orders:", len(clean))

print("Remaining pending orders:",
      (clean["status"].str.lower() == "pending").sum())
# Convert order_amount to numeric
clean["order_amount"] = pd.to_numeric(
    clean["order_amount"],
    errors="coerce"
)

print("Invalid order amounts:",
      clean["order_amount"].isna().sum())
# Display invalid order amount rows
print("\nInvalid order amount rows:")
print(clean[clean["order_amount"].isna()].head(10))
# Load product catalogue
products = pd.read_csv("data/raw/products.csv")

# Check product catalogue columns
print("\nProduct catalogue columns:")
print(products.columns.tolist())

# Check orders with invalid amounts
print("\nOrders with invalid amounts:")
print(
    clean.loc[
        clean["order_amount"].isna(),
        ["order_id", "product_id", "order_amount"]
    ].head()
)