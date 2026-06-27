# Vendor Performance Analysis

An end-to-end data analytics project that evaluates vendor and brand performance for a retail/wholesale business — from raw data ingestion through SQL transformation, exploratory analysis, statistical hypothesis testing, and an interactive Power BI dashboard.

## Business Problem

Effective inventory and sales management are critical for optimizing profitability in the retail and wholesale industry. Companies need to ensure they aren't incurring losses due to inefficient pricing, poor inventory turnover, or excessive vendor dependency.

The goal of this analysis is to:
- Identify underperforming brands that require promotional or pricing adjustments
- Determine top vendors contributing to sales and gross profit
- Analyze the impact of bulk purchasing on unit costs
- Assess inventory turnover to reduce holding costs and improve efficiency
- Investigate the profitability variance between high-performing and low-performing vendors

## Data Overview

The raw data is spread across four tables, each serving a distinct purpose:

| Table | Description |
|---|---|
| `purchases` | Actual purchase transactions — date, brand, vendor, dollars paid, quantity purchased |
| `purchase_prices` | Product-wise actual and purchase prices; vendor + brand combination is unique |
| `vendor_invoice` | Aggregates of the purchases table (quantity, dollars) plus freight cost; unique by vendor + PO number |
| `sales` | Actual sales transactions — brand, quantity sold, selling price, revenue earned |

Since the data needed for analysis is spread across these tables, a **summary table** was built containing: purchase transactions per vendor, sales transaction data, freight costs per vendor, and actual product prices.

### Why pre-aggregate?

The underlying query involves heavy joins and aggregations across large `sales` and `purchases` tables. Storing the pre-aggregated result instead of re-running that query every time:
- Avoids repeated expensive computation
- Enables faster dashboarding & reporting — dashboards can pull directly from `vendor_sales_summary` rather than recomputing joins each time

## Workflow

1. **Data Ingestion** (`ingestion_db.py`) — Loads raw CSV files into a SQLite database (`inventory.db`) using SQLAlchemy, with logging for traceability.
2. **Exploratory Data Analysis** (`Exploratory_Data_Analysis.ipynb`) — Examines the individual tables to identify key variables and relationships, then builds the consolidated `vendor_sales_summary` table via a multi-CTE SQL query (freight, purchase, and sales summaries joined together) and cleans it.
3. **Vendor Summary Pipeline** (`get_vendor_summary.py`) — Productionizes that summary + cleaning logic into a reusable, loggable script.
4. **Statistical & Performance Analysis** (`Vendor_Performance_Analysis.ipynb`) — Analyzes the resultant summary table's column distributions to understand patterns, identify anomalies, and ensure data quality, then answers the core business questions (see Key Findings).
5. **Power BI Dashboard** — Visual reporting layer built on the final summarized data for stakeholder-facing insights.

## Key Derived Metrics

| Metric | Description |
|---|---|
| `GrossProfit` | TotalSalesDollars − TotalPurchaseDollars |
| `ProfitMargin` | GrossProfit / TotalSalesDollars × 100 |
| `StockTurnover` | TotalSalesQuantity / TotalPurchaseQuantity |
| `SalesPurchaseRatio` | TotalSalesDollars / TotalPurchaseDollars |
| `PurchaseContribution%` | Vendor's share of total purchase dollars |
| `UnsoldInventoryValue` | (TotalPurchaseQuantity − TotalSalesQuantity) × PurchasePrice |

## Key Findings

**Data Quality**
- Some transactions show negative gross profit (as low as -$52,002.78), indicating products sold at a loss.
- Some products were purchased but never sold (zero sales quantity/dollars) — likely slow-moving or obsolete stock.
- Purchase/freight costs show extreme variance (freight ranges from $0.09 to $257,032.07), pointing to possible logistics inefficiencies or bulk shipment effects.
- Stock turnover ranges from 0 to 274.5 — some products sell far faster than they're restocked, while others sit idle.

**Correlation Insights**
- Purchase price has almost no correlation with total sales dollars (-0.012) or gross profit (-0.016) — price variation alone doesn't drive sales or profit outcomes.
- Total purchase quantity and total sales quantity are very strongly correlated (0.999), reflecting efficient inventory flow-through overall.
- Profit margin correlates negatively with total sales price (-0.179), suggesting competitive pricing pressure compresses margins as prices rise.
- Stock turnover has weak negative correlation with both gross profit (-0.038) and profit margin (-0.055) — turning inventory faster doesn't necessarily mean higher profitability.

**Bulk Purchasing**
- Vendors buying in bulk (large order size) achieve the lowest unit price (~$10.78/unit) — about a **72% reduction** in unit cost compared to small orders.
- This confirms bulk pricing strategies are effective at incentivizing larger purchase volumes, even though per-unit revenue is lower.

**Vendor Profitability — Top vs. Low Performers**
- 95% CI for profit margin: **low-performing vendors: 40.48%–42.62%**, vs. **top-performing vendors: 30.74%–31.61%**.
- A two-sample t-test confirmed this difference is statistically significant (p < 0.05) — vendors with lower sales volume tend to maintain meaningfully higher margins, likely due to premium pricing or lower operating costs.
- **Implication for high-performing vendors**: selective price adjustments, cost optimization, or bundling could improve margins.
- **Implication for low-performing vendors**: despite strong margins, low volume may call for better marketing, more competitive pricing, or improved distribution.

## Power BI Dashboard
<img width="901" height="721" alt="image" src="https://github.com/user-attachments/assets/f8a9351a-97c4-435a-8802-71f26aaad25f" />

## Tech Stack

- **Python**: pandas, NumPy, Matplotlib, Seaborn, SciPy
- **Database**: SQLite, SQLAlchemy
- **Statistics**: Confidence intervals, two-sample t-test (hypothesis testing)
- **BI/Reporting**: Power BI
- **Logging**: Python `logging` module with per-script handlers

## Repository Structure
├── ingestion_db.py                      # CSV → SQLite ingestion script

├── get_vendor_summary.py                # Vendor summary table builder

├── Exploratory_Data_Analysis.ipynb      # Initial data exploration & SQL development

├── Vendor_Performance_Analysis.ipynb    # Core analysis & hypothesis testing

├── vendor_sales_summary.csv             # Final summarized dataset

├── logs/                                # Pipeline execution logs

└── README.md


## How to Run

```bash
# 1. Install dependencies
pip install pandas numpy matplotlib seaborn scipy sqlalchemy

# 2. Ingest raw CSVs into SQLite
python ingestion_db.py

# 3. Build the vendor summary table
python get_vendor_summary.py

# 4. Open the notebooks for EDA and analysis
jupyter notebook Vendor_Performance_Analysis.ipynb
```
