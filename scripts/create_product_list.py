import pandas as pd
import os

print("--- Starting: Creating Final Curated 'Hero' Product List ---")

# --- Configuration ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(project_root, "data/raw")
OFFICIAL_PRODUCTS_FILE = os.path.join(RAW_DATA_DIR, "cool_gadgets_products.csv")

# --- The Final, Hand-Picked "Hero" Product List ---
# This list is focused on major, exciting product categories.
curated_products = {
    'id': [101, 102, 103, 104, 105, 106, 107],
    'title': [
        'iPhone 16 Pro',                                        # New Smartphone
        'Samsung Galaxy S25 Ultra',                             # New Smartphone
        'Sony WH-1000XM5 Wireless Noise Cancelling Headphones', # Audio
        'Bose QuietComfort Ultra Headphones',                   # Audio
        'Razer Blade 16 Gaming Laptop',                         # Laptops
        'GoPro HERO12 Black Action Camera',                     # Cameras
        'Playstation 5 Pro'                                     # Gaming Consoles (current buzz)
    ],
    'category': [
        'Smartphones', 'Smartphones', 'Audio', 'Audio', 'Laptops', 'Cameras', 'Gaming Consoles'
    ]
}

# Create the DataFrame from our final curated list
new_products_df = pd.DataFrame(curated_products)

# --- Save this as our new official product list ---
new_products_df.to_csv(OFFICIAL_PRODUCTS_FILE, index=False)

print("\n--- SUCCESS! ---")
print("'cool_gadgets_products.csv' has been created with the product list.")
print("The final products are:")
print(new_products_df)