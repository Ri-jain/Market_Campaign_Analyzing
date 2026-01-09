import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io

# ==========================================
# 🧠 THE ENGINE (MarketingAnalyzer Class)
# ==========================================
class MarketingAnalyzer:
    def __init__(self, df):
        """Initialize with a dataframe directly."""
        self.df = df.copy()
        self._clean_data()
        self._calculate_metrics()

    def _clean_data(self):
        # 1. Clean Column Names
        self.df.columns = self.df.columns.str.strip()
        
        # 2. Rename Standards (Social + Search)
        rename_map = {
            'Cost': 'Spend', 'Amount Spent': 'Spend',
            'Post engagement': 'Engagements', 'Likes': 'Engagements',
            'Views': 'Impressions', 'Link Clicks': 'Clicks',
            'Campaign': 'Campaign Name', 'Ad Name': 'Campaign Name'
        }
        self.df = self.df.rename(columns=rename_map)
        
        # 3. Numeric Conversions
        for col in ['Spend', 'Impressions', 'Clicks', 'Engagements']:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

        # 4. Handle Date
        if 'Date' in self.df.columns:
            self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce', dayfirst=True)
            self.df['Day'] = self.df['Date'].dt.day_name()

    def _calculate_metrics(self):
        # Safe calculations avoiding division by zero
        self.df['CTR'] = np.where(self.df['Impressions'] > 0, (self.df['Clicks'] / self.df['Impressions']) * 100, 0)
        self.df['Engagement Rate'] = np.where(self.df['Impressions'] > 0, (self.df['Engagements'] / self.df['Impressions']) * 100, 0)
        self.df['CPC'] = np.where(self.df['Clicks'] > 0, self.df['Spend'] / self.df['Clicks'], 0)

    def detect_relative_waste(self):
        """
        The 'Smart Kill List' logic.
        Calculates waste thresholds RELATIVE to each platform.
        """
        waste_list = []
        if 'Platform' in self.df.columns:
            for platform in self.df['Platform'].unique():
                p_data = self.df[self.df['Platform'] == platform].copy()
                
                # Dynamic Benchmarks (Relative to Platform)
                high_spend = p_data['Spend'].quantile(0.75)
                low_eng = p_data['Engagement Rate'].quantile(0.25)
                
                # Flagging logic
                bad_campaigns = p_data[
                    (p_data['Spend'] > high_spend) & 
                    (p_data['Engagement Rate'] < low_eng)
                ].copy()
                
                # Add Context for the User (The "Why")
                bad_campaigns['Flag Reason'] = f"Spend > ${high_spend:,.0f} & ER < {low_eng:.2f}% (vs {platform} avg)"
                waste_list.append(bad_campaigns)
        
        if waste_list:
            return pd.concat(waste_list).sort_values(by='Spend', ascending=False)
        return pd.DataFrame()

# ==========================================
# 🛠️ HELPER: GENERATE EXCEL TEMPLATE
# ==========================================
def generate_excel_template():
    # 1. Define Data matching your SOP exactly
    headers = ['Platform', 'Date', 'Campaign Name', 'Objective', 'Location', 'Spend', 'Impressions', 'Clicks', 'Engagements']
    example_data = [
        ['TikTok', '2025-01-01', 'Summer_Promo_001', 'Awareness', 'Chicago', 500.00, 45000, 800, 3500],
        ['Google Ads', '2025-01-02', 'Search_Q1_Sales', 'Sales', 'New York', 1200.50, 15000, 600, 150],
        ['Instagram', '2025-01-03', 'Influencer_Collab', 'Engagement', 'Austin', 300.75, 22000, 400, 1800]
    ]
    df = pd.DataFrame(example_data, columns=headers)
    
    # 2. Write to In-Memory Buffer
    buffer = io.BytesIO()
    # Use xlsxwriter engine for formatting
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Data_Input', index=False)
        
        # Formatting (Green Headers)
        workbook = writer.book
        worksheet = writer.sheets['Data_Input']
        header_fmt = workbook.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1})
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 15)  # Set column width
            
    return buffer.getvalue()

# ==========================================
# 🖥️ THE DASHBOARD (Streamlit UI)
# ==========================================
st.set_page_config(page_title="Cross-Platform Audit", page_icon="🕵️", layout="wide")

st.sidebar.header("1. Start Here")

# --- STEP 1: DOWNLOAD TEMPLATE ---
st.sidebar.markdown("### Step 1: Get Template")
try:
    excel_file = generate_excel_template()
    st.sidebar.download_button(
        label="📥 Download Excel Template",
        data=excel_file,
        file_name="Marketing_Data_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Click to download a formatted Excel file with examples."
    )
except Exception as e:
    st.sidebar.warning("To enable template download, install XlsxWriter: `pip install XlsxWriter`")

st.sidebar.markdown("---")

# --- STEP 2: INSTRUCTIONS ---
st.sidebar.markdown("### Step 2: Instructions")
with st.sidebar.expander("⚠️ Read Before Uploading", expanded=True):
    st.markdown("""
    1. **Do not rename headers.**
    2. **Clean Numbers Only.** (e.g., `1200.50`, NOT `$1,200`).
    3. **Date Format:** `YYYY-MM-DD`.
    """)

st.sidebar.markdown("---")

# --- STEP 3: UPLOAD ---
st.sidebar.header("2. Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx'])

st.title("🕵️ Cross-Platform Efficiency Audit")

if uploaded_file:
    # --- 1. LOAD DATA ---
    try:
        if uploaded_file.name.endswith('.csv'):
            raw_
