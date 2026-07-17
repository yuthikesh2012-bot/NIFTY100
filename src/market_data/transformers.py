def normalize_record(record:dict)->dict:
    return {k.lower():v for k,v in record.items()}
