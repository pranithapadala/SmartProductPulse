# scripts/create_product_list.py
import pandas as pd
import os

print("--- Creating Master Product List for 'Cool Gadgets' ---")

# This is our master list. You can add or remove products here anytime.
gadgets_data = [
    {'id': 101, 'title': "Apple Vision Pro", 'category': "Mixed Reality"},
    {'id': 102, 'title': "iPhone 16 Pro", 'category': "Smartphones"},
    {'id': 103, 'title': "Samsung Galaxy S25 Ultra", 'category': "Smartphones"},
    {'id': 104, 'title': "AirPods Pro 3", 'category': "Audio"},
    {'id': 105, 'title': "Razer Blade 16 Gaming Laptop", 'category': "Laptops"},
    {'id': 106, 'title': "Playstation 6", 'category': "Gaming Consoles"},
    {'id': 107, 'title': "Nintendo Switch 2", 'category': "Gaming Consoles"}
]

# Convert our list of gadgets into a DataFrame
products_df = pd.DataFrame(gadgets_data)

# Define where to save the file
OUTPUT_DIR = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True) # This creates the folder if it doesn't exist
output_path = os.path.join(OUTPUT_DIR, "cool_gadgets_products.csv")

# Save the DataFrame to a CSV file
products_df.to_csv(output_path, index=False)

print(f"Success: Saved {len(products_df)} products to '{output_path}'")
print("\n--- Master Product List Creation Complete ---")