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

# --- PROFESSIONAL UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    
    /* Updated Insight Box: Light Violet Theme */
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
    # Loading logic (Replace with your actual paths)
    try:
        df = pd.read_parquet("cleaned_data.parquet")
    except:
        df = pd.DataFrame() 
    
    try:
        district_df = pd.read_csv("district_priority.csv")
    except:
        district_df = pd.DataFrame()

    ALL_VALID = [
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
    
    geojson_map = {"Andaman and Nicobar Islands": "Andaman & Nicobar", "Jammu and Kashmir": "Jammu & Kashmir"}

    df['state'] = df['state'].str.strip()
    df = df[df['state'].isin(ALL_VALID)]
    df['state_for_map'] = df['state'].replace(geojson_map)
    
    if not district_df.empty:
        district_df = district_df[district_df['State'].isin(ALL_VALID)]
        district_df['State_Map'] = district_df['State'].replace(geojson_map)

    df["date"] = pd.to_datetime(df["date"])
    df['month_num'] = df['date'].dt.month
    df['month_name'] = df['date'].dt.month_name().str[:3]

    return df, district_df

df_clean, district_summary = load_and_clean_data()

# --- SIDEBAR: FILTERS & NAVIGATION ---
with st.sidebar:
    st.title("📌 Dashboard Controls")
    menu = st.radio("Switch View:", 
        ["📋 Executive Summary", "🗺️ National Heatmap", "🚨 Priority Districts", "📈 Enrollment Trends", "💫 Performance Matrix"])
    
    st.markdown("---")
    st.subheader("Interactive Filters")

    # 1. Date Range Filter
    min_date = df_clean['date'].min().date()
    max_date = df_clean['date'].max().date()
    selected_dates = st.date_input("Date Range", [min_date, max_date])

    # 2. State Filter with Select All
    all_states = sorted(df_clean['state'].unique())
    select_all_states = st.checkbox("Select All States", value=True)
    if select_all_states:
        selected_states = all_states
    else:
        selected_states = st.multiselect("Select Specific States", all_states)

    # 3. District Filter (Conditional)
    relevant_districts = sorted(df_clean[df_clean['state'].isin(selected_states)]['District'].unique())
    select_all_districts = st.checkbox("Select All Districts", value=True)
    if select_all_districts:
        selected_districts = relevant_districts
    else:
        selected_districts = st.multiselect("Select Specific Districts", relevant_districts)

    st.markdown("---")
    st.markdown("Created by: **Aliya Jabbar**")

# --- APPLY FILTERS TO DATA ---
if len(selected_dates) == 2:
    start_date, end_date = pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1])
    mask = (
        (df_clean['state'].isin(selected_states)) & 
        (df_clean['District'].isin(selected_districts)) &
        (df_clean['date'] >= start_date) & 
        (df_clean['date'] <= end_date)
    )
    df_final = df_clean.loc[mask]
    
    # Filter district summary based on state/district selection
    dist_final = district_summary[
        (district_summary['State'].isin(selected_states)) & 
        (district_summary['District'].isin(selected_districts))
    ]
else:
    df_final = df_clean.copy()
    dist_final = district_summary.copy()

# --- HEADER ---
st.title("Aadhaar Enrollment Gap Analysis")
st.caption(f"Strategic Intelligence Dashboard | View: {menu} | Data Refresh 2026")

