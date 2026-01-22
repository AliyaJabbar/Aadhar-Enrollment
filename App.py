import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Aadhaar Enrollment Gap Analysis", 
    layout="wide", 
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# --- UPDATED UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    
    /* Updated to Light Violet Theme */
    .insight-box { 
        background-color: #f3e5f5; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #d1c4e9;
        border-left: 6px solid #7b1fa2; 
        color: #2c003e;
        font-weight: 500;
        margin-top: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.02);
    }
    
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #f0f0f0;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data
def load_and_clean_data():
    # Placeholder for your data loading logic
    # df = pd.read_parquet("cleaned_data.parquet")
    # district_df = pd.read_csv("district_priority.csv")
    
    # Mock data for demonstration if files don't exist
    data = {
        'state': ['Bihar', 'Maharashtra', 'Uttar Pradesh', 'Tamil Nadu', 'Bihar'],
        'District': ['Patna', 'Pune', 'Lucknow', 'Chennai', 'Gaya'],
        'total_enrollment': [5000, 7000, 9000, 4000, 3000],
        'children_enrollment': [3000, 2000, 5000, 1500, 1800],
        'age_0_5': [1000, 800, 2000, 500, 700],
        'age_5_17': [2000, 1200, 3000, 1000, 1100],
        'age_18_greater': [2000, 5000, 4000, 2500, 1200],
        'pincode': [101, 102, 103, 104, 105],
        'date': pd.to_datetime(['2026-01-01', '2026-01-05', '2026-01-10', '2026-01-15', '2026-01-20']),
        'PRIORITY_SCORE': [85, 40, 90, 30, 75]
    }
    df = pd.DataFrame(data)
    district_df = df.copy() # Simplified for example
    
    geojson_map = {"Andaman and Nicobar Islands": "Andaman & Nicobar", "Jammu and Kashmir": "Jammu & Kashmir"}
    df['state_for_map'] = df['state'].replace(geojson_map)
    df['month_name'] = df['date'].dt.month_name().str[:3]
    df['month_num'] = df['date'].dt.month
    
    return df, district_df

df_clean, district_summary = load_and_clean_data()

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.title("📌 Navigation & Filters")
    menu = st.radio("Switch View:", 
        ["📋 Executive Summary", "🗺️ National Heatmap", "🚨 Priority Districts", "📈 Enrollment Trends", "💫 Performance Matrix"])
    
    st.markdown("---")
    st.subheader("Filter Data")
    
    # State Filter
    all_states = sorted(df_clean['state'].unique())
    selected_states = st.multiselect("Select States", options=all_states, default=all_states)
    
    # Dynamic District Filter (updates based on state)
    filtered_districts = df_clean[df_clean['state'].isin(selected_states)]['District'].unique()
    selected_districts = st.multiselect("Select Districts", options=sorted(filtered_districts), default=sorted(filtered_districts))

    st.markdown("---")
    st.info(f"Showing data for {len(selected_states)} States and {len(selected_districts)} Districts.")

# --- FILTER DATA BASED ON SELECTION ---
df_final = df_clean[(df_clean['state'].isin(selected_states)) & (df_clean['District'].isin(selected_districts))]
dist_final = district_summary[(district_summary['state'].isin(selected_states)) & (district_summary['District'].isin(selected_districts))]

# --- HEADER ---
st.title("Aadhaar Enrollment Gap Analysis")
st.caption(f"Strategic Intelligence Dashboard | View: {menu}")

# --- 📋 SECTION 1: EXECUTIVE SUMMARY ---
if menu == "📋 Executive Summary":
    m1, m2, m3, m4 = st.columns(4)
    total_e = df_final['total_enrollment'].sum()
    child_e = df_final['children_enrollment'].sum()
    
    m1.metric("Total Enrollments", f"{total_e:,}")
    m2.metric("Child Enrollment", f"{child_e:,}", f"{(child_e/total_e*100 if total_e > 0 else 0):.1f}%")
    m3.metric("Pincodes Covered", f"{df_final['pincode'].nunique():,}")
    m4.metric("Adult Baseline", f"{df_final['age_18_greater'].sum():,}")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        age_totals = {'Age 0-5': df_final['age_0_5'].sum(), 'Age 5-17': df_final['age_5_17'].sum(), 'Age 18+': df_final['age_18_greater'].sum()}
        # Multi-color palette: Deep Purple, Amber, and Sky Blue
        fig3 = px.pie(names=list(age_totals.keys()), values=list(age_totals.values()), 
                     hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
        fig3.update_layout(title="Demographic Breakdown")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('<div class="insight-box">Strategic Observation: The demographic trend confirms that children (0-17) constitute the primary growth segment for new Aadhaar generation.</div>', unsafe_allow_html=True)

    with c2:
        top10_s = df_final.groupby('state')['children_enrollment'].sum().nlargest(10).reset_index()
        fig1 = px.bar(top10_s, x='children_enrollment', y='state', orientation='h',
                      title="Top States (Child Enrollment)", color='children_enrollment', color_continuous_scale='Purples')
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('<div class="insight-box">Operational Insight: High-volume states require optimized infrastructure to handle the demand in the 0-17 age bracket.</div>', unsafe_allow_html=True)

# ... (Rest of sections 2-5 follow same logic using df_final and dist_final)
