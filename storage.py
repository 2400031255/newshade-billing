import json
import os
from models import Customer, Bill, BillItem, Service
from datetime import datetime

CUSTOMERS_FILE = "data/customers.json"
BILLS_FILE = "data/bills.json"
SERVICES_FILE = "data/services.json"

def _ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def _read_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        return json.load(f)

def _write_json(filepath, data):
    _ensure_data_dir()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

# --- Customer Storage ---

def save_customer(customer: Customer):
    data = _read_json(CUSTOMERS_FILE)
    data[customer.customer_id] = {
        "name": customer.name,
        "phone": customer.phone,
        "visit_history": customer.visit_history
    }
    _write_json(CUSTOMERS_FILE, data)

def get_customer(customer_id: str):
    data = _read_json(CUSTOMERS_FILE)
    if customer_id not in data:
        return None
    c = data[customer_id]
    return Customer(customer_id, c["name"], c["phone"], c.get("visit_history", []))

def get_all_customers():
    data = _read_json(CUSTOMERS_FILE)
    return [Customer(cid, c["name"], c["phone"], c.get("visit_history", [])) for cid, c in data.items()]

def find_customer_by_phone(phone: str):
    for c in get_all_customers():
        if c.phone == phone:
            return c
    return None

def delete_customer_visit(customer_id: str, bill_id: str):
    customer = get_customer(customer_id)
    if not customer:
        return
    customer.visit_history = [v for v in customer.visit_history if v["bill_id"] != bill_id]
    save_customer(customer)

# --- Bill Storage ---

def save_bill(bill: Bill):
    data = _read_json(BILLS_FILE)
    data[bill.bill_id] = {
        "customer_id": bill.customer.customer_id,
        "items": [{"service_name": i.service.name, "service_price": i.service.price, "quantity": i.quantity} for i in bill.items],
        "payment_method": bill.payment_method,
        "date": bill.date.isoformat(),
        "discount": bill.discount,
        "total": bill.total
    }
    _write_json(BILLS_FILE, data)

def get_all_bills():
    return _read_json(BILLS_FILE)

def get_bills_by_date(date_str: str):
    all_bills = get_all_bills()
    return {bid: b for bid, b in all_bills.items() if b["date"].startswith(date_str)}

# --- Services Storage ---

def load_services():
    return _read_json(SERVICES_FILE)

def save_services(services: dict):
    _write_json(SERVICES_FILE, services)

def delete_service(sid: str):
    data = load_services()
    data.pop(sid, None)
    save_services(data)
