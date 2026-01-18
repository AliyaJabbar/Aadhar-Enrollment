import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Aadhaar Enrollment Analysis", layout="wide", page_icon="🎯")

# Custom CSS
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

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_data.csv")
    df["date"] = pd.to_datetime(df["date"])
    district_df = pd.read_csv("district_priority.csv")
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
     "🌍 Geographic Map", "📈 Trends", "💫 Performance Matrix"]
)

st.sidebar.markdown("---")
st.sidebar.info("📊 3.4M+ enrollments | 🗓️ Mar-Dec 2025")

# Overview Section
if selected_viz == "📋 Overview":
    st.header("📋 Executive Summary")
    col1, col2, col3, col4 = st.columns(4)
    total_enrollment = df_clean['total_enrollment'].sum()
    child_enrollment = df_clean['children_enrollment'].sum()
    child_pct = (child_enrollment / total_enrollment * 100)
    
    with col1: st.metric("Total Enrollments", f"{total_enrollment:,}")
    with col2: st.metric("Child Enrollments", f"{child_enrollment:,}", f"{child_pct:.1f}%")
    with col3: st.metric("States Covered", df_clean['state'].nunique())
    with col4: st.metric("Districts Analyzed", df_clean['district'].nunique())
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        age_totals = {
            'Age 0-5': int(df_clean['age_0_5'].sum()),
            'Age 5-17': int(df_clean['age_5_17'].sum()),
            'Age 18+': int(df_clean['age_18_greater'].sum())
        }
        fig = go.Figure(data=[go.Pie(labels=list(age_totals.keys()), values=list(age_totals.values()),
            hole=0.4, marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1']))])
        fig.update_layout(title='Age Distribution', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        top_states = df_clean.groupby('state')['children_enrollment'].sum().nlargest(5).reset_index()
        fig = px.bar(top_states, x='children_enrollment', y='state', orientation='h', 
                     title='Top 5 States', color='children_enrollment', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

# State Analysis
elif selected_viz == "🗺️ State Analysis":
    st.header("🗺️ State-wise Analysis")
    state_data = df_clean.groupby('state').agg({'children_enrollment': 'sum', 'total_enrollment': 'sum'}).reset_index()
    state_data = state_data.sort_values('children_enrollment', ascending=False)
    fig = px.bar(state_data.head(15), x='children_enrollment', y='state', orientation='h', title='Top 15 States')
    st.plotly_chart(fig, use_container_width=True)

# Priority Districts
elif selected_viz == "🚨 Priority Districts":
    st.header("🚨 Priority Districts Analysis")
    data_display = district_summary.head(20).copy()
    data_display['label'] = data_display['District'] + ', ' + data_display['State']
    fig = px.bar(data_display, y='label', x='PRIORITY_SCORE', orientation='h', 
                 title='Top 20 Priority Districts', color='PRIORITY_SCORE', color_continuous_scale='Reds')
    st.plotly_chart(fig, use_container_width=True)

# Geographic Map
elif selected_viz == "🌍 Geographic Map":
    st.header("🌍 Geographic Heatmap")
    state_map_data = df_clean.groupby('state').agg({'children_enrollment': 'sum'}).reset_index()
    fig = px.choropleth(
        state_map_data,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        featureidkey='properties.ST_NM', locations='state', color='children_enrollment',
        color_continuous_scale='RdYlGn', title='State-wise Enrollment'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, use_container_width=True)

# Trends
elif selected_viz == "📈 Trends":
    st.header("📈 Enrollment Trends")
    monthly_data = df_clean.groupby('month').agg({'age_0_5': 'sum', 'age_5_17': 'sum', 'age_18_greater': 'sum'}).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly_data['month'], y=monthly_data['age_0_5'], name='Age 0-5'))
    fig.add_trace(go.Scatter(x=monthly_data['month'], y=monthly_data['age_5_17'], name='Age 5-17'))
    fig.update_layout(title='Monthly Trends', hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

# Performance Matrix
elif selected_viz == "💫 Performance Matrix":
    st.header("💫 District Performance Analysis")
    fig = px.scatter(district_summary, x='Pincodes', y='Children', size='Total',
                     color='PRIORITY_SCORE', hover_name='District', title='Performance Matrix')
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Built with Streamlit & Plotly | 2026</div>", unsafe_allow_html=True)
