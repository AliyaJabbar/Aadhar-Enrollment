import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Aadhaar Enrollment Analysis", layout="wide", page_icon="🎯")

# Custom CSS for UI
st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("🎯 Aadhaar Enrollment Gap Analysis Dashboard")
st.markdown("### AI-Powered Priority District Identification System")
st.markdown("---")

# Load and Clean Data
@st.cache_data
def load_data():
    # 1. Load data
    df = pd.read_parquet("cleaned_data.parquet")
    district_df = pd.read_csv("district_priority.csv")
    
    # 2. FIX STATE NAMES (The "47 states" fix)
    df['state'] = df['state'].astype(str).str.strip().str.title()
    corrections = {
        "Nct Of Delhi": "Delhi",
        "Odisha": "Odisha", "Orissa": "Odisha",
        "Andaman And Nicobar Islands": "Andaman & Nicobar Islands",
        "Telengana": "Telangana"
    }
    df['state'] = df['state'].replace(corrections)
    
    # 3. Handle dates & Month mapping
    df["date"] = pd.to_datetime(df["date"])
    month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
                   7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
    df['month_name'] = df['month'].map(month_names)
    
    # 4. Remove Unknowns
    df = df[~df['state'].str.isdigit()]
    df = df[df['state'] != "Unknown"]
    district_df = district_df[district_df['District'].str.lower() != 'unknown']
    
    return df, district_df

try:
    df_clean, district_summary = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar
st.sidebar.header("📊 Dashboard Controls")
selected_viz = st.sidebar.selectbox(
    "Select Visualization:",
    ["📋 Overview", "🗺️ State Analysis", "🚨 Priority Districts", 
     "🌍 Geographic Map", "📈 Trends", "💫 Performance Matrix", "🏆 Best vs Worst"]
)

st.sidebar.markdown("---")
st.sidebar.info(f"📊 {len(df_clean):,} Records | 🗓️ Mar-Dec 2025")

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
        age_totals = {'Age 0-5': df_clean['age_0_5'].sum(), 'Age 5-17': df_clean['age_5_17'].sum(), 'Age 18+': df_clean['age_18_greater'].sum()}
        fig_pie = go.Figure(data=[go.Pie(labels=list(age_totals.keys()), values=list(age_totals.values()), hole=0.4, marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1']))])
        fig_pie.update_layout(title="Age Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_r:
        # Mini Top 5
        top5 = df_clean.groupby('state')['children_enrollment'].sum().nlargest(5).reset_index()
        fig_top5 = px.bar(top5, x='children_enrollment', y='state', orientation='h', title="Top 5 States", color='children_enrollment', color_continuous_scale='Viridis')
        fig_top5.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top5, use_container_width=True)

# --- 🗺️ STATE ANALYSIS (Sorted Desc) ---
elif selected_viz == "🗺️ State Analysis":
    st.header("📊 Top 15 States by Child Enrollment")
    state_data = df_clean.groupby('state').agg({'children_enrollment': 'sum'}).reset_index()
    state_data = state_data.sort_values('children_enrollment', ascending=False).head(15)
    
    fig = px.bar(state_data, x='children_enrollment', y='state', orientation='h',
                 color='children_enrollment', color_continuous_scale='Blues', text='children_enrollment')
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    # Use 'total ascending' in yaxis to ensure the largest bar is at the TOP
    fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

# --- 🚨 PRIORITY DISTRICTS ---
elif selected_viz == "🚨 Priority Districts":
    st.header("🚨 Top 20 Priority Districts")
    priority_top20 = district_summary.sort_values('PRIORITY_SCORE', ascending=False).head(20).copy()
    priority_top20['label'] = priority_top20['District'] + ', ' + priority_top20['State']
    
    fig = px.bar(priority_top20, y='label', x='PRIORITY_SCORE', orientation='h', 
                 color='PRIORITY_SCORE', color_continuous_scale='Reds', text='Children')
    fig.update_traces(texttemplate='%{text} children', textposition='outside')
    fig.update_layout(height=700, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

# --- 📈 TRENDS ---
elif selected_viz == "📈 Trends":
    st.header("📈 Monthly Enrollment Trends")
    monthly = df_clean.groupby(['month', 'month_name']).agg({'age_0_5':'sum', 'age_5_17':'sum', 'age_18_greater':'sum'}).reset_index().sort_values('month')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_0_5'], name='Age 0-5', line=dict(color='#FF6B6B', width=3)))
    fig.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_5_17'], name='Age 5-17', line=dict(color='#4ECDC4', width=3)))
    fig.update_layout(hovermode='x unified', title="Enrollment over Time")
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"🔍 **Key Insight:** September recorded the highest activity with {monthly['age_0_5'].max():,} infant enrollments.")

# --- 💫 PERFORMANCE MATRIX ---
elif selected_viz == "💫 Performance Matrix":
    st.header("💫 District Performance Analysis")
    scatter_data = district_summary[(district_summary['Children'] > 10) & (district_summary['Pincodes'] > 2)].copy()
    fig = px.scatter(scatter_data, x='Pincodes', y='Children', size='Total', color='PRIORITY_SCORE', 
                     hover_name='District', color_continuous_scale='RdYlGn_r',
                     labels={'Pincodes': 'Active Pincodes', 'Children': 'Child Enrollment'})
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
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=700)
    st.plotly_chart(fig, use_container_width=True)

# --- 🌍 GEOGRAPHIC MAP ---
elif selected_viz == "🌍 Geographic Map":
    st.header("🌍 National Heatmap")
    state_map = df_clean.groupby('state')['children_enrollment'].sum().reset_index()
    fig = px.choropleth(state_map, 
                        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
                        featureidkey='properties.ST_NM', locations='state', color='children_enrollment', color_continuous_scale='RdYlGn')
    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Built for Aadhaar Hackathon 2026</div>", unsafe_allow_html=True)
