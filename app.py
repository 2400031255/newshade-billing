import uuid, json, os, math
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import Customer, Bill, BillItem
from services import SERVICES, get_services, DEFAULTS
from storage import (save_customer, get_customer, get_all_customers,
                     find_customer_by_phone, save_bill, get_bills_by_date,
                     delete_customer_visit, load_services, save_services, delete_service)

app = Flask(__name__)
app.secret_key = "newshades-secret-2024"

ADMIN_FILE = os.path.join(os.environ.get("SALON_DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"), "admin.json")

def _get_admin():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE) as f:
            return json.load(f)
    # first run — hash the default password
    hashed = generate_password_hash("komali123")
    _save_admin("komali", hashed)
    return {"username": "komali", "password": hashed}

def _save_admin(username, hashed_password):
    os.makedirs("data", exist_ok=True)
    with open(ADMIN_FILE, "w") as f:
        json.dump({"username": username, "password": hashed_password}, f)

def gen_id(prefix=""):
    return prefix + str(uuid.uuid4())[:8].upper()

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def employee_or_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") not in ("admin", "employee"):
            flash("Employee or Admin access required.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def login_or_guest_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("role"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("role"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        admin = _get_admin()
        if username == admin["username"] and check_password_hash(admin["password"], password):
            session["role"] = "admin"
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/guest")
def guest():
    session["role"] = "guest"
    return redirect(url_for("dashboard"))

@app.route("/employee")
def employee():
    session["role"] = "employee"
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Pages ─────────────────────────────────────────────────────────────────────

@app.route("/")
@login_or_guest_required
def dashboard():
    customers = get_all_customers()
    today = datetime.now().strftime("%Y-%m-%d")
    bills = get_bills_by_date(today)
    revenue = sum(b["total"] for b in bills.values())
    return render_template("dashboard.html", total_customers=len(customers),
                           total_bills=len(bills), revenue=revenue, today=today)

@app.route("/customers")
@login_or_guest_required
def customers():
    return render_template("customers.html", customers=get_all_customers())

@app.route("/customers/add", methods=["GET", "POST"])
@employee_or_admin_required
def add_customer():
    if request.method == "POST":
        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        if find_customer_by_phone(phone):
            flash("Customer with this phone already exists.", "error")
        else:
            save_customer(Customer(gen_id("C"), name, phone))
            flash("Customer added successfully.", "success")
            return redirect(url_for("customers"))
    return render_template("add_customer.html")

@app.route("/customers/<cid>/history")
@login_or_guest_required
def customer_history(cid):
    customer = get_customer(cid)
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for("customers"))
    return render_template("customer_history.html", customer=customer)

@app.route("/bill/new", methods=["GET", "POST"])
@employee_or_admin_required
def new_bill():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        name = request.form.get("name", "").strip()
        customer = find_customer_by_phone(phone)
        if not customer:
            if not name:
                flash("Please provide customer name.", "error")
                return render_template("new_bill.html", services=SERVICES)
            customer = Customer(gen_id("C"), name, phone)
            save_customer(customer)

        service_ids = request.form.getlist("services")
        if not service_ids:
            flash("Please select at least one service.", "error")
            return render_template("new_bill.html", services=SERVICES)

        items = []
        for sid in service_ids:
            qty = int(request.form.get(f"qty_{sid}", 1) or 1)
            items.append(BillItem(get_services()[sid], qty))

        discount = float(request.form.get("discount", 0) or 0)
        if math.isnan(discount) or math.isinf(discount) or not (0 <= discount <= 100):
            discount = 0.0
        payment = request.form.get("payment", "Cash")

        bill = Bill(gen_id("B"), customer, items, payment, discount=discount)
        save_bill(bill)

        customer.visit_history.append({
            "bill_id": bill.bill_id,
            "date": bill.date.strftime("%d-%m-%Y"),
            "total": bill.total,
            "payment_method": payment
        })
        save_customer(customer)
        return redirect(url_for("bill_receipt", bid=bill.bill_id))

    return render_template("new_bill.html", services=SERVICES)

@app.route("/bill/<bid>")
@login_or_guest_required
def bill_receipt(bid):
    from storage import get_all_bills
    bills = get_all_bills()
    if bid not in bills:
        flash("Bill not found.", "error")
        return redirect(url_for("dashboard"))
    b = bills[bid]
    # ensure date string is full ISO format for time display
    customer = get_customer(b["customer_id"])
    return render_template("bill_receipt.html", bill=b, bill_id=bid, customer=customer)

