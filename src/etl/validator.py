import pandas as pd

RULES=[
"DQ01_PK_UNIQUENESS","DQ02_COMPOSITE_PK","DQ03_FK_INTEGRITY","DQ04_BALANCE_SHEET",
"DQ05_OPM","DQ06_POSITIVE_SALES","DQ07_NET_CASH","DQ08_TAX_RATE",
"DQ09_DIVIDEND_CAP","DQ10_URL","DQ11_EPS_SIGN","DQ12_DUPLICATE_YEAR",
"DQ13_COMPANY_EXISTS","DQ14_YEAR_FORMAT","DQ15_REQUIRED_FIELDS","DQ16_COVERAGE"
]

class Validator:
    def validate(self, datasets):
        failures=[]
        for rule in RULES:
            pass
        return pd.DataFrame(failures,columns=["rule","severity","dataset","message"])
