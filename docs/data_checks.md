# Data checks

I ran `python -m python.profile_data`, which measures every column of the raw files.
Full report: docs/data_profile.md

**1. Does each table have a unique ID?**
Yes for product and customer. Every Product code (250) and every Customer (292) appears only once.
Sales has no single ID. One customer buys many products each month, so a sales row is
identified by Month + Customer + Product code (to be verified).

**2. Are there empty cells?**
No. No cell is empty in any of the 3 tables.

**3. Are there duplicate rows in sales?**
No. No row appears twice.

**4. Are numbers stored with symbols like $ or commas?**
No. Quantity, Net sales and Cost are all plain numbers.

**5. What do the dates look like?**
Month is text like "Jan-2024", one value per month, January to December 2024.
So the data is monthly, not daily, and it needs converting to a real date.

**6. Does every sale point to a real product and customer?**
Yes. Every Product code and Customer in sales exists in the product and customer tables.

**7. Anything strange?**

- Some Quantity, Net sales and Cost values are negative. These are likely returns.
- Country is always "UAE" and UOM is always "EA", so these columns add no information.
- Customer type is written inconsistently, e.g. "General Trade-Offline" vs "Modern Trade - Offline".

## Decisions

- A. Negative rows (returns): keep them and add an `is_return` flag.
  Reason: returns are real business events. Removing them would overstate sales,
  and the flag lets the dashboard show gross sales, returns and net sales separately.
- B. Product/customer details repeated in sales: check they match the product and
  customer tables first. If they match, keep only the keys (Product code, Customer)
  in sales. Reason: each fact is stored in one place, so it can't contradict itself.
- C. Messy labels: fix spacing and capitals, and split Customer type into Trade type and
  Online/Offline. Look-alike labels are not merged, because that is a business decision;
  they are flagged for the data owner.
- D. The 8 rows where quantity and value have opposite signs are moved to
  data/rejected/sales_rejected.csv with a reason, so they stay out of the dashboard
  but are kept for review.

## Deep checks

I ran `python -m python.deep_checks` to answer the questions the profile raised.

**1. Is Month + Customer + Product code unique in sales?**
Yes. No combination appears twice, so each sales row is one customer buying one product in one month.

**2. How many rows are negative or zero? Any sold below cost?**

- About 9,450 rows (6%) are returns: negative quantity and value, totalling -5.4M AED
  (1.2% of the 441.9M AED net sales).
- 216 rows have quantity 0 but money moved. These are likely discounts or price corrections.
- 8 rows make no sense: quantity and value point in opposite directions.
- 1,576 rows were sold below cost (cost higher than sales). This is normal business, e.g. promotions.

**3. Do the product details in sales match the product table?**
Yes. Brand, Division, Category and Sub-category match exactly (0 differences).
So sales only needs to keep Product code.

**4. Do the customer details in sales match the customer table?**
Yes. Country and Customer type match exactly (0 differences).
So sales only needs to keep Customer.

**5. Are the Customer type and Sales channel labels clean?**
No.

- Customer type has 12 labels with inconsistent spacing ("General Trade-Offline" vs
  "Modern Trade - Offline") and look-alikes ("Modern Trade" vs "Modern Trade - Offline",
  "E-Commerce" vs "E-Commerce-Online").
- Sales channel has 13 labels, all in CAPITALS, including code-like names (CONTRACTUAL5, CONTRACTUAL6).

## External data: UAE 2024 calendar

- Public holidays: https://www.talentmate.com/articles/uae-public-holidays-2024-complete-list
- Retail seasons (Ramadan, Dubai Shopping Festival, summer, back to school): general knowledge, approximate dates
- Used to label months in Power BI (dim_date[Public Holiday], dim_date[Retail Season]).
  Shows timing only, not cause. Islamic dates shift about 11 days each year.
