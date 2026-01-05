import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
            'Campaign': 'Campaign Name'
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
        # Loop through each platform (TikTok, Google, etc.) individually
        if 'Platform' in self.df.columns:
            for platform in self.df['Platform'].unique():
                p_data = self.df[self.df['Platform'] == platform].copy()
                
                # Dynamic Benchmarks (Relative to Platform)
                # "High Spend" = Top 25% of Spenders
                high_spend = p_data['Spend'].quantile(0.75)
                # "Low Engagement" = Bottom 25% of Engagement
                low_eng = p_data['Engagement Rate'].quantile(0.25)
                
                # Flagging logic
                bad_campaigns = p_data[
                    (p_data['Spend'] > high_spend) & 
                    (p_data['Engagement Rate'] < low_eng)
                ].copy()
                
                # Add Context for the User (The "Why")
                bad_campaigns['Flag Reason'] = f"Spend > ${high_spend:.0f} & ER < {low_eng:.2f}% (vs {platform} avg)"
                waste_list.append(bad_campaigns)
        
        if waste_list:
            return pd.concat(waste_list).sort_values(by='Spend', ascending=False)
        return pd.DataFrame()

# ==========================================
# 🖥️ THE DASHBOARD (Streamlit UI)
# ==========================================
st.set_page_config(page_title="Cross-Platform Audit", page_icon="🕵️", layout="wide")

st.sidebar.header("📂 Data Input")
uploaded_file = st.sidebar.file_uploader("Upload 'cross_platform_marketing_sample_v2.csv'", type=['csv', 'xlsx'])

st.title("🕵️ Cross-Platform Efficiency Audit")

if uploaded_file:
    # --- 1. LOAD DATA ---
    try:
        if uploaded_file.name.endswith('.csv'):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
            
        # Initialize Engine
        analyzer = MarketingAnalyzer(raw_df)
        df = analyzer.df

        # --- 2. TOP METRICS ---
        total_spend = df['Spend'].sum()
        total_impressions = df['Impressions'].sum()
        avg_er = df['Engagement Rate'].mean()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Spend Analyzed", f"${total_spend:,.0f}")
        c2.metric("Total Impressions", f"{total_impressions:,.0f}")
        c3.metric("Global Avg Engagement", f"{avg_er:.2f}%")
        
        st.divider()

        # --- 3. THE TABS ---
        tab1, tab2, tab3, tab4 = st.tabs(["📉 The Kill List", "📊 Performance Map", "🗓️ Heatmaps", "🧠 Strategy"])

        # TAB 1: THE KILL LIST (Relative Waste)
        with tab1:
            st.subheader("🚨 Detected Budget Waste")
            st.markdown("**Logic:** Identifying campaigns with *High Spend* & *Low Engagement* relative to their specific platform.")
            
            # Run the Smart Logic
            waste_df = analyzer.detect_relative_waste()
            
            if not waste_df.empty:
                st.error(f"⚠️ Found {len(waste_df)} campaigns burning budget (Total Waste: ${waste_df['Spend'].sum():,.0f})")
                
                # Display the "Smart" Table
                st.dataframe(
                    waste_df[['Platform', 'Campaign Name', 'Spend', 'Engagement Rate', 'Flag Reason']]
                    .style.background_gradient(subset=['Spend'], cmap='Reds')
                    .format({'Spend': '${:,.0f}', 'Engagement Rate': '{:.2f}%'}),
                    use_container_width=True
                )
                
                # Download Button
                csv = waste_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Kill List (CSV)",
                    csv,
                    "audit_kill_list.csv",
                    "text/csv"
                )
            else:
                st.success("✅ No major waste detected relative to benchmarks!")

        # TAB 2: PERFORMANCE MAP
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Efficiency Map")
                st.caption("Size = Impressions. Color = Platform.")
                fig_scatter = px.scatter(
                    df, 
                    x='Spend', 
                    y='Engagement Rate', 
                    size='Impressions',
                    color='Platform',
                    hover_data=['Clicks', 'CPC'],
                    title="Spend vs. Engagement Rate",
                    template="plotly_dark"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            with col2:
                st.subheader("Why Benchmarks Matter")
                st.caption("Visualizing the 'Normal' engagement range for each platform.")
                # Box Plot to explain why Google is lower than TikTok
                fig_box = px.box(
                    df, 
                    x='Platform', 
                    y='Engagement Rate', 
                    color='Platform',
                    title="Engagement Rate Distribution by Platform",
                    template="plotly_dark"
                )
                st.plotly_chart(fig_box, use_container_width=True)

        # TAB 3: HEATMAPS
        with tab3:
            st.subheader("When does your audience engage?")
            if 'Day' in df.columns:
                heat_data = df.groupby(['Day', 'Platform'])['Engagements'].sum().reset_index()
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                fig_heat = px.density_heatmap(
                    heat_data, 
                    x='Day', 
                    y='Platform', 
                    z='Engagements',
                    category_orders={"Day": days_order},
                    color_continuous_scale="Viridis",
                    title="Engagement Volume by Day & Platform"
                )
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.warning("Date column not found, cannot generate heatmap.")

        # TAB 4: STRATEGY SPLIT
        with tab4:
            st.subheader("Spend by Objective")
            if 'Objective' in df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    fig_pie = px.pie(
                        df, 
                        values='Spend', 
                        names='Objective', 
                        title='Where is the money going?',
                        hole=0.4,
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Bar Chart for Performance by Objective
                    obj_perf = df.groupby('Objective')[['Engagement Rate']].mean().reset_index()
                    fig_bar = px.bar(
                        obj_perf,
                        x='Objective',
                        y='Engagement Rate',
                        color='Objective',
                        title="Which Objective drives the most Engagement?",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No 'Objective' column found in this dataset.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👋 Upload your `cross_platform_marketing_sample_v2.csv` (the 20k row file) to begin.")
