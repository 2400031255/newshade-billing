from models import Service

DEFAULTS = {
    "1":  {"name": "Haircut",              "price": 200.0},
    "2":  {"name": "Hair Wash",            "price": 150.0},
    "3":  {"name": "Hair Coloring",        "price": 800.0},
    "4":  {"name": "Hair Spa",             "price": 600.0},
    "5":  {"name": "Facial",               "price": 500.0},
    "6":  {"name": "Cleanup",              "price": 300.0},
    "7":  {"name": "Eyebrow Threading",    "price":  50.0},
    "8":  {"name": "Upper Lip Threading",  "price":  30.0},
    "9":  {"name": "Waxing (Full Arms)",   "price": 250.0},
    "10": {"name": "Waxing (Full Legs)",   "price": 350.0},
    "11": {"name": "Manicure",             "price": 300.0},
    "12": {"name": "Pedicure",             "price": 350.0},
    "13": {"name": "Bridal Makeup",        "price": 3000.0},
    "14": {"name": "Party Makeup",         "price": 1500.0},
    "15": {"name": "Head Massage",         "price": 200.0},
}

def get_services():
    from storage import load_services
    data = load_services()
    if not data:
        return {sid: Service(s["name"], s["price"]) for sid, s in DEFAULTS.items()}
    return {sid: Service(s["name"], s["price"]) for sid, s in data.items()}

# Keep SERVICES as a module-level accessor for backward compat
class _ServicesProxy(dict):
    def __getitem__(self, key):
        return get_services()[key]
    def items(self):
        return get_services().items()
    def __iter__(self):
        return iter(get_services())
    def __contains__(self, key):
        return key in get_services()
    def __len__(self):
        return len(get_services())

SERVICES = _ServicesProxy()
