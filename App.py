import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Aadhaar Strategic Gap Analysis", 
    layout="wide", 
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# --- PROFESSIONAL VIOLET UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .insight-box { 
        background-color: #f3e5f5; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 6px solid #7b1fa2; 
        color: #2c003e;
        font-weight: 500;
        margin-top: 15px;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #f0f0f0;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data
def load_and_clean_data():
    # Replace the following with your actual data loading:
    # df = pd.read_parquet("cleaned_data.parquet")
    
    # FOR DEMONSTRATION: Creating a robust mock dataset
    ALL_STATES = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
        'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
        'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
        'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
        'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Andaman and Nicobar Islands', 'Chandigarh', 'Delhi', 'Jammu and Kashmir', 
        'Ladakh', 'Lakshadweep', 'Puducherry'
    ]
    
    # Generating dummy data for all states to show filters working
    data = []
    for state in ALL_STATES:
        for i in range(1, 4): # 3 districts per state
            data.append({
                'state': state,
                'District': f"{state} Dist_{i}",
                'total_enrollment': 5000 + (i * 100),
                'children_enrollment': 2000 + (i * 50),
                'age_0_5': 800, 'age_5_17': 1200, 'age_18_greater': 3000,
                'pincode': 1000 + i,
                'date': pd.to_datetime('2025-12-01') + pd.DateOffset(days=i*10),
                'PRIORITY_SCORE': 40 + (i * 10)
            })
    
    df = pd.DataFrame(data)
    df['state_for_map'] = df['state'].replace({"Andaman and Nicobar Islands": "Andaman & Nicobar", "Jammu and Kashmir": "Jammu & Kashmir"})
    df['month_year'] = df['date'].dt.strftime('%b %Y')
    return df

df_raw = load_and_clean_data()

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.title("🎯 Global Filters")
    menu = st.radio("View Dashboard:", 
        ["📋 Executive Summary", "🗺️ National Heatmap", "🚨 Priority Districts", "📈 Enrollment Trends", "💫 Performance Matrix"])
    
    st.markdown("---")
    
    # 1. Date Filter
    min_date = df_raw['date'].min().date()
    max_date = df_raw['date'].max().date()
    selected_date_range = st.date_input("Select Date Range", [min_date, max_date])

    # 2. State Multi-select (Select All logic)
    all_states = sorted(df_raw['state'].unique())
    select_all_states = st.checkbox("Select All States", value=True)
    if select_all_states:
        selected_states = all_states
    else:
        selected_states = st.multiselect("Pick States", all_states)

    # 3. District Multi-select
    relevant_districts = sorted(df_raw[df_raw['state'].isin(selected_states)]['District'].unique())
    select_all_districts = st.checkbox("Select All Districts", value=True)
    if select_all_districts:
        selected_districts = relevant_districts
    else:
        selected_districts = st.multiselect("Pick Districts", relevant_districts)

# --- APPLY GLOBAL FILTERS ---
mask = (
    (df_raw['state'].isin(selected_states)) & 
    (df_raw['District'].isin(selected_districts)) &
    (df_raw['date'].dt.date >= selected_date_range[0]) &
    (df_raw['date'].dt.date <= selected_date_range[1])
)
df_final = df_raw.loc[mask]

# --- DASHBOARD PAGES ---
st.title("Aadhaar Enrollment Gap Analysis")

if df_final.empty:
    st.warning("No data found for the selected filters. Please adjust your selection in the sidebar.")
else:
    if menu == "📋 Executive Summary":
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Enrollments", f"{df_final['total_enrollment'].sum():,}")
        m2.metric("Children", f"{df_final['children_enrollment'].sum():,}")
        m3.metric("Pincodes", f"{df_final['pincode'].nunique():,}")
        m4.metric("States", f"{df_final['state'].nunique():,}")

        c1, c2 = st.columns(2)
        with c1:
            # Multi-color Pie Chart
            age_data = pd.DataFrame({
                'Group': ['Infants (0-5)', 'Juveniles (5-17)', 'Adults (18+)'],
                'Value': [df_final['age_0_5'].sum(), df_final['age_5_17'].sum(), df_final['age_18_greater'].sum()]
            })
            fig = px.pie(age_data, names='Group', values='Value', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown('<div class="insight-box"><b>Strategic Summary:</b> Based on selected filters, child enrollment remains the highest priority for operational scaling.</div>', unsafe_allow_html=True)

    elif menu == "🗺️ National Heatmap":
        map_data = df_final.groupby('state_for_map')['total_enrollment'].sum().reset_index()
        fig = px.choropleth(
            map_data,
            geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
            featureidkey='properties.ST_NM',
            locations='state_for_map',
            color='total_enrollment',
            color_continuous_scale='Purples'
        )
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box"><b>Geographic Focus:</b> Violet zones represent areas with maximum enrollment activity within your selected date range.</div>', unsafe_allow_html=True)

    elif menu == "🚨 Priority Districts":
        p_data = df_final.groupby(['state', 'District'])['PRIORITY_SCORE'].mean().reset_index().nlargest(15, 'PRIORITY_SCORE')
        fig = px.bar(p_data, x='PRIORITY_SCORE', y='District', color='PRIORITY_SCORE', 
                     color_continuous_scale='RdPu', orientation='h', title="Top Districts Requiring Attention")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box"><b>Critical Action:</b> These districts show the highest gap scores based on current filters.</div>', unsafe_allow_html=True)

    elif menu == "📈 Enrollment Trends":
        trend_data = df_final.groupby(df_final['date'].dt.date)[['age_0_5', 'age_5_17']].sum().reset_index()
        fig = px.line(trend_data, x='date', y=['age_0_5', 'age_5_17'], 
                      title="Daily Enrollment Trends", color_discrete_sequence=['#9c27b0', '#e91e63'])
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box"><b>Temporal Analysis:</b> Fluctuations above represent changes over the selected date range.</div>', unsafe_allow_html=True)

    elif menu == "💫 Performance Matrix":
        fig = px.scatter(df_final, x='pincode', y='total_enrollment', size='children_enrollment', 
                         color='state', hover_name='District', title="District Saturation vs Volume")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box"><b>Efficiency Matrix:</b> Larger bubbles represent higher child enrollment concentrations.</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #757575;'>Data Refresh: Jan 2026 | Created by Aliya Jabbar</p>", unsafe_allow_html=True)
