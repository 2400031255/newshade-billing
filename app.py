import uuid, json, os, math, shutil
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response, abort
from werkzeug.security import generate_password_hash, check_password_hash
from models import Customer, Bill, BillItem
from services import SERVICES, get_services, DEFAULTS
from storage import (save_customer, get_customer, get_all_customers,
                     find_customer_by_phone, save_bill, get_bills_by_date,
                     delete_customer_visit, load_services, save_services, delete_service,
                     get_admin, save_admin)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 1 day


def _get_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = uuid.uuid4().hex
        session["_csrf_token"] = token
    return token

@app.context_processor
def inject_csrf_token():
    return {"csrf_token": _get_csrf_token, "get_customer": get_customer}

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = request.form.get("_csrf_token") or request.headers.get("X-CSRFToken")
        if not token or token != session.get("_csrf_token"):
            abort(400, description="Invalid CSRF token")

@app.errorhandler(500)
def internal_error(e):
    return render_template("login.html"), 500

ADMIN_FILE = os.path.join(os.environ.get("SALON_DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"), "admin.json")

def _get_admin():
    admin = get_admin()
    if admin: return admin
    default_pass = os.environ.get("DEFAULT_ADMIN_PASSWORD") or "Admin@" + str(uuid.uuid4())[:6]
    hashed = generate_password_hash(default_pass)
    save_admin("admin", hashed)
    return {"username": "admin", "password": hashed}

def _save_admin(username, hashed_password, employee_password=None):
    save_admin(username, hashed_password, employee_password)

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
        if session.get("role") not in ("admin", "employee"):
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

@app.route("/employee", methods=["GET", "POST"])
def employee():
    admin = _get_admin()
    emp_pass = admin.get("employee_password", "") if admin else ""
    if not emp_pass:
        session["role"] = "employee"
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        entered = request.form.get("password", "")
        if check_password_hash(emp_pass, entered):
            session["role"] = "employee"
            return redirect(url_for("dashboard"))
        flash("Incorrect employee password.", "error")
    return redirect(url_for("login") + "?emp=1")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Pages ─────────────────────────────────────────────────────────────────────

@app.route("/")
@login_or_guest_required
def dashboard():
    customers = get_all_customers()
    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    bills = get_bills_by_date(today)
    revenue = sum(b["total"] for b in bills.values())

    # Recent bills with customer names
    recent_bills = []
    for bid, b in sorted(bills.items(), key=lambda x: x[1]["date"], reverse=True)[:8]:
        c = get_customer(b["customer_id"])
        recent_bills.append({"id": bid, "customer": c.name if c else "Walk-in", "total": b["total"], "payment": b["payment_method"], "time": b["date"][11:16]})

    # Top services today
    service_count = {}
    for b in bills.values():
        for item in b["items"]:
            name = item["service_name"]
            service_count[name] = service_count.get(name, 0) + item["quantity"]
    top_services = sorted(service_count.items(), key=lambda x: x[1], reverse=True)[:5]

    # Payment breakdown
    payment_summary = {}
    for b in bills.values():
        pm = b["payment_method"]
        payment_summary[pm] = payment_summary.get(pm, 0) + b["total"]

    return render_template("dashboard.html",
        total_customers=len(customers),
        total_bills=len(bills),
        revenue=revenue,
        recent_bills=recent_bills,
        top_services=top_services,
        payment_summary=payment_summary,
        today=today)

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

        try:
            discount = float(request.form.get("discount", 0) or 0)
            if not math.isfinite(discount) or not (0 <= discount <= 100):
                discount = 0.0
        except (ValueError, TypeError):
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
    data = load_services() or {sid: {"name": s["name"], "price": s["price"], "category": s.get("category", "General")} for sid, s in DEFAULTS.items()}
    next_id = max([int(k) for k in data.keys() if k.isdigit()] or [0]) + 1
    new_id = str(next_id)
    name = request.form.get("name", "").strip()
    try:
        price = float(request.form.get("price", 0) or 0)
        if not math.isfinite(price) or price < 0: price = 0.0
    except (ValueError, TypeError):
        price = 0.0
    category = request.form.get("category", "General").strip() or "General"
    if name:
        data[new_id] = {"name": name, "price": price, "category": category}
        save_services(data)
        flash(f"Service '{name}' added.", "success")
    return redirect(url_for("services_page"))

