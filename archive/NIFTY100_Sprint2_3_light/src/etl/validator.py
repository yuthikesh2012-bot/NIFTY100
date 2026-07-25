import pandas as pd

RULES = [
    "DQ01",
    "DQ02",
    "DQ03",
    "DQ04",
    "DQ05",
    "DQ06",
    "DQ07",
    "DQ08",
    "DQ09",
    "DQ10",
    "DQ11",
    "DQ12",
    "DQ13",
    "DQ14",
    "DQ15",
    "DQ16",
]


class Validator:
    def validate(self, datasets):
        failures = []
        for name, frame in datasets.items():
            failures.extend(self.validate_frame(name, frame))
        return self.failure_frame(failures)

    def validate_frame(self, dataset, frame):
        failures = []
        if frame is None:
            return failures

        if isinstance(frame, pd.DataFrame):
            if "company_id" in frame.columns and frame["company_id"].duplicated().any():
                failures.append({"rule": "DQ01", "severity": "error", "dataset": dataset, "message": "Duplicate company_id values detected"})
            if "year" in frame.columns and frame["year"].duplicated().any():
                failures.append({"rule": "DQ12", "severity": "warning", "dataset": dataset, "message": "Duplicate year values detected"})
            if "sales" in frame.columns and (frame["sales"] <= 0).any():
                failures.append({"rule": "DQ06", "severity": "error", "dataset": dataset, "message": "Non-positive sales detected"})
            if "net_profit" in frame.columns and (frame["net_profit"] < 0).any():
                failures.append({"rule": "DQ11", "severity": "warning", "dataset": dataset, "message": "Negative net profit detected"})
            if "company_name" in frame.columns and frame["company_name"].fillna("").eq("").any():
                failures.append({"rule": "DQ15", "severity": "error", "dataset": dataset, "message": "Missing company_name values"})
            if "website" in frame.columns and frame["website"].fillna("").eq("").any():
                failures.append({"rule": "DQ10", "severity": "warning", "dataset": dataset, "message": "Missing website values"})
            if "tax_percentage" in frame.columns and (frame["tax_percentage"] > 40).any():
                failures.append({"rule": "DQ08", "severity": "warning", "dataset": dataset, "message": "Tax percentage exceeds 40"})
            if "net_cash_flow" in frame.columns and (frame["net_cash_flow"] < 0).any():
                failures.append({"rule": "DQ07", "severity": "warning", "dataset": dataset, "message": "Negative net cash flow detected"})
            if "ebitda" in frame.columns and (frame["ebitda"] == 0).any():
                failures.append({"rule": "DQ16", "severity": "warning", "dataset": dataset, "message": "Zero EBITDA detected"})
        return failures

    def failure_frame(self, failures):
        return pd.DataFrame(failures, columns=["rule", "severity", "dataset", "message"])