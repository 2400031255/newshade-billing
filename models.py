from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class Service:
    name: str
    price: float
    category: str = "General"


@dataclass
class BillItem:
    service: Service
    quantity: int = 1

    @property
    def total(self):
        return self.service.price * self.quantity

@dataclass
class Customer:
    customer_id: str
    name: str
    phone: str
    visit_history: List[dict] = field(default_factory=list)

@dataclass
class Bill:
    bill_id: str
    customer: Customer
    items: List[BillItem]
    payment_method: str
    date: datetime = field(default_factory=datetime.now)
    discount: float = 0.0

    @property
    def subtotal(self):
        return sum(item.total for item in self.items)

    @property
    def discount_amount(self):
        return self.subtotal * (self.discount / 100)

    @property
    def total(self):
        return self.subtotal - self.discount_amount
