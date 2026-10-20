-- Star schema for the sales dashboard.
-- The pipeline rebuilds these tables from scratch on every run (full refresh).

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;

CREATE TABLE dim_product (
    product_code  TEXT PRIMARY KEY,
    brand         TEXT NOT NULL,
    division      TEXT NOT NULL,
    category      TEXT NOT NULL,
    sub_category  TEXT NOT NULL
);

CREATE TABLE dim_customer (
    customer       TEXT PRIMARY KEY,
    country        TEXT NOT NULL,
    customer_type  TEXT NOT NULL,
    trade_type     TEXT NOT NULL,
    sales_mode     TEXT NOT NULL,
    sales_channel  TEXT NOT NULL
);

CREATE TABLE fact_sales (
    month              TEXT NOT NULL,  -- first day of the month, e.g. 2024-01-01
    customer           TEXT NOT NULL REFERENCES dim_customer (customer),
    product_code       TEXT NOT NULL REFERENCES dim_product (product_code),
    transaction_type   TEXT NOT NULL CHECK (transaction_type IN ('Sale', 'Return', 'Adjustment')),
    quantity           REAL NOT NULL,
    net_sales_aed      REAL NOT NULL,
    cost_of_sales_aed  REAL NOT NULL,
    gross_profit_aed   REAL NOT NULL,
    PRIMARY KEY (month, customer, product_code)
);