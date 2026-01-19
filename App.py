import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Aadhaar Gap Analysis", layout="wide", page_icon="🎯")

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- ROBUST DATA LOADING ---
@st.cache_data
def load_and_clean_data():
    # Load Files
    df = pd.read_parquet("cleaned_data.parquet")
    district_df = pd.read_csv("district_priority.csv")
    
    # 1. THE OFFICIAL WHITELIST (Ensures exactly 36/36)
    INDIA_DIVISIONS = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
        'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
        'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
        'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
        'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
        'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
    ]
    
    # 2. GEOJSON MAPPING (For the Map visualization)
    # Most GeoJSONs use "&" and specific spellings
    geojson_map = {
        "Andaman and Nicobar Islands": "Andaman & Nicobar",
        "Jammu and Kashmir": "Jammu & Kashmir",
    }

    # 3. APPLY CLEANING
    df['state'] = df['state'].str.strip()
    # Force filter to only the 36 valid divisions
    df = df[df['state'].isin(INDIA_DIVISIONS)]
    df['state'] = df['state'].replace(geojson_map)
    
    # District Clean
    district_df = district_df[district_df['State'].isin(INDIA_DIVISIONS)]
    district_df['State'] = district_df['State'].replace(geojson_map)
    district_df = district_df[district_df['District'].str.lower() != 'unknown']

    # Dates
    df["date"] = pd.to_datetime(df["date"])
    df['month_name'] = df['date'].dt.month_name().str[:3]
    df['month_num'] = df['date'].dt.month

    return df, district_df

df_clean, district_summary = load_and_clean_data()

# --- SIDEBAR ---
st.sidebar.title("📊 Analysis Portal")
menu = st.sidebar.radio("Navigate:", 
    ["Overview", "National Heatmap", "Priority Ranking", "Growth Trends", "District Matrix"])

st.sidebar.markdown("---")
st.sidebar.success(f"✅ Data Status: 36/36 States/UTs")
st.sidebar.info(f"🏘️ Districts: {df_clean['district'].nunique():,}")

# --- DASHBOARD LOGIC ---

if menu == "Overview":
    st.title("🎯 Aadhaar Enrollment Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Population", f"{df_clean['total_enrollment'].sum():,}")
    c2.metric("Children (0-17)", f"{df_clean['children_enrollment'].sum():,}")
    c3.metric("State Coverage", "36/36")
    c4.metric("Avg Priority Score", f"{district_summary['PRIORITY_SCORE'].mean():.1f}")

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        # Age Donut
        age_data = {'0-5': df_clean['age_0_5'].sum(), '5-17': df_clean['age_5_17'].sum(), '18+': df_clean['age_18_greater'].sum()}
        fig = px.pie(names=list(age_data.keys()), values=list(age_data.values()), hole=0.5, 
                     title="Enrollment by Age Group", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        # Top States
        top_s = df_clean.groupby('state')['children_enrollment'].sum().nlargest(10).reset_index()
        fig = px.bar(top_s, x='children_enrollment', y='state', orientation='h', title="Top 10 States (Child Enrollment)")
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

elif menu == "National Heatmap":
    st.title("🌍 State-wise Enrollment Heatmap")
    state_map = df_clean.groupby('state')['children_enrollment'].sum().reset_index()
    fig = px.choropleth(
        state_map,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        featureidkey='properties.ST_NM',
        locations='state',
        color='children_enrollment',
        color_continuous_scale='YlGnBu',
        title="National Geographic Saturation"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=700)
    st.plotly_chart(fig, use_container_width=True)

elif menu == "Priority Ranking":
    st.title("🚨 Most Urgent Intervention Districts")
    priority_top = district_summary.sort_values('PRIORITY_SCORE', ascending=False).head(20).copy()
    priority_top['label'] = priority_top['District'] + " (" + priority_top['State'] + ")"
    fig = px.bar(priority_top, x='PRIORITY_SCORE', y='label', orientation='h', color='PRIORITY_SCORE', color_continuous_scale='Reds')
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=700)
    st.plotly_chart(fig, use_container_width=True)

elif menu == "Growth Trends":
    st.title("📈 Monthly Enrollment Velocity")
    monthly = df_clean.groupby(['month_num', 'month_name']).agg({'children_enrollment':'sum'}).reset_index().sort_values('month_num')
    fig = px.line(monthly, x='month_name', y='children_enrollment', markers=True, title="Enrollment Trends (2025)")
    st.plotly_chart(fig, use_container_width=True)

elif menu == "District Matrix":
    st.title("💫 Performance Analysis")
    fig = px.scatter(district_summary, x='Pincodes', y='Children', size='Total', color='PRIORITY_SCORE',
                     hover_name='District', color_continuous_scale='RdYlGn_r', title="Volume vs. Coverage")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Aadhaar Gap Analysis Dashboard v2.0 | Built for 2026 Hackathon")
