PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS companies(
 company_id INTEGER PRIMARY KEY,
 ticker TEXT UNIQUE,
 company_name TEXT,
 sector_id INTEGER
);

CREATE TABLE IF NOT EXISTS profitandloss(
 company_id INTEGER,
 year TEXT,
 sales REAL,
 net_profit REAL,
 PRIMARY KEY(company_id,year),
 FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS balancesheet(
 company_id INTEGER,
 year TEXT,
 total_assets REAL,
 PRIMARY KEY(company_id,year),
 FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS cashflow(
 company_id INTEGER,
 year TEXT,
 operating_cashflow REAL,
 PRIMARY KEY(company_id,year),
 FOREIGN KEY(company_id) REFERENCES companies(company_id)
);
