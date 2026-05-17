import json, os
from models import Customer, Bill, BillItem, Service
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_render_data = os.environ.get("RENDER_DATA_DIR")
DATA_DIR = _render_data if (_render_data and os.access(os.path.dirname(_render_data) or '/', os.W_OK)) else os.path.join(BASE_DIR, "data")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
BILLS_FILE     = os.path.join(DATA_DIR, "bills.json")
SERVICES_FILE  = os.path.join(DATA_DIR, "services.json")

# ── MongoDB setup (disabled due to SSL issues on Python 3.14) ───────────────
MONGO_URI = None  # Disabled - using JSON file storage
_db = None

def _get_db():
    return None

def _use_mongo():
    return False

# ── JSON helpers (local fallback) ────────────────────────────────────────────

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _read_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {}
    return data

def _write_json(filepath, data):
    _ensure_data_dir()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ── Customer Storage ─────────────────────────────────────────────────────────

def save_customer(customer: Customer):
    if _use_mongo():
        _get_db().customers.replace_one(
            {"_id": customer.customer_id},
            {"_id": customer.customer_id, "name": customer.name,
             "phone": customer.phone, "visit_history": customer.visit_history},
            upsert=True)
    else:
        data = _read_json(CUSTOMERS_FILE)
        data[customer.customer_id] = {"name": customer.name, "phone": customer.phone, "visit_history": customer.visit_history}
        _write_json(CUSTOMERS_FILE, data)

def get_customer(customer_id: str):
    if _use_mongo():
        c = _get_db().customers.find_one({"_id": customer_id})
        if not c: return None
        return Customer(customer_id, c["name"], c["phone"], c.get("visit_history", []))
    data = _read_json(CUSTOMERS_FILE)
    if customer_id not in data: return None
    c = data[customer_id]
    return Customer(customer_id, c["name"], c["phone"], c.get("visit_history", []))

def get_all_customers():
    if _use_mongo():
        return [Customer(c["_id"], c["name"], c["phone"], c.get("visit_history", [])) for c in _get_db().customers.find()]
    data = _read_json(CUSTOMERS_FILE)
    return [Customer(cid, c["name"], c["phone"], c.get("visit_history", [])) for cid, c in data.items()]

def find_customer_by_phone(phone: str):
    if _use_mongo():
        c = _get_db().customers.find_one({"phone": phone})
        if not c: return None
        return Customer(c["_id"], c["name"], c["phone"], c.get("visit_history", []))
    for c in get_all_customers():
        if c.phone == phone: return c
    return None

def delete_customer_visit(customer_id: str, bill_id: str):
    customer = get_customer(customer_id)
    if not customer: return
    customer.visit_history = [v for v in customer.visit_history if v["bill_id"] != bill_id]
    save_customer(customer)

# ── Bill Storage ─────────────────────────────────────────────────────────────

def save_bill(bill: Bill):
    doc = {
        "customer_id": bill.customer.customer_id,
        "items": [{"service_name": i.service.name, "service_price": i.service.price, "quantity": i.quantity} for i in bill.items],
        "payment_method": bill.payment_method,
        "date": bill.date.isoformat(),
        "discount": bill.discount,
        "total": bill.total
    }
    if _use_mongo():
        _get_db().bills.replace_one({"_id": bill.bill_id}, {"_id": bill.bill_id, **doc}, upsert=True)
    else:
        data = _read_json(BILLS_FILE)
        data[bill.bill_id] = doc
        _write_json(BILLS_FILE, data)

def get_all_bills():
    if _use_mongo():
        return {b["_id"]: {k: v for k, v in b.items() if k != "_id"} for b in _get_db().bills.find()}
    return _read_json(BILLS_FILE)

def get_bills_by_date(date_str: str):
    return {bid: b for bid, b in get_all_bills().items() if b["date"].startswith(date_str)}

# ── Services Storage ─────────────────────────────────────────────────────────

def load_services():
    if _use_mongo():
        doc = _get_db().services.find_one({"_id": "catalog"})
        return doc["data"] if doc else {}
    return _read_json(SERVICES_FILE)

def save_services(services: dict):
    if _use_mongo():
        _get_db().services.replace_one({"_id": "catalog"}, {"_id": "catalog", "data": services}, upsert=True)
    else:
        _write_json(SERVICES_FILE, services)

def delete_service(sid: str):
    data = load_services()
    data.pop(sid, None)
    save_services(data)

# ── Admin Storage ─────────────────────────────────────────────────────────────

ADMIN_FILE = os.path.join(DATA_DIR, "admin.json")

def get_admin():
    if _use_mongo():
        doc = _get_db().admin.find_one({"_id": "admin"})
        return {"username": doc["username"], "password": doc["password"]} if doc else None
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE) as f:
            return json.load(f)
    return None

def save_admin(username, hashed_password):
    if _use_mongo():
        _get_db().admin.replace_one({"_id": "admin"}, {"_id": "admin", "username": username, "password": hashed_password}, upsert=True)
    else:
        _ensure_data_dir()
        with open(ADMIN_FILE, "w") as f:
            json.dump({"username": username, "password": hashed_password}, f)
