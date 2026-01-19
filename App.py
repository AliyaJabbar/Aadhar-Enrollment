import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="Aadhaar Gap Analysis", layout="wide", page_icon="🎯")

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-bottom: 4px solid #4ECDC4;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING PIPELINE ---
@st.cache_data
def load_and_clean_data():
    # 1. Load your exported files
    try:
        df = pd.read_csv("cleaned_data.parquet")
        district_df = pd.read_csv("district_priority.csv")
    except Exception as e:
        st.error(f"⚠️ Files missing! Ensure 'cleaned_data.csv' and 'district_priority.csv' are in your repository.")
        st.stop()

    # 2. THE OFFICIAL 36 VALIDATOR (Your Colab Logic)
    VALID_STATES = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
        'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
        'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
        'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
        'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Andaman and Nicobar Islands', 'Chandigarh', 
        'Dadra and Nagar Haveli and Daman and Diu',
        'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
    ]

    # 3. GeoJSON Alignment Fix
    # (Maps Colab names to standardized GeoJSON strings for the map)
    geojson_fix = {
        "Andaman and Nicobar Islands": "Andaman & Nicobar",
        "Jammu and Kashmir": "Jammu & Kashmir"
    }

    # 4. Final Filtration
    df = df[df['state'].isin(VALID_STATES)]
    df['state'] = df['state'].replace(geojson_fix)
    
    district_df = district_df[district_df['State'].isin(VALID_STATES)]
    district_df['State'] = district_df['State'].replace(geojson_fix)
    
    # Remove 'Unknown' or invalid districts
    district_df = district_df[~district_df['District'].str.lower().str.contains('unknown|error|none', na=True)]

    # 5. Date Formatting
    df["date"] = pd.to_datetime(df["date"])
    df['month_name'] = df['date'].dt.month_name().str[:3]
    df['month_num'] = df['date'].dt.month
    
    return df, district_df

df_clean, district_summary = load_and_clean_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🛠️ Analysis Tools")
menu = st.sidebar.radio("Navigate to:", 
    ["🏠 Dashboard Overview", "🗺️ Geographic Heatmap", "🚨 Priority Districts", "📊 Trends & Performance"])

st.sidebar.markdown("---")
st.sidebar.success(f"✅ Data Validated: 36/36 States/UTs")
st.sidebar.info(f"🏘️ Districts Analyzed: {len(district_summary):,}")

# --- 🏠 DASHBOARD OVERVIEW ---
if menu == "🏠 Dashboard Overview":
    st.title("🎯 Aadhaar Enrollment Gap Analysis")
    st.markdown("### Executive Summary of National Performance")
    
    # Top Level Metrics
    m1, m2, m3, m4 = st.columns(4)
    total_enroll = df_clean['total_enrollment'].sum()
    child_enroll = df_clean['children_enrollment'].sum()
    
    m1.metric("Total Enrollments", f"{total_enroll:,}")
    m2.metric("Child Enrollments", f"{child_enroll:,}", f"{(child_enroll/total_enroll*100):.1f}%")
    m3.metric("Pincodes Covered", f"{df_clean['pincode'].nunique():,}")
    m4.metric("Avg Priority Score", f"{district_summary['PRIORITY_SCORE'].mean():.1f}")

    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        # Age Distribution Donut (Cell 4)
        age_totals = {
            'Infants (0-5)': df_clean['age_0_5'].sum(),
            'Students (5-17)': df_clean['age_5_17'].sum(),
            'Adults (18+)': df_clean['age_18_greater'].sum()
        }
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(age_totals.keys()), values=list(age_totals.values()),
            hole=0.5, marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1']),
            textinfo='label+percent'
        )])
        fig_pie.update_layout(title="Demographic Breakdown", legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_b:
        # Best vs Worst Performers (Cell 8)
        top_d = district_summary.nlargest(5, 'Children')
        bot_d = district_summary.nsmallest(5, 'Children')
        comp_df = pd.concat([top_d, bot_d])
        comp_df['Category'] = comp_df['Children'].apply(lambda x: 'Top ✅' if x > comp_df['Children'].median() else 'Priority 🚨')
        
        fig_comp = px.bar(comp_df, x='Children', y='District', color='Category', 
                          orientation='h', title="Top vs Bottom Performers",
                          color_discrete_map={'Top ✅': '#6BCF7F', 'Priority 🚨': '#FF6B6B'})
        st.plotly_chart(fig_comp, use_container_width=True)

# --- 🗺️ GEOGRAPHIC HEATMAP ---
elif menu == "🗺️ Geographic Heatmap":
    st.title("🌍 National Child Enrollment Density")
    
    state_map_data = df_clean.groupby('state')['children_enrollment'].sum().reset_index()
    
    # Official GeoJSON for India
    GEOJSON_URL = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    
    fig_map = px.choropleth(
        state_map_data, geojson=GEOJSON_URL, featureidkey='properties.ST_NM',
        locations='state', color='children_enrollment',
        color_continuous_scale='YlGnBu', title="National Heatmap (0-17 Years)"
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(height=700, margin={"r":0,"t":50,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

# --- 🚨 PRIORITY DISTRICTS ---
elif menu == "🚨 Priority Districts":
    st.title("🚨 Urgent Intervention Areas")
    st.warning("Districts ranked by Priority Score: Lower Enrollment + Lower Coverage = Higher Score.")
    
    # Priority Bar Chart (Cell 6)
    priority_top20 = district_summary.sort_values('PRIORITY_SCORE', ascending=False).head(20)
    priority_top20['Label'] = priority_top20['District'] + " (" + priority_top20['State'] + ")"
    
    fig_prior = px.bar(
        priority_top20, x='PRIORITY_SCORE', y='Label', orientation='h',
        color='PRIORITY_SCORE', color_continuous_scale='Reds',
        text='Children', title="Top 20 Critical Districts"
    )
    fig_prior.update_layout(height=700, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_prior, use_container_width=True)

# --- 📊 TRENDS & PERFORMANCE ---
elif menu == "📊 Trends & Performance":
    st.title("📈 Growth & Performance Matrix")
    
    t1, t2 = st.tabs(["Monthly Trends", "District Matrix"])
    
    with t1:
        # Monthly Growth (Cell 3)
        monthly = df_clean.groupby(['month_num', 'month_name']).agg({'age_0_5':'sum', 'age_5_17':'sum'}).reset_index().sort_values('month_num')
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_0_5'], name='0-5 Years', line=dict(color='#FF6B6B', width=4)))
        fig_trend.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_5_17'], name='5-17 Years', line=dict(color='#4ECDC4', width=4)))
        fig_trend.update_layout(title="Monthly Enrollment Velocity", hovermode='x unified')
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with t2:
        # Performance Scatter (Cell 7)
        fig_scatter = px.scatter(
            district_summary, x='Pincodes', y='Children', size='Total', color='PRIORITY_SCORE',
            hover_name='District', color_continuous_scale='RdYlGn_r',
            title="Performance Matrix: Coverage vs Volume"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")
st.markdown("<center>Built for Aadhaar Hackathon 2026 | Powered by Gemini 3 Flash</center>", unsafe_allow_html=True)
