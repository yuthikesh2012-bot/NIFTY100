from datetime import datetime

def parse_date(value):
    for fmt in ("%Y-%m-%d","%d-%m-%Y","%d/%m/%Y"):
        try:
            return datetime.strptime(str(value),fmt)
        except Exception:
            pass
    return None