@app.route("/services/<sid>/edit", methods=["POST"])
@admin_required
def edit_service(sid):
    data = load_services() or {s: {"name": v["name"], "price": v["price"], "category": v.get("category", "General")} for s, v in DEFAULTS.items()}
    if sid in data:
        data[sid]["name"] = request.form.get("name", data[sid]["name"]).strip()
        try:
            data[sid]["price"] = float(request.form.get("price", data[sid]["price"]) or 0)
            if not math.isfinite(data[sid]["price"]) or data[sid]["price"] < 0: data[sid]["price"] = 0.0
        except (ValueError, TypeError):
            data[sid]["price"] = 0.0
        data[sid]["category"] = request.form.get("category", data[sid].get("category", "General")).strip() or "General"
        save_services(data)
        flash("Service updated.", "success")
    return redirect(url_for("services_page"))

@app.route("/services/<sid>/delete", methods=["POST"])
@admin_required
def remove_service(sid):
    data = load_services() or {s: {"name": v["name"], "price": v["price"], "category": v.get("category", "General")} for s, v in DEFAULTS.items()}
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
        emp_password = request.form.get("employee_password", None)
        # Employee password only save (skip admin password check)
        if current_password == "__skip__":
            new_emp = emp_password.strip() if emp_password is not None else ""
            hashed_emp = generate_password_hash(new_emp) if new_emp else admin.get("employee_password", "")
            _save_admin(admin["username"], admin["password"], hashed_emp)
            flash("Employee password updated.", "success")
            return redirect(url_for("profile"))
        if not check_password_hash(admin["password"], current_password):
            flash("Current password is incorrect.", "error")
            return render_template("profile.html", admin=admin)
        if not new_username:
            flash("Username cannot be empty.", "error")
            return render_template("profile.html", admin=admin)
        if new_password and new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("profile.html", admin=admin)
        emp_password = request.form.get("employee_password", "").strip()
        new_emp_hash = generate_password_hash(emp_password) if emp_password else admin.get("employee_password", "")
        _save_admin(new_username, generate_password_hash(new_password) if new_password else admin["password"], new_emp_hash)
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

# ── Search ───────────────────────────────────────────────────────────────────

@app.route("/customers/search")
@login_or_guest_required
def search_customers():
    q = request.args.get("q", "").strip().lower()
    all_customers = get_all_customers()
    if q:
        results = [c for c in all_customers if q in c.name.lower() or q in c.phone]
    else:
        results = all_customers
    return jsonify([{"id": c.customer_id, "name": c.name, "phone": c.phone, "visits": len(c.visit_history)} for c in results])

# ── Monthly Report ────────────────────────────────────────────────────────────

@app.route("/report/monthly", methods=["GET", "POST"])
@admin_required
def monthly_report():
    from storage import get_all_bills
    now = datetime.now().astimezone()
    month_str = request.form.get("month", now.strftime("%Y-%m")) if request.method == "POST" else now.strftime("%Y-%m")
    all_bills = get_all_bills()
    bills = {bid: b for bid, b in all_bills.items() if b["date"].startswith(month_str)}
    revenue = sum(b["total"] for b in bills.values())
    payment_summary = {}
    service_summary = {}
    daily_revenue = {}
    for b in bills.values():
        pm = b["payment_method"]
        payment_summary[pm] = payment_summary.get(pm, 0) + b["total"]
        day = b["date"][:10]
        daily_revenue[day] = daily_revenue.get(day, 0) + b["total"]
        for item in b["items"]:
            sn = item["service_name"]
            service_summary[sn] = service_summary.get(sn, 0) + item["quantity"]
    top_services = sorted(service_summary.items(), key=lambda x: x[1], reverse=True)[:10]
    daily_sorted = sorted(daily_revenue.items())
    return render_template("monthly_report.html", month=month_str, bills=bills,
        revenue=revenue, payment_summary=payment_summary,
        top_services=top_services, daily_sorted=daily_sorted)

# ── PDF Export ────────────────────────────────────────────────────────────────

