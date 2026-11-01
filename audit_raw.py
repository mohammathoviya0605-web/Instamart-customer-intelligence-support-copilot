import pandas as pd

tickets = pd.read_csv(
    "data/raw/tickets.csv",
    keep_default_na=False
)

print("TICKETS DATA AUDIT")
print("------------------")

print("\nShape:")
print(tickets.shape)

print("\nColumns:")
print(tickets.columns.tolist())

print("\nData Types:")
print(tickets.dtypes)

print("\nMissing Values:")
print(tickets.isnull().sum())

print("\nBlank Values:")
print((tickets == "").sum())

print("\nMissing Percentage:")
print((tickets.isnull().mean() * 100).round(2))