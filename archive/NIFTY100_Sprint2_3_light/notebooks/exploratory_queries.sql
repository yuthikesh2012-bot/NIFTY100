-- 1. Company count by sector
SELECT broad_sector, COUNT(*) AS company_count
FROM companies
GROUP BY broad_sector;

-- 2. Top 10 companies by market capitalization
SELECT company_name, market_cap
FROM companies
ORDER BY market_cap DESC
LIMIT 10;

-- 3. Sales trend by year
SELECT year, SUM(sales) AS total_sales
FROM profitandloss
GROUP BY year
ORDER BY year;

-- 4. Net profit trend by year
SELECT year, SUM(net_profit) AS total_net_profit
FROM profitandloss
GROUP BY year
ORDER BY year;

-- 5. Companies with negative net cash flow
SELECT company_id, year, net_cash_flow
FROM cashflow
WHERE net_cash_flow < 0
ORDER BY net_cash_flow ASC;

-- 6. Companies with high dividend payout
SELECT company_id, year, dividend_payout
FROM profitandloss
WHERE dividend_payout > 20
ORDER BY dividend_payout DESC;

-- 7. Companies with low ROE
SELECT company_id, year, roe_percentage
FROM financial_ratios
WHERE roe_percentage < 10
ORDER BY roe_percentage ASC;

-- 8. Balance sheet leverage by year
SELECT year, AVG(total_liabilities / NULLIF(total_assets, 0)) AS avg_leverage
FROM balancesheet
GROUP BY year
ORDER BY year;

-- 9. Recent stock prices by company
SELECT company_id, date, close_price
FROM stock_prices
ORDER BY date DESC
LIMIT 20;

-- 10. Companies with missing sector mapping
SELECT c.company_id, c.company_name
FROM companies c
LEFT JOIN sectors s ON s.company_id = c.company_id
WHERE s.company_id IS NULL;
