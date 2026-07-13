import csv
from pathlib import Path

def write_audit(records, output_file):
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file,'w',newline='') as f:
        w=csv.DictWriter(f, fieldnames=records[0].keys() if records else ['dataset'])
        w.writeheader()
        if records:
            w.writerows(records)
