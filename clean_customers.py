import pandas as pd

# Load raw customer data
customers = pd.read_csv("data/raw/customers.csv")

# Make a copy
clean = customers.copy()

# Standardize city names
clean["city"] = clean["city"].str.strip().str.title()

# Standardize gender
clean["gender"] = clean["gender"].str.strip().str.lower()
clean["gender"] = clean["gender"].replace({
    "f": "female",
    "m": "male"
})

# Replace blank gender with unknown
clean["gender"] = clean["gender"].replace("", "unknown")
clean["gender"] = clean["gender"].fillna("unknown")

# Handle invalid ages
clean["age"] = clean["age"].where(
    clean["age"].between(10, 100)
)

# Fill missing ages with median age
clean["age"] = clean["age"].fillna(clean["age"].median())

# Check results
print("Missing ages:", clean["age"].isnull().sum())
print("Missing genders:", clean["gender"].isnull().sum())
print("\nGender counts:")
print(clean["gender"].value_counts())

print("\nAge range:")
print(clean["age"].min(), clean["age"].max())
print("\nCity counts:")
print(clean["city"].value_counts())
# Save cleaned customer data
clean.to_csv("data/clean/customers.csv", index=False)

print("\nCleaned customer dataset saved successfully!")
print("Final shape:", clean.shape)