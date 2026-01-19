import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Aadhaar Enrollment Analysis", layout="wide", page_icon="🎯")

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #4ECDC4;
    }
    .stHeader { color: #2c3e50; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING & CLEANING PIPELINE ---
@st.cache_data
def load_data():
    # 1. Load data (Supports both Parquet and CSV for GitHub flexibility)
    try:
        df = pd.read_parquet("cleaned_data.parquet")
    except:
        df = pd.read_csv("cleaned_data.csv")
        
    district_df = pd.read_csv("district_priority.csv")
    
    # 2. STANDARDIZE STATE NAMES (Fixing GeoJSON Mismatches)
    df['state'] = df['state'].astype(str).str.strip().str.title()
    
    # Mapping to match jbrobst India GeoJSON exactly
    corrections = {
        "Nct Of Delhi": "Delhi",
        "Arunachal Pradesh": "Arunachal Pradesh",
        "Andaman And Nicobar Islands": "Andaman & Nicobar",
        "Jammu And Kashmir": "Jammu & Kashmir",
        "Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
        "Odisha": "Odisha", "Orissa": "Odisha",
        "Telengana": "Telangana",
        "Pondicherry": "Puducherry"
    }
    df['state'] = df['state'].replace(corrections)
    
    # 3. Handle dates & Month mapping
    df["date"] = pd.to_datetime(df["date"])
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df['month_name'] = df['date'].dt.month_name().str[:3]
    df['month_num'] = df['date'].dt.month
    
    # 4. Remove Data Errors/Unknowns
    df = df[~df['state'].str.isdigit()]
    df = df[df['state'] != "Unknown"]
    district_df = district_df[district_df['District'].str.lower() != 'unknown']
    
    return df, district_df

# Load datasets
try:
    df_clean, district_summary = load_data()
except Exception as e:
    st.error(f"⚠️ Error loading data. Ensure 'cleaned_data.csv' and 'district_priority.csv' are in your GitHub repo. Error: {e}")
    st.stop()

# --- SIDEBAR NAV ---
st.sidebar.title("🚀 Navigation")
selected_viz = st.sidebar.radio(
    "Select Analysis View:",
    ["📋 Overview", "🗺️ State Ranking", "🚨 Priority Districts", 
     "🌍 National Heatmap", "📈 Growth Trends", "💫 Performance Matrix", "🏆 Best vs Worst"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Download Reports")
csv = district_summary.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("Download Priority CSV", data=csv, file_name="aadhaar_priority_list.csv", mime="text/csv")

# --- DASHBOARD HEADER ---
st.title("🎯 Aadhaar Enrollment Gap Analysis")
st.markdown(f"**Geographic Scope:** {df_clean['state'].nunique()} States/UTs | **Timeframe:** 2025")

# --- 📋 OVERVIEW SECTION ---
if selected_viz == "📋 Overview":
    st.header("📋 Executive Summary")
    col1, col2, col3, col4 = st.columns(4)
    total = df_clean['total_enrollment'].sum()
    child = df_clean['children_enrollment'].sum()
    
    with col1: st.metric("Total Enrollments", f"{total:,}")
    with col2: st.metric("Child Enrollments", f"{child:,}", f"{(child/total*100):.1f}%")
    with col3: st.metric("States/UTs Covered", df_clean['state'].nunique())
    with col4: st.metric("Districts Analyzed", df_clean['district'].nunique())

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        # Age Distribution Donut
        age_totals = {'Infants (0-5)': df_clean['age_0_5'].sum(), 'Students (5-17)': df_clean['age_5_17'].sum(), 'Adults (18+)': df_clean['age_18_greater'].sum()}
        fig_pie = go.Figure(data=[go.Pie(labels=list(age_totals.keys()), values=list(age_totals.values()), hole=0.5, marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1']))])
        fig_pie.update_layout(title="Demographic Breakdown", legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_r:
        # Top 5 States
        top5 = df_clean.groupby('state')['children_enrollment'].sum().nlargest(5).reset_index()
        fig_top5 = px.bar(top5, x='children_enrollment', y='state', orientation='h', title="Top 5 Performing States", color='children_enrollment', color_continuous_scale='Viridis')
        fig_top5.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top5, use_container_width=True)

# --- 🗺️ STATE RANKING ---
elif selected_viz == "🗺️ State Ranking":
    st.header("📊 State-wise Child Enrollment")
    state_data = df_clean.groupby('state').agg({'children_enrollment': 'sum'}).reset_index().sort_values('children_enrollment', ascending=False).head(15)
    
    fig = px.bar(state_data, x='children_enrollment', y='state', orientation='h',
                 color='children_enrollment', color_continuous_scale='Blues', text='children_enrollment')
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'}, xaxis_title="Enrollments")
    st.plotly_chart(fig, use_container_width=True)

# --- 🚨 PRIORITY DISTRICTS ---
elif selected_viz == "🚨 Priority Districts":
    st.header("🚨 Top 20 Priority Districts")
    st.info("Priority is calculated based on Low Enrollment + Low Coverage + Low Record Activity.")
    priority_top20 = district_summary.sort_values('PRIORITY_SCORE', ascending=False).head(20).copy()
    priority_top20['label'] = priority_top20['District'] + ', ' + priority_top20['State']
    
    fig = px.bar(priority_top20, y='label', x='PRIORITY_SCORE', orientation='h', 
                 color='PRIORITY_SCORE', color_continuous_scale='Reds', text='Children')
    fig.update_traces(texttemplate='%{text} enrollments', textposition='outside')
    fig.update_layout(height=700, yaxis={'categoryorder':'total ascending'}, xaxis_title="Priority Score (Higher = More Urgent)")
    st.plotly_chart(fig, use_container_width=True)

# --- 📈 TRENDS ---
elif selected_viz == "📈 Trends":
    st.header("📈 Temporal Enrollment Trends")
    monthly = df_clean.groupby(['month_num', 'month_name']).agg({'age_0_5':'sum', 'age_5_17':'sum'}).reset_index().sort_values('month_num')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_0_5'], name='Infants (0-5)', line=dict(color='#FF6B6B', width=4), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_5_17'], name='Students (5-17)', line=dict(color='#4ECDC4', width=4), mode='lines+markers'))
    fig.update_layout(hovermode='x unified', title="Enrollment Growth (2025)")
    st.plotly_chart(fig, use_container_width=True)
    st.success(f"💡 **Peak Activity:** Analysis shows September as the highest enrollment month.")

# --- 💫 PERFORMANCE MATRIX ---
elif selected_viz == "💫 Performance Matrix":
    st.header("💫 District Performance Analysis")
    # Filtering outliers for better visualization
    scatter_data = district_summary[(district_summary['Children'] > 0) & (district_summary['Pincodes'] > 0)].copy()
    
    fig = px.scatter(scatter_data, x='Pincodes', y='Children', size='Total', color='PRIORITY_SCORE', 
                     hover_name='District', color_continuous_scale='RdYlGn_r', size_max=40,
                     labels={'Pincodes': 'Active Pincodes', 'Children': 'Child Enrollment'},
                     title="Child Enrollment vs. Geographic Coverage")
    st.plotly_chart(fig, use_container_width=True)

# --- 🏆 BEST VS WORST ---
elif selected_viz == "🏆 Best vs Worst":
    st.header("🏆 High Performers vs Priority Gaps")
    top10 = district_summary.nlargest(10, 'Children').copy()
    bot10 = district_summary.nsmallest(10, 'Children').copy()
    top10['Category'] = 'Top Performers ✅'
    bot10['Category'] = 'Priority Districts 🚨'
    
    comparison = pd.concat([top10, bot10])
    comparison['label'] = comparison['District'] + ', ' + comparison['State']
    
    fig = px.bar(comparison, x='Children', y='label', color='Category', orientation='h',
                 color_discrete_map={'Top Performers ✅': '#6BCF7F', 'Priority Districts 🚨': '#FF6B6B'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=700, xaxis_title="Enrollment Count")
    st.plotly_chart(fig, use_container_width=True)

# --- 🌍 GEOGRAPHIC MAP ---
elif selected_viz == "🌍 Geographic Map":
    st.header("🌍 National Heatmap")
    state_map = df_clean.groupby('state')['children_enrollment'].sum().reset_index()
    
    # India GeoJSON standard
    GEOJSON_URL = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    
    fig = px.choropleth(
        state_map, 
        geojson=GEOJSON_URL,
        featureidkey='properties.ST_NM', 
        locations='state', 
        color='children_enrollment', 
        color_continuous_scale='YlGnBu',
        title="National Child Enrollment Density"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=800, margin={"r":0,"t":50,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Built for Aadhaar Hackathon 2026 | Powered by Streamlit</div>", unsafe_allow_html=True)
