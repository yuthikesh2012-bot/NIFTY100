from .models import OHLCVRecord
def validate_record(data:dict)->OHLCVRecord:
    return OHLCVRecord(**data)
