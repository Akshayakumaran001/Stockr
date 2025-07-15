import yfinance as yf
import pandas as pd
import os


ticker_symbols = ["AAPL", "GOOGL", "MSFT"] 
output_dir = 'F:\\finance_projects'


os.makedirs(output_dir, exist_ok=True)

start_date_str = input("Enter the start date (YYYY-MM-DD, e.g., 2023-01-01): ")
end_date_str = input("Enter the end date (YYYY-MM-DD, e.g., 2023-12-31): ")

# Convert date strings to datetime objects
try:
    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)
except ValueError:
    print("Invalid date format. Please use YYYY-MM-DD.")
    exit()

# List to hold data for all tickers
all_stock_data = []

# Loop through each ticker symbol
for ticker in ticker_symbols:
    print(f"\nDownloading data for {ticker} from {start_date} to {end_date}...")
    try:
        # Download stock data
        stock_data_single = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)

        # Check if data was returned
        if stock_data_single.empty:
            print(f"No data found for {ticker} in the specified date range. Skipping.")
            continue

        # Add a 'Ticker' column to identify the stock
        stock_data_single['Ticker'] = ticker

        # Ensure columns are flat (yfinance with auto_adjust=True usually gives flat names, but this guards against MultiIndex issues)
        stock_data_single.columns = [col[0] if isinstance(col, tuple) else col for col in stock_data_single.columns]

        # Select only the required financial columns first
        required_financial_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        # Make sure these columns exist before selecting
        existing_financial_cols = [col for col in required_financial_cols if col in stock_data_single.columns]

        # If not all required columns exist, print a warning and skip this ticker (optional, but good for robustness)
        if len(existing_financial_cols) < len(required_financial_cols):
            print(f"Warning: Not all required financial columns found for {ticker}. Skipping.")
            continue

        stock_data_single = stock_data_single[existing_financial_cols]

        # Add the 'Ticker' column AFTER the initial column selection
        stock_data_single['Ticker'] = ticker

        # Calculate Daily_Return in percentage
        stock_data_single['Daily_Return'] = stock_data_single['Close'].pct_change() * 100

        # Drop rows with NaN in 'Daily_Return' (typically the first row, as pct_change() creates NaN for the first value)
        stock_data_single = stock_data_single.dropna(subset=['Daily_Return'])

        # Reset index to make 'Date' a regular column, for Power BI
        stock_data_single = stock_data_single.reset_index()

        all_stock_data.append(stock_data_single)
            

    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")

# Combine all data into a single DataFrame
if not all_stock_data:
    print("No stock data was successfully downloaded for any ticker. Exiting.")
    exit()

combined_stock_data = pd.concat(all_stock_data, ignore_index=True)

# Save the combined data to a single CSV file
output_filename = os.path.join(output_dir, "combined_stock_data.csv")
combined_stock_data.to_csv(output_filename, index=False)  
print(f"\nCombined data for {len(ticker_symbols)} tickers saved to {output_filename}")
