import pandas as pd

data = {
    "customer": ["Arun", "Meena", "Ravi", "Meena"],
    "city": ["Chennai", "Pune", "Chennai", "Pune"],
    "amount": [500, 800, None, 800]
}

df = pd.DataFrame(data)

print("Shape:", df.shape)
print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())