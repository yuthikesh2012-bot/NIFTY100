CORE_FILES={"companies.xlsx","profitandloss.xlsx","balancesheet.xlsx","cashflow.xlsx","analysis.xlsx","documents.xlsx","prosandcons.xlsx"}

SUPPLEMENTARY_FILES={"sectors.xlsx","stock_prices.xlsx","market_cap.xlsx","financial_ratios.xlsx","peer_groups.xlsx"}

def detect_header(filename:str)->int:
    return 1 if filename.lower() in CORE_FILES else 0
