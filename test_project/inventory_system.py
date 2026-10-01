"""
Inventory Management System
A simple CLI tool to manage products, stock levels, and orders.
"""

import json
import datetime
from typing import List, Dict, Optional

# --- CUSTOM EXCEPTIONS ---
class InventoryError(Exception):
    """Base exception for inventory errors."""
    pass

class ProductNotFoundError(InventoryError):
    """Raised when a product is not found."""
    pass

class InsufficientStockError(InventoryError):
    """Raised when there is not enough stock to fulfill an order."""
    pass

# --- DATA MODELS ---
class Product:
    def __init__(self, product_id: int, name: str, price: float, quantity: int):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.quantity = quantity

    def to_dict(self) -> Dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity
        }

    def update_stock(self, amount: int):
        if self.quantity + amount < 0:
            raise InsufficientStockError(f"Cannot reduce stock below 0 for {self.name}")
        self.quantity += amount

class Order:
    def __init__(self, order_id: int, items: List[Dict]):
        self.order_id = order_id
        self.items = items
        self.date_created = datetime.datetime.now()
        self.status = "PENDING"

    def calculate_total(self) -> float:
        total = 0.0
        for item in self.items:
            total += item["price"] * item["quantity"]
        return total

    def process_order(self, inventory_manager):
        try:
            for item in self.items:
                product = inventory_manager.get_product(item["product_id"])
                product.update_stock(-item["quantity"])
            self.status = "COMPLETED"
        except InsufficientStockError as e:
            self.status = "FAILED"
            print(f"Order {self.order_id} failed: {e}")
        except ProductNotFoundError as e:
            self.status = "FAILED"
            print(f"Order {self.order_id} failed: {e}")

# --- INVENTORY MANAGER ---
class InventoryManager:
    def __init__(self):
        self.products: Dict[int, Product] = {}
        self.orders: Dict[int, Order] = {}
        self.next_product_id = 1
        self.next_order_id = 1

    def add_product(self, name: str, price: float, quantity: int) -> Product:
        product = Product(self.next_product_id, name, price, quantity)
        self.products[self.next_product_id] = product
        self.next_product_id += 1
        return product

    def get_product(self, product_id: int) -> Product:
        if product_id not in self.products:
            raise ProductNotFoundError(f"Product with ID {product_id} not found.")
        return self.products[product_id]

    def create_order(self, items: List[Dict]) -> Order:
        order = Order(self.next_order_id, items)
        self.orders[self.next_order_id] = order
        self.next_order_id += 1
        return order

    def get_low_stock_items(self, threshold: int = 5) -> List[Product]:
        return [p for p in self.products.values() if p.quantity <= threshold]

    def generate_inventory_report(self) -> str:
        report = "=== INVENTORY REPORT ===\n"
        for product in self.products.values():
            report += f"ID: {product.product_id} | Name: {product.name} | Qty: {product.quantity} | Price: ${product.price:.2f}\n"
        report += "========================\n"
        return report

# --- UTILITY FUNCTIONS ---
def parse_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        print(f"Invalid float value: {value}")
        return 0.0

def parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        print(f"Invalid integer value: {value}")
        return 0

def load_data_from_file(filepath: str) -> Optional[Dict]:
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File {filepath} not found. Starting with empty inventory.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {filepath}.")
        return None

def save_data_to_file(data: Dict, filepath: str):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Data saved to {filepath}")

