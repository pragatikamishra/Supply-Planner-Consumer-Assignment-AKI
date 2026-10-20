
# Business context for SalesPilot

This file explains what the numbers mean, so SalesPilot can answer "why" questions.
It comes from the Power BI dashboard findings. Update it when the dashboard shows something new.

## What the measures mean

- Net sales: money received after discounts, in AED. Returns are negative.
- Gross profit = net sales - cost of sales.
- Gross margin % = gross profit / net sales. The company average is about 24%.
- A negative gross margin means the product cost more than it was sold for (sold below cost).
- Return rate % = returns value / gross sales. The company average is about 1.2%.
- Transaction types: Sale (normal sale), Return (customer sent goods back, negative quantity), Adjustment (zero quantity, value correction).

## How to explain common findings

- Negative or very low margin: usually the product is sold below cost to some customers (heavy discounts, promotions or special trade terms), or its cost went up while the selling price stayed the same. Look at which customers or months have the lowest margin.
- High return rate: possible quality or damage problems, wrong orders, or over-stocking at the customer. Look at which customers or months the returns come from.
- Sales drop in a month: check holidays. In 2024, Ramadan was in March to early April, and Eid Al Fitr was 8-12 April, which explains the low April.
- Sales peak: September is back to school; December and January are the Dubai Shopping Festival.

## Brand groups on the dashboard (scatter chart)

- Star: above-average sales and above-average margin.
- Volume driver: above-average sales but below-average margin.
- Hidden gem: below-average sales but above-average margin.
- Question mark: below average on both.

## What a planner should do

- Products sold below cost: review the price, discounts and supplier cost before re-ordering.
- Products with high returns: check quality and the supplier before ordering more.
- Seasonal dips: order less before the dip and restock early for the rebound.

## Key findings from the dashboard (2024)

These numbers were checked on the Power BI dashboard. Use them when someone asks about
the findings, insights or a summary.

### Overall

- Net sales were AED 441.89M at a 24.41% gross margin. Returns were AED 5.39M, a 1.21% return rate. 292 customers bought during the year.
- Data quality: 8 of 160,572 rows were rejected because quantity and value had opposite signs. They are kept in data/rejected with a reason.

### Seasonality (Overview page)

- April was the weakest month at AED 26.25M, 24.7% below March, because of the end of Ramadan and Eid Al Fitr (8-12 April).
- May rebounded by 44% as customers restocked after Eid.
- September was the peak month at AED 44.79M (back to school).
- Planner action: order less before Ramadan, and restock early for the May rebound and the September peak.

### Products and brands (Products page)

- Brand 16 (AED 91.78M) and Brand 15 (AED 62.75M) are the two biggest brands, but they are volume drivers with only 15-19% margin, below the company's 24.41%.
- Product P015 (Brand 26) is sold below cost, at a -0.61% gross margin.
- Product P105 (Brand 14) has an 8.70% return rate, about 7 times the 1.21% average.
- The Automotive division sells about AED 22M at almost 0% margin.
- Durable Goods has the best margin (about 39%) but also the highest return rate (4.84%).
- Planner action: protect stock of the volume drivers, review pricing of P015 and Automotive, and check quality for P105 before re-ordering.

### Customers and channels (Customers page)

- Customer 219 (a supermarket) is the biggest customer, at AED 29.57M.
- The top 10 customers make up 35.54% of sales, which is a concentration risk.
- Modern Trade is the biggest trade type (about AED 156M) and has the highest return rate (about 2%).
- Key Accounts earn only about 0.8% margin, so their trade terms should be reviewed.
- The online share looks tiny (0.19%) only because some E-Commerce customers have no Online/Offline label. E-Commerce customers actually buy about AED 50M. This is a data-quality issue, not real behaviour.

## How the data was prepared (the pipeline)

- Source: a Google Sheet with three tabs: sales (160,572 rows, monthly, 2024, UAE, AED), product (250 products) and customer (292 customers).
- Extract: Python downloads each tab and saves an untouched copy in data/raw.
- Checks: every column was profiled (missing values, duplicates, types, ranges). Every product and customer in sales exists in the master tables. Month + customer + product is unique. Negative values, zero quantities and sign mismatches were counted.
- Decisions: returns were kept and labelled (Sale, Return, Adjustment) instead of deleted. Product and customer details repeated in the sales tab were verified identical, then kept only in the product and customer tables (star schema). Customer labels were tidied (spacing, capitals) and split into trade type and online/offline. 8 rows with opposite signs were rejected with a reason.
- Load: the clean tables go into a SQLite database (data/sales.db), and row counts are verified (160,572 in = 160,564 loaded + 8 rejected).
- One command (python main.py) runs everything in about 16 seconds and writes a log file.
- Power BI reads the database through ODBC, and SalesPilot reads the same database, so both always show the same numbers.

## Recommendations for the manager

1. Plan stock by season: order less before Ramadan and Eid, restock early for May, and build stock for September.
2. Protect availability of the volume-driver brands (Brand 16 and Brand 15), but review their pricing because their margin is below average.
3. Fix loss-makers: review the price and cost of P015 and the Automotive division.
4. Investigate returns: check quality and supplier for P105, and returns in Modern Trade and Durable Goods.
5. Reduce customer risk: agree forecasts with the top 10 customers, who make up 35.54% of sales, and review Key Account trade terms.
6. Fix data quality at the source: add the missing Online/Offline labels for E-Commerce customers and correct the 8 rejected rows.
7. Next data to add: stock levels, supplier lead times and more years of sales, to calculate reorder points and forecast demand.
