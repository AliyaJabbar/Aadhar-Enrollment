import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Aadhaar Enrollment Gap Analysis", 
    layout="wide", 
    page_icon="🎯",
    initial_sidebar_state="expanded" # Ensures navigation is visible on load
)

# --- PROFESSIONAL UI STYLING ---
st.markdown("""
    <style>
    /* Main background */
    .main { background-color: #fcfcfc; }
    
    /* Professional Insight Box */
    .insight-box { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #e0e0e0;
        border-left: 6px solid #2e7d32; 
        color: #000000; /* Strict black text */
        font-weight: 500;
        margin-top: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.02);
    }
    
    /* Metric styling */
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
    # Attempting to load files (Replace with your actual paths)
    try:
        df = pd.read_parquet("cleaned_data.parquet")
    except:
        # Fallback for demonstration - replace with actual loading logic
        df = pd.DataFrame() 
    
    district_df = pd.read_csv("district_priority.csv")
    
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
    
    district_df = district_df[district_df['State'].isin(ALL_VALID)]
    district_df['State_Map'] = district_df['State'].replace(geojson_map)
    district_df = district_df.sort_values(by=['PRIORITY_SCORE', 'District'], ascending=[False, True])

    df["date"] = pd.to_datetime(df["date"])
    df['month_name'] = df['date'].dt.month_name().str[:3]
    df['month_num'] = df['date'].dt.month

    return df, district_df

df_clean, district_summary = load_and_clean_data()

# --- SIDEBAR NAVIGATION (Ensured Visible) ---
with st.sidebar:
    st.title("📌 Menu")
    menu = st.radio("Switch View:", 
        ["📋 Executive Summary", "🗺️ National Heatmap", "🚨 Priority Districts", "📈 Enrollment Trends", "💫 Performance Matrix"])
    st.markdown("---")
    st.markdown("Created by: **Aliya Jabbar**")

# --- HEADER ---
st.title("Aadhaar Enrollment Gap Analysis")
st.caption("Strategic Intelligence Dashboard | Data Refresh 2026")

# --- 📋 SECTION 1: EXECUTIVE SUMMARY ---
if menu == "📋 Executive Summary":
    m1, m2, m3, m4 = st.columns(4)
    total_e = df_clean['total_enrollment'].sum()
    child_e = df_clean['children_enrollment'].sum()
    
    m1.metric("Total Enrollments", f"{total_e:,}")
    m2.metric("Child Enrollment", f"{child_e:,}", f"{(child_e/total_e*100):.1f}%")
    m3.metric("Pincodes Covered", f"{df_clean['pincode'].nunique():,}")
    m4.metric("Adult Baseline", f"{df_clean['age_18_greater'].sum():,}")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        age_totals = {'Age 0-5': df_clean['age_0_5'].sum(), 'Age 5-17': df_clean['age_5_17'].sum(), 'Age 18+': df_clean['age_18_greater'].sum()}
        fig3 = go.Figure(data=[go.Pie(labels=list(age_totals.keys()), values=list(age_totals.values()),
                                     hole=0.4, marker=dict(colors=['#1b5e20', '#4caf50', '#81c784']))])
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('<div class="insight-box">Strategic Observation: The demographic trend confirms that children (0-17) constitute the primary growth segment for new Aadhaar generation.</div>', unsafe_allow_html=True)

    with c2:
        top10_s = df_clean.groupby('state')['children_enrollment'].sum().nlargest(10).reset_index()
        fig1 = px.bar(top10_s, x='children_enrollment', y='state', orientation='h',
                      title="Top 10 States (Child Enrollment)", color='children_enrollment', color_continuous_scale='Greens')
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('<div class="insight-box">Operational Insight: Higher population states continue to lead in volume, necessitating sustained infrastructure in these regions.</div>', unsafe_allow_html=True)

# --- 🗺️ SECTION 2: NATIONAL HEATMAP (Red-Green Scale) ---
elif menu == "🗺️ National Heatmap":
    st.header("Geographic Enrollment Density")
    state_map_data = df_clean.groupby('state_for_map')['children_enrollment'].sum().reset_index()
    
    # Red to Green scale: Red (low) to Green (high)
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
    priority_top20 = district_summary.head(20).copy()
    priority_top20['label'] = priority_top20['District'] + ", " + priority_top20['State']
    
    fig5 = px.bar(priority_top20, x='PRIORITY_SCORE', y='label', orientation='h',
                  color='PRIORITY_SCORE', color_continuous_scale='Reds')
    fig5.update_layout(height=700, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown('<div class="insight-box">Immediate Action Required: The districts listed above exhibit the highest priority scores due to low saturation and limited service points.</div>', unsafe_allow_html=True)

# --- 📈 SECTION 4: ENROLLMENT TRENDS ---
elif menu == "📈 Enrollment Trends":
    st.header("Temporal Enrollment Analysis")
    monthly = df_clean.groupby(['month_num', 'month_name']).agg({'age_0_5':'sum', 'age_5_17':'sum'}).reset_index().sort_values('month_num')
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_0_5'], name='Age 0-5', line=dict(color='#d32f2f', width=4), mode='lines+markers'))
    fig2.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_5_17'], name='Age 5-17', line=dict(color='#388e3c', width=4), mode='lines+markers'))
    fig2.update_layout(title="Monthly Trends (Infant vs Juvenile)", hovermode='x unified')
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('<div class="insight-box">Cyclical Trend: Enrollment spikes often correlate with academic admission cycles, specifically in the 5-17 age bracket.</div>', unsafe_allow_html=True)

# --- 💫 SECTION 5: PERFORMANCE MATRIX (Red-Green Scale) ---
elif menu == "💫 Performance Matrix":
    st.header("District Efficiency Matrix")
    scatter_data = district_summary[(district_summary['Children'] > 0) & (district_summary['Pincodes'] > 0)].copy()
    
    # Priority score is Red-Green (High score = Red/High priority)
    fig6 = px.scatter(scatter_data, x='Pincodes', y='Children', size='Total', color='PRIORITY_SCORE',
                      hover_name='District', 
                      color_continuous_scale='RdYlGn_r', # Reversed: High priority (gap) is Red
                      size_max=40,
                      title="Enrollment Volume vs. Pincode Coverage")
    st.plotly_chart(fig6, use_container_width=True)
    
    st.markdown('<div class="insight-box">Performance Evaluation: High-priority clusters (Red) in the bottom-left represent critical infrastructure gaps, whereas Green clusters indicate healthy saturation.</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #757575;'>Aadhaar Enrollment Gap Analysis | 2026 | Created by Aliya Jabbar</p>", unsafe_allow_html=True)
