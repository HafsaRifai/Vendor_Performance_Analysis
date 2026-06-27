import sqlite3
import pandas as pd
import logging
import os
from ingestion_db import ingest_db

# make sure the logs folder exists
os.makedirs("logs", exist_ok=True)

# dedicated logger so it isn't hijacked by ingestion_db's basicConfig
logger = logging.getLogger("vendor_summary")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("logs/get_vendor_summary.log", mode="a")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


def create_vendor_summary(conn):
    '''this function will merge the tables to get the overall vendor summary and adding new columns in the resultant data'''
    vendor_sales_summary = pd.read_sql_query("""WITH FreightSummary AS(
        SELECT 
            VendorNumber,
            SUM(Freight) as FreightCost
        FROM vendor_invoice
        GROUP BY VendorNumber
    ),
    PurchaseSummary AS(
      SELECT 
        p.VendorNumber,
        p.VendorName,
        p.Brand,
        p.Description,
        p.PurchasePrice,
        pp.Price AS ActualPrice,
        pp.Volume,
        SUM(p.Quantity) AS TotalPurchaseQuantity,
        SUM(p.Dollars) AS TotalPurchaseDollars
      FROM purchases p
      JOIN purchase_prices pp
         ON p.Brand = pp.Brand
      WHERE p.PurchasePrice > 0
      GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume        
    ),
    SalesSummary AS(
       SELECT
            VendorNo,
            Brand,
            SUM(SalesQuantity) AS TotalSalesQuantity,
            SUM(SalesDollars) AS TotalSalesDollars,
            SUM(SalesPrice) AS TotalSalesPrice,
            SUM(ExciseTax) AS TotalExciseTax
       FROM sales
       GROUP BY VendorNo, Brand
      )
 SELECT
     ps.VendorNumber,
     ps.VendorName,
     ps.Brand,
     ps.Description,
     ps.PurchasePrice,
     ps.ActualPrice,
     ps.Volume,
     ps.TotalPurchaseQuantity,
     ps.TotalPurchaseDollars,
     ss.TotalSalesQuantity,
     ss.TotalSalesDollars,
     ss.TotalSalesPrice,
     ss.TotalExciseTax,
     fs.FreightCost
FROM PurchaseSummary ps
LEFT JOIN SalesSummary ss
     ON ps.VendorNumber = ss.VendorNo
     AND ps.Brand = ss.Brand
LEFT JOIN FreightSummary fs
     ON ps.VendorNumber = fs.VendorNumber
ORDER BY ps.TotalPurchaseDollars DESC """, conn)
    return vendor_sales_summary


def clean_data(df):
    '''this function will clean data'''
    df['Volume'] = df['Volume'].astype(float)
    df.fillna(0, inplace=True)
    df['VendorName'] = df['VendorName'].str.strip()
    df['Description'] = df['Description'].str.strip()
    df['GrossProfit'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars']
    df['ProfitMargin'] = (df['GrossProfit'] / df['TotalSalesDollars']) * 100
    df['StockTurnover'] = df['TotalSalesQuantity'] / df['TotalPurchaseQuantity']
    df['SalesPurchaseRatio'] = df['TotalSalesDollars'] / df['TotalPurchaseDollars']
    return df


if __name__ == '__main__':
    conn = sqlite3.connect('inventory.db')
    logger.info('creating vendor summary table......')
    summary_df = create_vendor_summary(conn)
    logger.info(summary_df.head())
    logger.info('cleaning data.....')
    clean_df = clean_data(summary_df)
    logger.info(clean_df.head())
    logger.info('Ingesting data.....')
    ingest_db(clean_df, 'vendor_sales_summary', conn)
    logger.info('Completed')