import uuid
from datetime import datetime
from models import Customer, Bill, BillItem
from services import SERVICES, display_services
from storage import (save_customer, get_customer, get_all_customers,
                     find_customer_by_phone, save_bill, get_bills_by_date)
from reports import print_bill, print_daily_report

def input_str(prompt):
    return input(prompt).strip()

def generate_id(prefix=""):
    return prefix + str(uuid.uuid4())[:8].upper()

# ── Customer Management ──────────────────────────────────────────────────────

def add_customer():
    print("\n── Add New Customer ──")
    name = input_str("Name: ")
    phone = input_str("Phone: ")
    if find_customer_by_phone(phone):
        print("⚠  Customer with this phone already exists.")
        return
    customer = Customer(generate_id("C"), name, phone)
    save_customer(customer)
    print(f"✔  Customer added. ID: {customer.customer_id}")

def view_customers():
    customers = get_all_customers()
    if not customers:
        print("No customers found.")
        return
    print(f"\n{'ID':<12} {'Name':<20} {'Phone':<15} {'Visits'}")
    print("-" * 55)
    for c in customers:
        print(f"{c.customer_id:<12} {c.name:<20} {c.phone:<15} {len(c.visit_history)}")

def view_customer_history():
    cid = input_str("Enter Customer ID or Phone: ")
    customer = get_customer(cid) or find_customer_by_phone(cid)
    if not customer:
        print("Customer not found.")
        return
    print(f"\nVisit History for {customer.name}:")
    if not customer.visit_history:
        print("  No visits recorded.")
        return
    for v in customer.visit_history:
        print(f"  [{v['date']}] Bill #{v['bill_id']} — ₹{v['total']:.2f} ({v['payment_method']})")

# ── Billing ──────────────────────────────────────────────────────────────────

def create_bill():
    print("\n── New Bill ──")
    cid = input_str("Customer ID or Phone (leave blank to add new): ")

    if cid:
        customer = get_customer(cid) or find_customer_by_phone(cid)
        if not customer:
            print("Customer not found.")
            return
    else:
        name = input_str("Customer Name: ")
        phone = input_str("Phone: ")
        customer = find_customer_by_phone(phone)
        if not customer:
            customer = Customer(generate_id("C"), name, phone)
            save_customer(customer)

    display_services()
    items = []
    while True:
        sid = input_str("Enter Service ID (or 'done' to finish): ")
        if sid.lower() == "done":
            break
        if sid not in SERVICES:
            print("Invalid service ID.")
            continue
        try:
            qty = int(input_str("Quantity [1]: ") or "1")
        except ValueError:
            qty = 1
        items.append(BillItem(SERVICES[sid], qty))

    if not items:
        print("No services selected. Bill cancelled.")
        return

    try:
        discount = float(input_str("Discount % [0]: ") or "0")
    except ValueError:
        discount = 0.0

    print("Payment Method: 1) Cash  2) Card  3) UPI")
    pm_map = {"1": "Cash", "2": "Card", "3": "UPI"}
    pm = pm_map.get(input_str("Choose [1]: ") or "1", "Cash")

    bill = Bill(generate_id("B"), customer, items, pm, discount=discount)
    print_bill(bill)
    save_bill(bill)

    customer.visit_history.append({
        "bill_id": bill.bill_id,
        "date": bill.date.strftime("%d-%m-%Y"),
        "total": bill.total,
        "payment_method": pm
    })
    save_customer(customer)
    print("✔  Bill saved successfully.")

# ── Reports ──────────────────────────────────────────────────────────────────

def daily_report():
    date_str = input_str("Enter date (YYYY-MM-DD) [today]: ") or datetime.now().strftime("%Y-%m-%d")
    bills = get_bills_by_date(date_str)
    if not bills:
        print(f"No bills found for {date_str}.")
        return
    print_daily_report(date_str, bills)

# ── Main Menu ────────────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════╗
║   GLAMOUR BEAUTY PARLOUR — BILLING   ║
╠══════════════════════════════════════╣
║  1. New Bill                         ║
║  2. Add Customer                     ║
║  3. View All Customers               ║
║  4. Customer Visit History           ║
║  5. Daily Sales Report               ║
║  0. Exit                             ║
╚══════════════════════════════════════╝
"""

def main():
    actions = {
        "1": create_bill,
        "2": add_customer,
        "3": view_customers,
        "4": view_customer_history,
        "5": daily_report,
    }
    while True:
        print(MENU)
        choice = input_str("Select option: ")
        if choice == "0":
            print("Goodbye! 👋")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()