@app.route("/customers/<cid>/delete", methods=["POST"])
@admin_required
def delete_customer(cid):
    from storage import _read_json, _write_json, CUSTOMERS_FILE
    data = _read_json(CUSTOMERS_FILE)
    data.pop(cid, None)
    _write_json(CUSTOMERS_FILE, data)
    flash("Customer deleted.", "success")
    return redirect(url_for("customers"))

@app.route("/customers/<cid>/history/<bid>/delete", methods=["POST"])
@admin_required
def delete_visit(cid, bid):
    delete_customer_visit(cid, bid)
    flash("Visit record deleted.", "success")
    return redirect(url_for("customer_history", cid=cid))

@app.route("/services")
@admin_required
def services_page():
    return render_template("services.html", services=get_services())

@app.route("/services/add", methods=["POST"])
@admin_required
def add_service():
    data = load_services() or {sid: {"name": s["name"], "price": s["price"]} for sid, s in DEFAULTS.items()}
    new_id = str(max(int(k) for k in data.keys()) + 1)
    name = request.form.get("name", "").strip()
    price = float(request.form.get("price", 0) or 0)
    if name:
        data[new_id] = {"name": name, "price": price}
        save_services(data)
        flash(f"Service '{name}' added.", "success")
    return redirect(url_for("services_page"))

@app.route("/services/<sid>/edit", methods=["POST"])
@admin_required
def edit_service(sid):
    data = load_services() or {s: {"name": v["name"], "price": v["price"]} for s, v in DEFAULTS.items()}
    if sid in data:
        data[sid]["name"] = request.form.get("name", data[sid]["name"]).strip()
        data[sid]["price"] = float(request.form.get("price", data[sid]["price"]) or 0)
        save_services(data)
        flash("Service updated.", "success")
    return redirect(url_for("services_page"))

@app.route("/services/<sid>/delete", methods=["POST"])
@admin_required
def remove_service(sid):
    data = load_services() or {s: {"name": v["name"], "price": v["price"]} for s, v in DEFAULTS.items()}
    name = data.get(sid, {}).get("name", "")
    delete_service(sid)
    flash(f"Service '{name}' deleted.", "success")
    return redirect(url_for("services_page"))
@app.route("/profile", methods=["GET", "POST"])
@admin_required
def profile():
    admin = _get_admin()
    if request.method == "POST":
        new_username = request.form.get("username", "").strip()
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        if not check_password_hash(admin["password"], current_password):
            flash("Current password is incorrect.", "error")
            return render_template("profile.html", admin=admin)
        if not new_username:
            flash("Username cannot be empty.", "error")
            return render_template("profile.html", admin=admin)
        if new_password and new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("profile.html", admin=admin)
        _save_admin(new_username, generate_password_hash(new_password) if new_password else admin["password"])
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", admin=admin)

@app.route("/revenue")
@admin_required
def revenue():
    from storage import get_all_bills
    all_bills = get_all_bills()
    daily = {}
    for bid, b in all_bills.items():
        day = b["date"][:10]
        if day not in daily:
            daily[day] = {"total": 0, "bills": 0, "payment": {}}
        daily[day]["total"] += b["total"]
        daily[day]["bills"] += 1
        pm = b["payment_method"]
        daily[day]["payment"][pm] = daily[day]["payment"].get(pm, 0) + b["total"]
    sorted_daily = dict(sorted(daily.items(), reverse=True))
    grand_total = sum(v["total"] for v in daily.values())
    return render_template("revenue.html", daily=sorted_daily, grand_total=grand_total)

@app.route("/about")
@login_or_guest_required
def about():
    return render_template("about.html")

@app.route("/report", methods=["GET", "POST"])
@admin_required
def report():
    date_str = request.form.get("date", datetime.now().strftime("%Y-%m-%d")) if request.method == "POST" else datetime.now().strftime("%Y-%m-%d")
    bills = get_bills_by_date(date_str)
    revenue = sum(b["total"] for b in bills.values())
    payment_summary = {}
    for b in bills.values():
        pm = b["payment_method"]
        payment_summary[pm] = payment_summary.get(pm, 0) + b["total"]
    return render_template("report.html", date=date_str, bills=bills,
                           revenue=revenue, payment_summary=payment_summary)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=8080)
