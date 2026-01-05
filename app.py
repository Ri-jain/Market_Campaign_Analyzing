import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np  # Kept for random data generation

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Cross-Platform Content Analyzer",
    page_icon="📱",
    layout="wide"
)

# --- 2. Sidebar & File Upload ---
with st.sidebar:
    st.header("1. Data Input")
    st.markdown("Upload your social media export (CSV).")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    
    st.markdown("---")
    st.header("2. Guide")
    st.info(
        """
        **Required Columns:**
        - Platform (text)
        - Date (date/time)
        - Spend (number)
        - Impressions (number)
        - Engagements (number)
        - Clicks (number)
        """
    )

# --- 3. Main Interface Logic ---
st.title("📱 Cross-Platform Content Analyzer")

if uploaded_file is None:
    # Empty State (User hasn't uploaded yet)
    st.info("👋 Welcome! Upload a CSV to compare TikTok, LinkedIn, and Instagram performance.")
    
    # Show a dummy table so user knows what to upload (Updated for Social)
    st.markdown("### Expected Data Format Example:")
    dummy_data = pd.DataFrame({
        'Platform': ['TikTok', 'LinkedIn', 'Instagram'],
        'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'Spend': [150, 200, 100],
        'Impressions': [15000, 4000, 8500],
        'Engagements': [300, 40, 450],
        'Clicks': [150, 20, 90]
    })
    st.table(dummy_data)

else:
    # --- 4. Data Processing & Error Handling ---
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- START AUTO-FIX LOGIC (Preserved from your old code) ---
        # 1. Clean column names (remove spaces)
        df.columns = df.columns.str.strip()

        # 2. Rename columns to standard schema
        rename_map = {
            'Cost': 'Spend',
            'Amount Spent': 'Spend',
            'Post engagement': 'Engagements',
            'Likes': 'Engagements',  # Fallback if "Engagements" doesn't exist
            'Views': 'Impressions',
            'Link Clicks': 'Clicks'
        }
        df = df.rename(columns=rename_map)

        # 3. If 'Platform' is missing, generate random data (Your "Audience" logic adapted)
        if 'Platform' not in df.columns:
            st.toast("⚠️ 'Platform' column missing - simulating data for demo.")
            platforms = ['TikTok', 'LinkedIn', 'Instagram', 'YouTube']
            df['Platform'] = np.random.choice(platforms, size=len(df))
        # --- END AUTO-FIX LOGIC ---

        # Check for missing columns
        req_cols = ['Date', 'Spend', 'Impressions', 'Engagements', 'Clicks']
        missing_cols = [c for c in req_cols if c not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Error: Your CSV is missing these columns: {', '.join(missing_cols)}")
        else:
            # Data Cleaning
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df['Day'] = df['Date'].dt.day_name()
            
            # --- NEW METRIC CALCULATIONS (The "New Engine") ---
            # Avoid division by zero errors
            df['CTR'] = df.apply(lambda x: (x['Clicks'] / x['Impressions']) * 100 if x['Impressions'] > 0 else 0, axis=1)
            df['Engagement Rate'] = df.apply(lambda x: (x['Engagements'] / x['Impressions']) * 100 if x['Impressions'] > 0 else 0, axis=1)
            df['CPC'] = df.apply(lambda x: x['Spend'] / x['Clicks'] if x['Clicks'] > 0 else 0, axis=1)

            # --- 5. Top Level KPIs ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Spend", f"${df['Spend'].sum():,.0f}")
            c2.metric("Total Impressions", f"{df['Impressions'].sum():,.0f}")
            c3.metric("Avg CTR", f"{df['CTR'].mean():.2f}%")
            c4.metric("Avg Engagement Rate", f"{df['Engagement Rate'].mean():.2f}%")
            
            st.divider()

            # --- 6. The Required Views (Tabs) ---
            tab1, tab2, tab3 = st.tabs(["📊 Performance", "🗓️ Heatmaps", "🏆 Rankings"])

            # VIEW 1: Engagement vs Spend (The "Efficiency Map")
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Efficiency Map")
                    st.caption("Are you paying for engagement?")
                    fig_scatter = px.scatter(
                        df, 
                        x='Spend', 
                        y='Engagement Rate', 
                        size='Impressions',
                        color='Platform',
                        hover_data=['Clicks', 'CPC'],
                        title="Spend vs. Engagement Rate (Size = Impressions)",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                with col2:
                    st.subheader("Impressions by Platform")
                    fig_bar = px.bar(
                        df.groupby('Platform')[['Impressions']].sum().reset_index(), 
                        x='Platform', 
                        y='Impressions', 
                        color='Platform',
                        title="Where are the eyeballs?",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

            # VIEW 2: Heatmap (Best Time to Post)
            with tab2:
                st.subheader("When does your audience engage?")
                if 'Day' in df.columns:
                    # Aggregating for Heatmap
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

            # VIEW 3: Leaderboard (Updated for Content)
            with tab3:
                st.subheader("Top Performing Content")
                
                # Filter cols that exist
                cols_to_show = ['Platform', 'Spend', 'Impressions', 'Clicks', 'CTR', 'Engagement Rate']
                final_cols = [c for c in cols_to_show if c in df.columns]
                
                # Sort by Engagement Rate instead of ROAS
                ranking = df[final_cols].sort_values(by='Engagement Rate', ascending=False).head(20)
                
                st.dataframe(
                    ranking.style.background_gradient(subset=['Engagement Rate'], cmap="Greens").format({
                        'Spend': "${:,.2f}",
                        'Impressions': "{:,.0f}",
                        'Clicks': "{:,.0f}",
                        'CTR': "{:.2f}%",
                        'Engagement Rate': "{:.2f}%"
                    }),
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
