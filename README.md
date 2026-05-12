# Beauty Parlour Billing Management System

## Project Structure
```
billing/
├── main.py        # Entry point & CLI menu
├── models.py      # Data models (Customer, Bill, Service, BillItem)
├── services.py    # Service catalog with prices
├── storage.py     # JSON-based data persistence
├── reports.py     # Bill printing & daily report
└── data/          # Auto-created; stores customers.json & bills.json
```

## Run
```bash
cd /Users/nikhilkarthik/Desktop/billing
python main.py
```

## Features
| Feature | Description |
|---|---|
| New Bill | Select customer → pick services → apply discount → choose payment → print bill |
| Add Customer | Register new customer with name & phone |
| View Customers | List all customers with visit count |
| Visit History | Full billing history per customer |
| Daily Report | Revenue summary & payment breakdown for any date |

## Services Offered (15 services)
Haircut, Hair Wash, Hair Coloring, Hair Spa, Facial, Cleanup, Threading, Waxing, Manicure, Pedicure, Bridal Makeup, Party Makeup, Head Massage, and more.

## Data Storage
All data is persisted in `data/customers.json` and `data/bills.json` — no database required.
