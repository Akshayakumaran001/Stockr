import yfinance as yf
import pandas as pd
import os

# Define the path where the CSV will be saved
output_directory = r"F:\finance_projects" # Using a raw string (r"") to handle backslashes
output_filename = "combined_stock_data.csv"
output_filepath = os.path.join(output_directory, output_filename)

# Define the ticker symbols (confirmed list including TSLA)
ticker_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

# Ask the user for start and end dates
start_date_str = input("Enter the start date (YYYY-MM-DD, e.g., 2023-01-01): ")
end_date_str = input("Enter the end date (YYYY-MM-DD, e.g., 2023-12-31): ")

# Convert date strings to datetime objects for yfinance
start_date = pd.to_datetime(start_date_str)
end_date = pd.to_datetime(end_date_str)

all_stock_data = []

for ticker in ticker_symbols:
    print(f"\nDownloading data for {ticker} from {start_date} to {end_date}...")
    try:
        stock_data_single = yf.download(ticker, start=start_date, end=end_date)
        
        # --- DEBUGGING PRINT STATEMENTS FOR INDIVIDUAL TICKERS ---
        print(f"--- Data for {ticker} (Head):")
        print(stock_data_single.head())
        print(f"--- Data for {ticker} (Tail):")
        print(stock_data_single.tail())
        print(f"--- Data for {ticker} (Shape): {stock_data_single.shape}")
        # --- END OF DEBUGGING PRINT STATEMENTS ---

        if not stock_data_single.empty:
            stock_data_single['Ticker'] = ticker
            # Calculate daily return as percentage
            stock_data_single['Daily_Return'] = stock_data_single['Close'].pct_change() * 100
            all_stock_data.append(stock_data_single)
        else:
            print(f"No data found for {ticker} in the specified date range. Skipping.")
    except Exception as e:
        print(f"Failed to download data for {ticker}: {e}")

if all_stock_data:
    combined_data = pd.concat(all_stock_data)
    
    # --- DEBUGGING PRINT STATEMENTS FOR COMBINED DATAFRAME ---
    print("\n--- Combined Data (Head):")
    print(combined_data.head())
    print("\n--- Combined Data (Tail):")
    print(combined_data.tail())
    print(f"\n--- Combined Data (Tickers present): {combined_data['Ticker'].unique().tolist()}")
    print(f"\n--- Combined Data (Shape): {combined_data.shape}")
    # --- END OF DEBUGGING PRINT STATEMENTS ---

    combined_data.to_csv(output_filepath, index=True) # index=True to save the Date as a column
    print(f"\nCombined data for {len(all_stock_data)} tickers saved to {output_filepath}")
else:
    print("No data was downloaded for any ticker in the specified range.")

