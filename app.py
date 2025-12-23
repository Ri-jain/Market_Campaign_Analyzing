import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np  # Added for random audience generation

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Campaign Analytics Dashboard",
    page_icon="📈",
    layout="wide"
)

# --- 2. Sidebar & File Upload ---
with st.sidebar:
    st.header("1. Data Input")
    st.markdown("Upload your campaign data CSV below.")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    
    st.markdown("---")
    st.header("2. Guide")
    st.info(
        """
        **Required Columns:**
        - Campaign (text)
        - Date (date/time)
        - Spend (number)
        - Revenue (number)
        - Audience (text)
        """
    )

# --- 3. Main Interface Logic ---
st.title("🚀 Marketing Campaign Analyzer")

if uploaded_file is None:
    # Empty State (User hasn't uploaded yet)
    st.info("👋 Welcome! Please upload a CSV file in the sidebar to begin analysis.")
    st.markdown("### Expected Data Format Example:")
    # Show a dummy table so user knows what to upload
    dummy_data = pd.DataFrame({
        'Campaign': ['Summer_Promo', 'Winter_Sale'],
        'Date': ['2025-01-01', '2025-01-02'],
        'Spend': [1000, 1500],
        'Revenue': [3000, 4000],
        'Audience': ['Gen Z', 'Millennials']
    })
    st.table(dummy_data)

else:
    # --- 4. Data Processing & Error Handling ---
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- START AUTO-FIX LOGIC ---
        # 1. Rename columns if they match your Google Ads format
        rename_map = {
            'Day': 'Date',
            'Cost': 'Spend',
            'Total conv. value': 'Revenue'
        }
        df = df.rename(columns=rename_map)

        # 2. If 'Audience' is missing, generate random data so the app doesn't crash
        if 'Audience' not in df.columns:
            st.toast("⚠️ 'Audience' column missing - generating simulated data for demo.")
            audiences = ['Gen Z', 'Millennials', 'Gen X', 'Boomers', 'All']
            df['Audience'] = np.random.choice(audiences, size=len(df))
        # --- END AUTO-FIX LOGIC ---

        # Check for missing columns (After the fix)
        req_cols = ['Campaign', 'Date', 'Spend', 'Revenue', 'Audience']
        missing_cols = [c for c in req_cols if c not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Error: Your CSV is missing these columns: {', '.join(missing_cols)}")
        else:
            # Data Cleaning / Feature Engineering
            # Use dayfirst=True to handle DD/MM/YY format correctly
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
            df['Day'] = df['Date'].dt.day_name()
            
            # Calculate KPIs
            df['ROAS'] = df['Revenue'] / df['Spend']
            total_spend = df['Spend'].sum()
            total_rev = df['Revenue'].sum()
            total_roas = total_rev / total_spend if total_spend > 0 else 0

            # --- 5. Top Level KPIs ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Spend", f"${total_spend:,.0f}")
            c2.metric("Total Revenue", f"${total_rev:,.0f}")
            c3.metric("Aggregate ROAS", f"{total_roas:.2f}x")
            
            st.divider()

            # --- 6. The Required Views (Tabs) ---
            tab1, tab2, tab3 = st.tabs(["📊 Performance", "🗓️ Heatmaps", "🏆 Rankings"])

            # VIEW 1 & 2: Spend vs Return & Audience
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Spend vs. Return")
                    fig_scatter = px.scatter(
                        df, x='Spend', y='Revenue', 
                        color='Campaign', size='ROAS',
                        hover_data=['Audience'],
                        title="Campaign Efficiency (Size = ROAS)"
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                with col2:
                    st.subheader("Performance by Audience")
                    # Aggregate by audience
                    aud_df = df.groupby('Audience')[['Spend', 'Revenue']].sum().reset_index()
                    aud_df['ROAS'] = aud_df['Revenue'] / aud_df['Spend']
                    
                    fig_bar = px.bar(
                        aud_df, x='Audience', y='ROAS', 
                        color='Audience',
                        title="ROAS by Audience Segment"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

            # VIEW 3: Day/Time Heatmap
            with tab2:
                st.subheader("Day of Week Performance")
                # Aggregating for Heatmap
                heat_data = df.groupby(['Day', 'Campaign'])['Revenue'].sum().reset_index()
                
                # Sorting days correctly
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                fig_heat = px.density_heatmap(
                    heat_data, x='Day', y='Campaign', z='Revenue',
                    category_orders={"Day": days_order},
                    color_continuous_scale="Viridis",
                    title="Revenue Concentration by Day & Campaign"
                )
                st.plotly_chart(fig_heat, use_container_width=True)

            # VIEW 4: Campaign Ranking
            with tab3:
                st.subheader("Campaign Leaderboard")
                ranking = df.groupby('Campaign')[['Spend', 'Revenue', 'ROAS']].mean().reset_index()
                ranking = ranking.sort_values(by='ROAS', ascending=False)
                
                # Formatting the table with pandas styler for visual impact
                st.dataframe(
                    ranking.style.background_gradient(subset=['ROAS'], cmap="Greens").format({
                        'Spend': "${:,.2f}",
                        'Revenue': "${:,.2f}",
                        'ROAS': "{:.2f}x"
                    }),
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")