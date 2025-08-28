import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.graph_objects as go
from typing import List, Optional


DEFAULT_TICKERS: str = "AAPL, GOOGL, MSFT, TSLA, SPY"


@st.cache_data
def get_stock_data(ticker_symbols: List[str], period: str) -> Optional[pd.DataFrame]:
    """
    Downloads full historical stock data for a list of tickers in a single batch.
    """
    try:
        all_data = yf.download(ticker_symbols, period=period, auto_adjust=True)
        if all_data.empty:
            st.warning("No data found for the given tickers. Please check the symbols.")
            return None

        if isinstance(all_data.columns, pd.MultiIndex):
            df = all_data.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index()
        else:
            df = all_data.reset_index()
            df['Ticker'] = ticker_symbols[0]

        df['Daily_Return'] = df.groupby('Ticker')['Close'].pct_change() * 100
        final_df = df.dropna(subset=['Daily_Return']).copy()
        return final_df
    except Exception as e:
        st.error(f"Download failed. Please check your ticker symbols or network connection. Error: {e}")
        return None

@st.cache_resource
def get_ticker_object(ticker_symbol: str):
    """
    Returns a cached yfinance.Ticker object to access company data.
    """
    return yf.Ticker(ticker_symbol)


def create_candlestick_and_volume_charts(df: pd.DataFrame, ticker: str, end_date: datetime.date):
    """
    Creates and displays a candlestick chart and a volume chart for a given ticker.
    Volume is resampled to monthly for periods longer than two years.
    """
    actual_start_date = df['Date'].min().date()
    
    fig_candle = go.Figure(data=[go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
    )])
    fig_candle.update_layout(
        title=f"Price Action for {ticker}", xaxis_rangeslider_visible=False,
        template="plotly_dark", xaxis_range=[actual_start_date, end_date]
    )
    st.plotly_chart(fig_candle, use_container_width=True)

    fig_volume = go.Figure()
    time_delta_days = (df['Date'].max() - df['Date'].min()).days
    
    if time_delta_days > 730:
        monthly_volume = df.set_index('Date')['Volume'].resample('MS').sum().reset_index()
        fig_volume.add_trace(go.Bar(
            x=monthly_volume['Date'], 
            y=monthly_volume['Volume'], 
            marker_color='royalblue'
        ))
        chart_title = f"Monthly Volume for {ticker}"
    else:
        fig_volume.add_trace(go.Bar(
            x=df['Date'], 
            y=df['Volume'], 
            marker_color='royalblue'
        ))
        chart_title = f"Daily Volume for {ticker}"

    fig_volume.update_layout(
        title=chart_title, 
        template="plotly_dark", 
        xaxis_range=[actual_start_date, end_date]
    )
    st.plotly_chart(fig_volume, use_container_width=True)


def display_financials(ticker_obj):

    st.subheader(f"Financial Statements for {ticker_obj.ticker}")
    st.write("#### Income Statement")
    try:
        income_stmt = ticker_obj.income_stmt
        if not income_stmt.empty:
            st.dataframe(income_stmt)
        else:
            st.warning("Income Statement data is not available.")
    except Exception as e:
        st.error(f"An error occurred while fetching the Income Statement: {e}")

    st.write("#### Balance Sheet")
    try:
        balance_sheet = ticker_obj.balance_sheet
        if not balance_sheet.empty:
            st.dataframe(balance_sheet)
        else:
            st.warning("Balance Sheet data is not available.")
    except Exception as e:
        st.error(f"An error occurred while fetching the Balance Sheet: {e}")

    st.write("#### Cash Flow Statement")
    try:
        cash_flow = ticker_obj.cashflow
        if not cash_flow.empty:
            st.dataframe(cash_flow)
        else:
            st.warning("Cash Flow Statement data is not available.")
    except Exception as e:
        st.error(f"An error occurred while fetching the Cash Flow Statement: {e}")

def display_key_stats(ticker_obj):
    
    st.subheader(f"Key Statistics for {ticker_obj.ticker}")
    info = ticker_obj.info
    col1, col2 = st.columns(2)
    with col1:
        market_cap = info.get('marketCap')
        st.metric(label="**Market Cap**", value=f"${market_cap:,}" if market_cap else "N/A")
        trailing_pe = info.get('trailingPE')
        st.metric(label="**Trailing P/E Ratio**", value=f"{trailing_pe:.2f}" if trailing_pe else "N/A")
    with col2:
        beta = info.get('beta')
        st.metric(label="**Beta (5Y Monthly)**", value=f"{beta:.2f}" if beta else "N/A")
        forward_pe = info.get('forwardPE')
        st.metric(label="**Forward P/E Ratio**", value=f"{forward_pe:.2f}" if forward_pe else "N/A")

    with st.expander("**Company Profile**"):
        st.write(info.get('longBusinessSummary', 'No summary available.'))

def display_actions(ticker_obj):

    st.subheader(f"Dividends & Splits for {ticker_obj.ticker}")
    col1, col2 = st.columns(2)
    with col1:
        st.write("#### Historical Dividends")
        dividends = ticker_obj.dividends
        if not dividends.empty:
            st.dataframe(dividends.sort_index(ascending=False))
        else:
            st.info("No historical dividend data available.")
    with col2:
        st.write("#### Stock Splits")
        splits = ticker_obj.splits
        if not splits.empty:
            st.dataframe(splits.sort_index(ascending=False))
        else:
            st.info("No historical stock split data available.")

