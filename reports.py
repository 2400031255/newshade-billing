from models import Bill
from datetime import datetime

def print_bill(bill: Bill):
    width = 48
    print("\n" + "=" * width)
    print("       ✂  GLAMOUR BEAUTY PARLOUR  ✂")
    print("         123 MG Road, Bangalore - 560001")
    print("         Phone: +91-9876543210")
    print("=" * width)
    print(f"  Bill No : {bill.bill_id}")
    print(f"  Date    : {bill.date.strftime('%d-%m-%Y %I:%M %p')}")
    print(f"  Customer: {bill.customer.name}")
    print(f"  Phone   : {bill.customer.phone}")
    print("-" * width)
    print(f"  {'Service':<22} {'Qty':>4} {'Rate':>8} {'Amount':>8}")
    print("-" * width)
    for item in bill.items:
        print(f"  {item.service.name:<22} {item.quantity:>4} {item.service.price:>8.2f} {item.total:>8.2f}")
    print("-" * width)
    print(f"  {'Subtotal':<35} ₹{bill.subtotal:>8.2f}")
    if bill.discount > 0:
        print(f"  {'Discount (' + str(bill.discount) + '%)':<35} ₹{bill.discount_amount:>8.2f}")
    print(f"  {'TOTAL':<35} ₹{bill.total:>8.2f}")
    print("-" * width)
    print(f"  Payment Method : {bill.payment_method}")
    print("=" * width)
    print("     Thank you! Visit us again. 😊")
    print("=" * width + "\n")

def print_daily_report(date_str: str, bills: dict):
    total_revenue = sum(b["total"] for b in bills.values())
    total_bills = len(bills)
    payment_summary = {}
    for b in bills.values():
        pm = b["payment_method"]
        payment_summary[pm] = payment_summary.get(pm, 0) + b["total"]

    print("\n" + "=" * 50)
    print(f"       DAILY SALES REPORT — {date_str}")
    print("=" * 50)
    print(f"  Total Bills Generated : {total_bills}")
    print(f"  Total Revenue         : ₹{total_revenue:.2f}")
    print("-" * 50)
    print("  Payment Breakdown:")
    for method, amount in payment_summary.items():
        print(f"    {method:<20} ₹{amount:.2f}")
    print("=" * 50 + "\n")
