# Raw data profile

## sales
Rows: 160,572 | Columns: 13 | Fully duplicated rows: 0

| column | missing | unique | type | range | examples |
|---|---|---|---|---|---|
| Month | 0 | 12 | date (100%) | 2024-01-01 to 2024-12-01 | Jan-2024, Feb-2024, Mar-2024 |
| Customer | 0 | 292 | text |  | Customer 001, Customer 002, Customer 003 |
| Country | 0 | 1 | text |  | UAE |
| Customer type | 0 | 12 | text |  | General Trade-Offline, Modern Trade - Offline, Key Account/Hypermarket |
| Brand | 0 | 39 | text |  | Brand 35, Brand 12, Brand 15 |
| Product code | 0 | 250 | text |  | P121, P192, P113 |
| Division | 0 | 6 | text |  | Durable Goods, Food, Personal Care |
| Category | 0 | 26 | text |  | Kitchen Appliances, Home Appliances, Baking |
| Sub-category | 0 | 52 | text |  | Air Fryers & Multi-Cookers, Irons & Garment Steamers, Brownie Mix |
| UOM | 0 | 1 | text |  | EA |
| Quantity | 0 | 3,345 | number (100%) | -5,402.00 to 23,046.00 | 4, 3, 11 |
| Net sales value (AED) | 0 | 119,835 | number (100%) | -216,651.56 to 1,038,572.16 | 1206.92, 1178, 1317.96 |
| Cost of sales (AED) | 0 | 110,590 | number (100%) | -95,316.06 to 951,541.41 | 829.22, 681.21, 916.72 |

## product
Rows: 250 | Columns: 5 | Fully duplicated rows: 0

| column | missing | unique | type | range | examples |
|---|---|---|---|---|---|
| Brand | 0 | 39 | text |  | Brand 26, Brand 10, Brand 16 |
| Product code | 0 | 250 | text |  | P001, P002, P003 |
| Division | 0 | 6 | text |  | Automotive, Food, Personal Care |
| Category | 0 | 26 | text |  | Lubricants, Confectionery, Oral Care |
| Sub-category | 0 | 52 | text |  | Engine Oil, Chocolate Wafers, Toothpaste |

## customer
Rows: 292 | Columns: 4 | Fully duplicated rows: 0

| column | missing | unique | type | range | examples |
|---|---|---|---|---|---|
| Customer | 0 | 292 | text |  | Customer 001, Customer 002, Customer 003 |
| Country | 0 | 1 | text |  | UAE |
| Customer type | 0 | 12 | text |  | General Trade-Offline, Modern Trade - Offline, Key Account/Hypermarket |
| Sales channel | 0 | 13 | text |  | PRIVATE, Other, GOVERNMENT |

## Links between tables
- `Sub-category` is in both sales and product: 0 values in sales missing from product, 0 values in product missing from sales
- `Category` is in both sales and product: 0 values in sales missing from product, 0 values in product missing from sales
- `Product code` is in both sales and product: 0 values in sales missing from product, 0 values in product missing from sales
- `Division` is in both sales and product: 0 values in sales missing from product, 0 values in product missing from sales
- `Brand` is in both sales and product: 0 values in sales missing from product, 0 values in product missing from sales
- `Country` is in both sales and customer: 0 values in sales missing from customer, 0 values in customer missing from sales
- `Customer` is in both sales and customer: 0 values in sales missing from customer, 0 values in customer missing from sales
- `Customer type` is in both sales and customer: 0 values in sales missing from customer, 0 values in customer missing from sales