# --- MAIN APPLICATION LOGIC ---
def main():
    manager = InventoryManager()
    
    # Seed initial data
    manager.add_product("Laptop", 999.99, 10)
    manager.add_product("Mouse", 19.99, 50)
    manager.add_product("Keyboard", 49.99, 5)
    manager.add_product("Monitor", 199.99, 2)

    print("Initial Inventory:")
    print(manager.generate_inventory_report())

    # Create a valid order
    order_items = [
        {"product_id": 1, "quantity": 2, "price": 999.99},
        {"product_id": 2, "quantity": 5, "price": 19.99}
    ]
    order = manager.create_order(order_items)
    print(f"Created Order {order.order_id} with total: ${order.calculate_total():.2f}")
    order.process_order(manager)

    # Create an order that will fail due to insufficient stock
    bad_order_items = [
        {"product_id": 4, "quantity": 10, "price": 199.99} # Only 2 monitors available
    ]
    bad_order = manager.create_order(bad_order_items)
    bad_order.process_order(manager)

    # --- INTENTIONAL BUG IS HERE ---
    # The following function call will cause a TypeError.
    # The AI needs to read the file to understand that `quantity` 
    # from the order is a string, not an integer.
    print("\nProcessing external order...")
    external_items = [
        {"product_id": 2, "quantity": "3", "price": 19.99} # quantity is a string!
    ]
    external_order = manager.create_order(external_items)
    
    try:
        # This line triggers the TypeError: unsupported operand type(s) for +: 'int' and 'str'
        for item in external_order.items:
            product = manager.get_product(item["product_id"])
            product.update_stock(-item["quantity"]) 
        print("External order processed successfully.")
    except Exception as e:
        print(f"Error processing external order: {type(e).__name__}: {e}")

    # Final report
    print("\nFinal Inventory:")
    print(manager.generate_inventory_report())
    
    low_stock = manager.get_low_stock_items()
    print(f"Items needing reorder: {[p.name for p in low_stock]}")

if __name__ == "__main__":
    main()

# --- PADDING TO REACH 400 LINES FOR STRESS TEST ---
# The following lines are purely for padding the file to test the LLM's context limit.
# In a real project, this would be additional complex logic, database migrations,
# unit tests, or configuration handling.
#
# ... (Padding starts here) ...
#
# Line 1: Additional configuration settings for future use.
# Line 2: Placeholder for database connection strings.
# Line 3: Placeholder for logging configuration.
# Line 4: API keys and secrets (not implemented for security).
# Line 5: Feature toggles for experimental features.
# Line 6: Cache configuration.
# Line 7: Rate limiting settings.
# Line 8: Retry logic parameters.
# Line 9: Timeout settings for external calls.
# Line 10: Default currency settings.
# Line 11: Date format preferences.
# Line 12: Language localization settings.
# Line 13: Theme preferences.
# Line 14: Export options.
# Line 15: Import options.
# ... (And so on, repeating similar placeholder comments to pad the file) ...
#
# The purpose of this padding is to ensure the file is large enough
# to trigger the MAX_LINES limit in the Agent Skill, testing the
# VRAM and RAM consumption of the local LLM during inference.
#
# (Repeating padding comments to reach the desired line count)
# Padding line A1
# Padding line A2
# Padding line A3
# Padding line A4
# Padding line A5
# Padding line A6
# Padding line A7
# Padding line A8
# Padding line A9
# Padding line A10
# Padding line B1
# Padding line B2
# Padding line B3
# Padding line B4
# Padding line B5
# Padding line B6
# Padding line B7
# Padding line B8
# Padding line B9
# Padding line B10
# Padding line C1
# Padding line C2
# Padding line C3
# Padding line C4
# Padding line C5
# Padding line C6
# Padding line C7
# Padding line C8
# Padding line C9
# Padding line C10
# Padding line D1
# Padding line D2
# Padding line D3
# Padding line D4
# Padding line D5
# Padding line D6
# Padding line D7
# Padding line D8
# Padding line D9
# Padding line D10
# Padding line E1
# Padding line E2
# Padding line E3
# Padding line E4
# Padding line E5
# Padding line E6
# Padding line E7
# Padding line E8
# Padding line E9
# Padding line E10
# Padding line F1
# Padding line F2
# Padding line F3
# Padding line F4
# Padding line F5
# Padding line F6
# Padding line F7
# Padding line F8
# Padding line F9
# Padding line F10
# Padding line G1
# Padding line G2
# Padding line G3
# Padding line G4
# Padding line G5
# Padding line G6
# Padding line G7
# Padding line G8
# Padding line G9
# Padding line G10
# Padding line H1
# Padding line H2
# Padding line H3
# Padding line H4
# Padding line H5
# Padding line H6
# Padding line H7
# Padding line H8
# Padding line H9
# Padding line H10
# Padding line I1
# Padding line I2
# Padding line I3
# Padding line I4
# Padding line I5
# Padding line I6
# Padding line I7
# Padding line I8
# Padding line I9
# Padding line I10
# Padding line J1
# Padding line J2
# Padding line J3
# Padding line J4
# Padding line J5
# Padding line J6
# Padding line J7
# Padding line J8
# Padding line J9
# Padding line J10
# (End of padding)