@app.route("/report/pdf")
@admin_required
def export_pdf():
    from storage import get_all_bills
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import io
    month_str = request.args.get("month", datetime.now().astimezone().strftime("%Y-%m"))
    all_bills = get_all_bills()
    bills = {bid: b for bid, b in all_bills.items() if b["date"].startswith(month_str)}
    revenue = sum(b["total"] for b in bills.values())
    # Fix resource leak - use try/finally for BytesIO
    buf = io.BytesIO()
    try:
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        elements.append(Paragraph("Newshades Family Salon", styles["Title"]))
        elements.append(Paragraph(f"Monthly Report \u2014 {month_str}", styles["Heading2"]))
        elements.append(Paragraph(f"Total Bills: {len(bills)}   |   Total Revenue: Rs.{revenue:.2f}", styles["Normal"]))
        elements.append(Spacer(1, 12))
        data = [["Bill ID", "Date", "Customer", "Total", "Payment"]]
        for bid, b in sorted(bills.items(), key=lambda x: x[1]["date"], reverse=True):
            c = get_customer(b["customer_id"])
            data.append([bid, b["date"][:10], c.name if c else "Walk-in", f"Rs.{b['total']:.2f}", b["payment_method"]])
        t = Table(data, colWidths=[80, 80, 150, 80, 80])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#3d1a3a")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTSIZE", (0,0), (-1,0), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fdf6f0")]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e8dce4")),
            ("FONTSIZE", (0,1), (-1,-1), 9),
            ("PADDING", (0,0), (-1,-1), 6),
        ]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)
        pdf_data = buf.read()
    finally:
        buf.close()
    response = make_response(pdf_data)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=report_{month_str}.pdf"
    return response

# ── Backup ───────────────────────────────────────────────────────────────────

def _do_backup(dest_dir=None):
    """Create a zip backup. Returns (zip_path, filename) or raises."""
    import zipfile
    from storage import DATA_DIR
    fname = f"newshades_backup_{datetime.now().astimezone().strftime('%Y%m%d_%H%M')}.zip"
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
        zip_path = os.path.join(dest_dir, fname)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in ["customers.json", "bills.json", "services.json", "admin.json"]:
                fp = os.path.join(DATA_DIR, f)
                if os.path.exists(fp):
                    zf.write(fp, f)
        # Keep only last 10 backups
        backups = sorted([f for f in os.listdir(dest_dir) if f.startswith("newshades_backup")])
        for old in backups[:-10]:
            try:
                os.remove(os.path.join(dest_dir, old))
            except OSError:
                pass
        return zip_path, fname
    return None, fname

def _get_backup_dir():
    """Return backup folder path from config or default."""
    from storage import DATA_DIR
    cfg_file = os.path.join(DATA_DIR, "backup_config.json")
    if os.path.exists(cfg_file):
        with open(cfg_file) as f:
            cfg = json.load(f)
        return cfg.get("backup_dir", "")
    return ""

@app.route("/backup")
@admin_required
def backup():
    import zipfile, io
    from storage import DATA_DIR
    # Also auto-save to configured folder
    bdir = _get_backup_dir()
    if bdir and os.path.isdir(bdir):
        try:
            _do_backup(bdir)
        except OSError:
            pass
    # Always download zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in ["customers.json", "bills.json", "services.json", "admin.json"]:
            fpath = os.path.join(DATA_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, fname)
    buf.seek(0)
    response = make_response(buf.read())
    response.headers["Content-Type"] = "application/zip"
    response.headers["Content-Disposition"] = f"attachment; filename=newshades_backup_{datetime.now().astimezone().strftime('%Y%m%d_%H%M')}.zip"
    return response

@app.route("/backup/settings", methods=["GET", "POST"])
@admin_required
def backup_settings():
    from storage import DATA_DIR
    cfg_file = os.path.join(DATA_DIR, "backup_config.json")
    backup_dir = _get_backup_dir()
    last_backups = []
    if backup_dir and os.path.isdir(backup_dir):
        last_backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("newshades_backup")], reverse=True)[:5]
    if request.method == "POST":
        new_dir = os.path.normpath(request.form.get("backup_dir", "").strip())
        if new_dir and new_dir != "." and not os.path.isdir(new_dir):
            flash(f"Folder not found: {new_dir}", "error")
        elif new_dir and "." in new_dir.split(os.sep) and new_dir != ".":
            flash("Invalid backup folder path.", "error")
            new_dir = ""
        else:
            with open(cfg_file, "w") as f:
                json.dump({"backup_dir": new_dir}, f)
            flash("Backup folder saved!", "success")
            if new_dir:
                try:
                    _do_backup(new_dir)
                    flash("First backup created successfully!", "success")
                except Exception as e:
                    flash(f"Backup failed: {e}", "error")
        return redirect(url_for("backup_settings"))
    return render_template("backup_settings.html", backup_dir=backup_dir, last_backups=last_backups)

# ── Printer helpers ───────────────────────────────────────────────────────────

import platform