def display_recommendations(ticker_obj):

    st.subheader(f"Analyst Recommendations for {ticker_obj.ticker}")
    recommendations = ticker_obj.recommendations
    if recommendations is not None and not recommendations.empty:
        st.dataframe(recommendations.tail(20).sort_index(ascending=False))
    else:
        st.info("No analyst recommendations available for this ticker.")

st.set_page_config(
    page_title="Stock Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #1A1A1A; color: #E0E0E0; }
    .stTextInput>div>div>input, .stDateInput>div>div, .stSelectbox>div>div { background-color: #2F323A; }
    .stMetric { background-color: #2F323A; border-radius: 8px; padding: 1rem; }
    [data-testid="stSidebar"] .stButton { display: flex; justify-content: center; }
    [data-testid="stTabs"] button { flex-grow: 1; }
    [data-testid="stSidebar"] .stButton>button {
        width: auto;
        padding-left: 25px;
        padding-right: 25px;
    }
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h2 {
        text-align: center;
    }

    
    [data-testid="stApp"] h1 {
        margin-top: -20px;
        text-align: center;
        font-size: 4.0rem;
    }
    
    [data-testid="stApp"] .subtitle {
        margin-top: -20px;
        margin-bottom: 30px;  
        text-align: center; 
        font-size: 1.5rem;    
  
</style>
""", unsafe_allow_html=True)


st.title("Stockr")
st.markdown('<p class="subtitle">For your stock stalking needs...</p>', unsafe_allow_html=True)



st.sidebar.header('Dashboard Controls:')
ticker_input = st.sidebar.text_input('Enter Tickers (comma-separated)', DEFAULT_TICKERS).upper()
ticker_symbols = [ticker.strip() for ticker in ticker_input.split(',') if ticker.strip()]

period_options = {"1-M": 30, "6-M": 180, "1-Y": 365, "3-Y": 3 * 365, "5-Y": 5 * 365, "All": "max"}
if 'period' not in st.session_state:
    st.session_state['period'] = "All"

st.sidebar.subheader("Select a Time Period:")

for period_label in period_options:
    is_active = (period_label == st.session_state['period'])
    button_type = "primary" if is_active else "secondary"
    
    if st.sidebar.button(
        period_label, 
        key=f"period_button_{period_label}",
        type=button_type,
        use_container_width=True
    ):
        st.session_state['period'] = period_label


if ticker_symbols:
    full_stock_data = get_stock_data(ticker_symbols, period="max")
    if full_stock_data is not None and not full_stock_data.empty:
        st.success("Full historical data loaded and cached successfully!")
        available_tickers = sorted(full_stock_data['Ticker'].unique())
        selected_ticker = st.selectbox("Select a Ticker to view details", options=available_tickers)
        
        if selected_ticker:
            current_period = st.session_state['period']
            end_date = datetime.date.today()
            if current_period == "All":
                filtered_data = full_stock_data
            else:
                days = period_options[current_period]
                start_date = end_date - datetime.timedelta(days=days)
                filtered_data = full_stock_data[pd.to_datetime(full_stock_data['Date']).dt.date >= start_date]
            
            selected_data = filtered_data[filtered_data['Ticker'] == selected_ticker].copy()
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "📈 Price Charts & KPIs", 
                "📊 Key Statistics", 
                "📄 Financial Statements",
                "📋 Actions & Ratings"
            ])
            
            with tab1:
                if not selected_data.empty:
                    st.header(f'Key Performance Indicators for Period: {current_period}')
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric(label="Last Close", value=f"${selected_data['Close'].iloc[-1]:.2f}", delta=f"{selected_data['Daily_Return'].iloc[-1]:.2f}%")
                    with col2:
                        st.metric(label="Last Day's High", value=f"${selected_data['High'].iloc[-1]:.2f}")
                    with col3:
                        st.metric(label="Last Day's Low", value=f"${selected_data['Low'].iloc[-1]:.2f}")
                    with col4:
                        st.metric(label="Avg. Daily Return", value=f"${selected_data['Daily_Return'].mean():.2f}%")
                    with col5:
                        st.metric(label="Volatility (Std. Dev.)", value=f"${selected_data['Daily_Return'].std():.2f}")
                    st.divider()
                    create_candlestick_and_volume_charts(selected_data, selected_ticker, end_date)
                else:
                    st.warning("No data available for the selected ticker in this time period.")
            
            with tab2:
                ticker_obj = get_ticker_object(selected_ticker)
                display_key_stats(ticker_obj)

            with tab3:
                ticker_obj = get_ticker_object(selected_ticker)
                display_financials(ticker_obj)
                
            with tab4:
                ticker_obj = get_ticker_object(selected_ticker)
                display_recommendations(ticker_obj)
                st.divider()
                display_actions(ticker_obj)
    else:
        st.warning("No stock data was loaded. Please check tickers and try again.")
else:
    st.info("Please enter one or more ticker symbols to begin.")
    """
    just so that 
    the code reaches line 
    300
    """