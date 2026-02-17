import streamlit as st
import pandas as pd
from curl_cffi import requests
import time

st.set_page_config(page_title="NSE Live Pro", layout="wide")

# Persistent Settings
st.title("🇮🇳 NSE F&O Momentum Pro")
st.markdown("Auto-updates every **30 seconds** | Sorting: **% Change**")


def get_clean_data():
    """Fetches data with a new session every time to prevent 'stale' refreshes."""
    url = f"https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O&timestamp={int(time.time())}"
    try:
        session = requests.Session()
        # Knock on the front door
        session.get("https://www.nseindia.com", impersonate="chrome120", timeout=10)
        # Grab the data
        response = session.get(url, impersonate="chrome120", timeout=10)
        if response.status_code == 200:
            return response.json().get('data', [])
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return None


@st.fragment(run_every=30)
def scanner_fragment():
    # Visual Pulse to show refresh is working
    st.caption(f"🔄 Last Update: {time.strftime('%H:%M:%S')} IST")

    raw_data = get_clean_data()

    if raw_data:
        stocks = []
        for item in raw_data:
            if item.get('symbol') and item.get('symbol') != 'NIFTY 50':
                # Calculate Volume Change %
                curr_vol = item.get('totalTradedVolume', 0)
                prev_vol = item.get('lastDayQuantity', 0)

                vol_change_pct = 0
                if prev_vol and prev_vol > 0:
                    vol_change_pct = ((curr_vol - prev_vol) / prev_vol) * 100

                stocks.append({
                    "Symbol": item.get('symbol'),
                    "LTP": item.get('lastPrice'),
                    "% Change": item.get('pChange'),
                    "Volume": curr_vol,
                    "Vol Change %": vol_change_pct,  # Added next to Volume
                    "High": item.get('dayHigh'),
                    "Low": item.get('dayLow')
                })

        df = pd.DataFrame(stocks)
        # Conversion to numeric
        for col in ["LTP", "% Change", "High", "Low", "Volume", "Vol Change %"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Main Sort (Retained original Price % Change sorting)
        df = df.sort_values(by='% Change', ascending=False).dropna()

        # Display Top 20 and Bottom 20
        col1, col2 = st.columns(2)

        # Define height for 20 rows
        DF_HEIGHT = 738

        # Shared format dictionary
        format_mapping = {
            "LTP": "₹{:.2f}",
            "% Change": "{:+.2f}%",
            "High": "₹{:.2f}",
            "Low": "₹{:.2f}",
            "Volume": "{:,}",
            "Vol Change %": "{:+.2f}%"
        }

        with col1:
            st.success("🚀 **Top 20 Gainers**")
            st.dataframe(
                df.head(20).style.format(format_mapping)
                .background_gradient(subset=['% Change'], cmap='Greens')
                .background_gradient(subset=['Vol Change %'], cmap='Oranges'),  # Subtle highlight for volume
                use_container_width=True,
                hide_index=True,
                height=DF_HEIGHT
            )

        with col2:
            st.error("📉 **Top 20 Losers**")
            # Sort ascending for losers
            losers = df.sort_values(by='% Change', ascending=True).head(20)
            st.dataframe(
                losers.style.format(format_mapping)
                .background_gradient(subset=['% Change'], cmap='Reds')
                .background_gradient(subset=['Vol Change %'], cmap='Oranges'),
                use_container_width=True,
                hide_index=True,
                height=DF_HEIGHT
            )

    else:
        st.warning("🔄 Fetching new session from NSE... (Site might be busy)")


# Start the fragment
scanner_fragment()