def _get_system_printers():
    """Return (printers_list, default) cross-platform."""
    system = platform.system()
    printers, default = [], ""
    if system == "Windows":
        try:
            import win32print
            printers = [p[2] for p in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            default = win32print.GetDefaultPrinter()
        except ImportError:
            pass
    else:  # macOS / Linux
        try:
            import subprocess
            lpstat_path = shutil.which("lpstat") or "/usr/bin/lpstat"
            out = subprocess.check_output([lpstat_path, "-a"], text=True, timeout=4)
            printers = [line.split()[0] for line in out.strip().splitlines() if line]
            try:
                d = subprocess.check_output([lpstat_path, "-d"], text=True, timeout=4)
                default = d.split(":")[-1].strip()
            except (subprocess.SubprocessError, OSError):
                default = printers[0] if printers else ""
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass
    return printers, default

def _get_saved_printer():
    from storage import DATA_DIR
    cfg = os.path.join(DATA_DIR, "printer_config.json")
    if os.path.exists(cfg):
        with open(cfg) as f:
            return json.load(f).get("printer", "")
    return ""

def _build_escpos_lines(bid, b, customer):
    """Build ESC/POS text content, returns list of (cmd, args) tuples."""
    W = 42
    subtotal = sum(i["service_price"] * i["quantity"] for i in b["items"])
    disc_amt = subtotal * b["discount"] / 100

    def row(label, value):
        gap = W - len(label) - len(value)
        return label + " " * max(1, gap) + value

    content = []
    content.append(("center_bold_big", "NEWSHADES FAMILY SALON"))
    content.append(("center", "Look Beautiful, Feel Beautiful"))
    content.append(("divider", "-"))
    content.append(("center_bold", "PAYMENT RECEIPT"))
    content.append(("divider", "-"))
    content.append(("left", row("Bill No :", bid)))
    content.append(("left", row("Date    :", b["date"][:10])))
    content.append(("left", row("Time    :", b["date"][11:16])))
    content.append(("left", row("Customer:", (customer.name if customer else "Walk-in")[:18])))
    content.append(("left", row("Mobile  :", customer.phone if customer else "-")))
    content.append(("divider", "-"))
    content.append(("bold", row("SERVICE", "AMOUNT")))
    content.append(("divider", "-"))
    for item in b["items"]:
        amt = item["service_price"] * item["quantity"]
        qty = f" x{item['quantity']}" if item["quantity"] > 1 else ""
        name = (item["service_name"] + qty)[:22]
        content.append(("left", row(name, f"Rs.{int(amt)}"[:10])))
    content.append(("divider", "-"))
    if b["discount"] > 0:
        content.append(("left", row("Subtotal", f"Rs.{int(subtotal)}"[:10])))
        content.append(("left", row(f"Discount({b['discount']}%)", f"-Rs.{int(disc_amt)}"[:10])))
        content.append(("divider", "-"))
    content.append(("bold_big", row("TOTAL", f"Rs.{int(b['total'])}")))
    content.append(("divider", "="))
    content.append(("left", row("Payment :", b["payment_method"])))
    content.append(("left", row("Status  :", "Paid")))
    content.append(("divider", "-"))
    content.append(("center", "Thank You! Visit Again"))
    content.append(("center", "Newshades Family Salon"))
    content.append(("center", "Look Beautiful, Feel Beautiful"))
    content.append(("feed", ""))
    return content

def _print_escpos(p, content):
    W = 42
    for cmd, text in content:
        if cmd == "center_bold_big":
            p.set(align="center", bold=True, double_height=True, double_width=False)
            p.text(text + "\n")
            p.set(align="left", bold=False, double_height=False)
        elif cmd == "center_bold":
            p.set(align="center", bold=True)
            p.text(text + "\n")
            p.set(align="left", bold=False)
        elif cmd == "center":
            p.set(align="center")
            p.text(text + "\n")
            p.set(align="left")
        elif cmd == "bold":
            p.set(bold=True)
            p.text(text + "\n")
            p.set(bold=False)
        elif cmd == "bold_big":
            p.set(bold=True, double_height=True)
            p.text(text + "\n")
            p.set(bold=False, double_height=False)
        elif cmd == "divider":
            p.text(text * W + "\n")
        elif cmd == "feed":
            p.text("\n\n\n")
        else:
            p.text(text + "\n")
    p.cut()

# ── ESC/POS Direct Print ─────────────────────────────────────────────────────

@app.route("/bill/<bid>/thermal", methods=["POST"])
@employee_or_admin_required
def thermal_print(bid):
    from storage import get_all_bills
    bills = get_all_bills()
    if bid not in bills:
        return jsonify({"error": "Bill not found"}), 404
    b = bills[bid]
    customer = get_customer(b["customer_id"])
    printer_name = request.form.get("printer", "").strip() or _get_saved_printer()

    if not printer_name:
        return jsonify({"error": "no_printer"}), 200

    try:
        content = _build_escpos_lines(bid, b, customer)
        system = platform.system()

        if system == "Windows":
            from escpos.printer import Win32Raw
            p = Win32Raw(printer_name)
            try:
                _print_escpos(p, content)
            finally:
                try:
                    p.close()
                except Exception:
                    pass

        else:  # macOS / Linux — use CUPS via lp command with raw ESC/POS bytes
            import subprocess, tempfile
            from escpos.printer import File as EscFile
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tf:
                tmp_path = tf.name
            try:
                p = EscFile(tmp_path)
                _print_escpos(p, content)
                p.close()
                lp_path = shutil.which("lp") or "/usr/bin/lp"
                subprocess.run(
                    [lp_path, "-d", printer_name, "-o", "raw", tmp_path],
                    check=True, timeout=10
                )
            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        return jsonify({"success": True})

    except ImportError:
        return jsonify({"error": "python-escpos not installed. Run: pip install python-escpos"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/printer-settings", methods=["GET", "POST"])
@admin_required
def printer_settings():
    from storage import DATA_DIR
    cfg_file = os.path.join(DATA_DIR, "printer_config.json")
    saved_printer = _get_saved_printer()
    printers, _ = _get_system_printers()
    if request.method == "POST":
        selected = request.form.get("printer", "").strip()
        with open(cfg_file, "w") as f:
            json.dump({"printer": selected}, f)
        flash(f"Printer set to: {selected or 'None'}", "success")
        return redirect(url_for("printer_settings"))
    return render_template("printer_settings.html", printers=printers, saved_printer=saved_printer)

@app.route("/printers")
@employee_or_admin_required
def get_printers():
    printers, default = _get_system_printers()
    return jsonify({"printers": printers, "default": default})

@app.route("/printer/test", methods=["POST"])
@employee_or_admin_required
def printer_test():
    printer_name = _get_saved_printer()
    if not printer_name:
        return jsonify({"error": "no_printer"})
    try:
        content = [
            ("center_bold", "NEWSHADES FAMILY SALON"),
            ("center", "--- TEST PRINT ---"),
            ("left",  "Printer is working!"),
            ("left",  "All systems OK."),
            ("divider", "-"),
            ("center", "Newshades Family Salon"),
            ("feed", ""),
        ]
        system = platform.system()
        if system == "Windows":
            from escpos.printer import Win32Raw
            p = Win32Raw(printer_name)
            try:
                _print_escpos(p, content)
            finally:
                try:
                    p.close()
                except Exception:
                    pass
        else:
            import subprocess, tempfile
            from escpos.printer import File as EscFile
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tf:
                tmp_path = tf.name
            try:
                p = EscFile(tmp_path)
                _print_escpos(p, content)
                p.close()
                lp_path = shutil.which("lp") or "/usr/bin/lp"
                subprocess.run([lp_path, "-d", printer_name, "-o", "raw", tmp_path],
                               check=True, timeout=10)
            finally:
                try: os.remove(tmp_path)
                except OSError: pass
        return jsonify({"success": True})
    except ImportError:
        return jsonify({"error": "python-escpos not installed. Run: pip install python-escpos"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/clear-data", methods=["POST"])
@admin_required
def clear_data():
    from storage import _write_json, BILLS_FILE, CUSTOMERS_FILE
    _write_json(BILLS_FILE, {})
    _write_json(CUSTOMERS_FILE, {})
    flash("All bills and customers cleared.", "success")
    return redirect(url_for("dashboard"))

@app.route("/report", methods=["GET", "POST"])
@admin_required
def report():
    date_str = request.form.get("date", datetime.now().astimezone().strftime("%Y-%m-%d")) if request.method == "POST" else datetime.now().astimezone().strftime("%Y-%m-%d")
    bills = get_bills_by_date(date_str)
    revenue = sum(b["total"] for b in bills.values())
    payment_summary = {}
    for b in bills.values():
        pm = b["payment_method"]
        payment_summary[pm] = payment_summary.get(pm, 0) + b["total"]
    return render_template("report.html", date=date_str, bills=bills,
                           revenue=revenue, payment_summary=payment_summary)

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("HOST", "0.0.0.0")  # 0.0.0.0 = accessible on local network
    app.run(host=host, debug=debug, port=8080)