# --- 📋 SECTION 1: EXECUTIVE SUMMARY ---
if menu == "📋 Executive Summary":
    m1, m2, m3, m4 = st.columns(4)
    total_e = df_final['total_enrollment'].sum()
    child_e = df_final['children_enrollment'].sum()
    
    m1.metric("Total Enrollments", f"{total_e:,}")
    m2.metric("Child Enrollment", f"{child_e:,}", f"{(child_e/total_e*100 if total_e > 0 else 0):.1f}%")
    m3.metric("Pincodes Covered", f"{df_final['pincode'].nunique():,}")
    m4.metric("Active States", f"{df_final['state'].nunique():,}")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        age_totals = {
            'Age 0-5': df_final['age_0_5'].sum(), 
            'Age 5-17': df_final['age_5_17'].sum(), 
            'Age 18+': df_final['age_18_greater'].sum()
        }
        # Multi-color Pie Chart
        fig3 = px.pie(
            names=list(age_totals.keys()), 
            values=list(age_totals.values()),
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig3.update_layout(title="Demographic Enrollment Share")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('<div class="insight-box">Strategic Observation: The demographic trend confirms that children (0-17) constitute the primary growth segment for new Aadhaar generation.</div>', unsafe_allow_html=True)

    with c2:
        top_s = df_final.groupby('state')['children_enrollment'].sum().nlargest(10).reset_index()
        fig1 = px.bar(top_s, x='children_enrollment', y='state', orientation='h',
                      title="Top States (Child Enrollment)", color='children_enrollment', color_continuous_scale='Purples')
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('<div class="insight-box">Operational Insight: Higher population states continue to lead in volume, necessitating sustained infrastructure in these regions.</div>', unsafe_allow_html=True)

# --- 🗺️ SECTION 2: NATIONAL HEATMAP ---
elif menu == "🗺️ National Heatmap":
    st.header("Geographic Enrollment Density")
    state_map_data = df_final.groupby('state_for_map')['children_enrollment'].sum().reset_index()
    
    fig4 = px.choropleth(
        state_map_data,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        featureidkey='properties.ST_NM',
        locations='state_for_map',
        color='children_enrollment',
        color_continuous_scale='RdYlGn', 
        title="India State-wise Distribution"
    )
    fig4.update_geos(fitbounds="locations", visible=False)
    fig4.update_layout(height=700)
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('<div class="insight-box">Geospatial Analysis: Areas highlighted in red indicate high-gap zones where enrollment center density is insufficient compared to the population.</div>', unsafe_allow_html=True)

# --- 🚨 SECTION 3: PRIORITY DISTRICTS ---
elif menu == "🚨 Priority Districts":
    st.header("Priority Action Zones")
    priority_top = dist_final.sort_values('PRIORITY_SCORE', ascending=False).head(20)
    priority_top['label'] = priority_top['District'] + ", " + priority_top['State']
    
    fig5 = px.bar(priority_top, x='PRIORITY_SCORE', y='label', orientation='h',
                  color='PRIORITY_SCORE', color_continuous_scale='Reds')
    fig5.update_layout(height=700, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown('<div class="insight-box">Immediate Action Required: The districts listed above exhibit the highest priority scores due to low saturation and limited service points.</div>', unsafe_allow_html=True)

# --- 📈 SECTION 4: ENROLLMENT TRENDS ---
elif menu == "📈 Enrollment Trends":
    st.header("Temporal Enrollment Analysis")
    # Group by date for more granular time filtering
    trend_data = df_final.groupby('date').agg({'age_0_5':'sum', 'age_5_17':'sum'}).reset_index()
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=trend_data['date'], y=trend_data['age_0_5'], name='Age 0-5', line=dict(color='#7b1fa2', width=3)))
    fig2.add_trace(go.Scatter(x=trend_data['date'], y=trend_data['age_5_17'], name='Age 5-17', line=dict(color='#ab47bc', width=3)))
    fig2.update_layout(title="Daily Enrollment Trends", hovermode='x unified')
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('<div class="insight-box">Temporal Analysis: Reviewing trends over the selected date range helps identify sudden spikes or drops in registration activity.</div>', unsafe_allow_html=True)

# --- 💫 SECTION 5: PERFORMANCE MATRIX ---
elif menu == "💫 Performance Matrix":
    st.header("District Efficiency Matrix")
    # Using filtered data for the scatter plot
    fig6 = px.scatter(dist_final, x='Pincodes', y='Children', size='Total', color='PRIORITY_SCORE',
                      hover_name='District', 
                      color_continuous_scale='RdYlGn_r', 
                      size_max=40,
                      title="Enrollment Volume vs. Pincode Coverage")
    st.plotly_chart(fig6, use_container_width=True)
    st.markdown('<div class="insight-box">Performance Evaluation: High-priority clusters (Red) represent critical infrastructure gaps, whereas Green clusters indicate healthy saturation.</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #757575;'>Aadhaar Enrollment Gap Analysis | 2026 | Created by Aliya Jabbar</p>", unsafe_allow_html=True)
