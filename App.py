import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Aadhaar Analytics Pro | 2026",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# --- PROFESSIONAL STYLING ---
st.markdown("""
    <style>
    /* Main background and font */
    .main { background-color: #f4f7f9; font-family: 'Inter', sans-serif; }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: transform 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }
    
    /* Insight Boxes */
    .insight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-top: 10px;
        font-weight: 400;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE (Optimized) ---
@st.cache_data
def load_and_clean_data():
    # Placeholder for your data loading logic
    # In a real app, ensure 'cleaned_data.parquet' is optimized
    try:
        df = pd.read_parquet("cleaned_data.parquet")
    except:
        # Mock data generation for demonstration if file not found
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

# --- SIDEBAR & FILTERS ---
with st.sidebar:
    st.image("https://uidai.gov.in/images/logo_uidai3.png", width=100)
    st.title("Strategic Oversight")
    
    menu = st.radio("DASHBOARD VIEW", 
                    ["📋 Executive Summary", "🗺️ National Heatmap", "🚨 Priority Districts", "📈 Enrollment Trends", "💫 Performance Matrix"],
                    index=0)
    
    st.markdown("---")
    st.subheader("Global Filters")
    selected_state = st.multiselect("Focus States", options=sorted(df_clean['state'].unique()), default=None, placeholder="All India")
    
    if selected_state:
        df_filtered = df_clean[df_clean['state'].isin(selected_state)]
    else:
        df_filtered = df_clean

# --- TOP HEADER ---
st.markdown(f"## {menu}")
st.caption(f"Last Updated: {datetime.now().strftime('%d %B %Y')} | System Status: Active")

# --- 📋 SECTION 1: EXECUTIVE SUMMARY ---
if menu == "📋 Executive Summary":
    # Key Performance Indicators
    total_e = df_filtered['total_enrollment'].sum()
    child_e = df_filtered['children_enrollment'].sum()
    pincodes = df_filtered['pincode'].nunique()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Gross Enrollments", f"{total_e:,}", help="Total Aadhaar generated")
    kpi2.metric("Child Saturation", f"{child_e:,}", f"{(child_e/total_e*100):.1f}%")
    kpi3.metric("Service Points", f"{pincodes:,}", "Unique Pincodes")
    kpi4.metric("Adult Baseline", f"{df_filtered['age_18_greater'].sum():,}")

    st.markdown("### Regional Performance")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        age_totals = {'Infants (0-5)': df_filtered['age_0_5'].sum(), 'Juveniles (5-17)': df_filtered['age_5_17'].sum(), 'Adults (18+)': df_filtered['age_18_greater'].sum()}
        fig3 = go.Figure(data=[go.Pie(labels=list(age_totals.keys()), values=list(age_totals.values()),
                                     hole=0.6, marker=dict(colors=['#3b82f6', '#60a5fa', '#93c5fd']))])
        fig3.update_layout(margin=dict(t=0, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=-0.1))
        st.plotly_chart(fig3, use_container_width=True)

    with c2:
        top10_s = df_filtered.groupby('state')['children_enrollment'].sum().nlargest(10).reset_index()
        fig1 = px.bar(top10_s, x='children_enrollment', y='state', orientation='h',
                      color='children_enrollment', color_continuous_scale='Blues')
        fig1.update_layout(margin=dict(t=0, b=0, l=0, r=0), coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)

    st.markdown("""
        <div class="insight-card">
        <b>Strategic Intelligence:</b> Data indicates a heavy skew towards the 5-17 demographic. 
        Recommended action: Pivot resources toward 0-5 'Bal Aadhaar' camps in low-performing districts.
        </div>
        """, unsafe_allow_html=True)

# --- 🗺️ SECTION 2: NATIONAL HEATMAP ---
elif menu == "🗺️ National Heatmap":
    st.info("Interactive Map: Hover to see specific state metrics.")
    state_map_data = df_clean.groupby('state_for_map')['children_enrollment'].sum().reset_index()
    
    fig4 = px.choropleth(
        state_map_data,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        featureidkey='properties.ST_NM',
        locations='state_for_map',
        color='children_enrollment',
        color_continuous_scale='GnBu',
        template="plotly_white"
    )
    fig4.update_geos(fitbounds="locations", visible=False)
    fig4.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
    st.plotly_chart(fig4, use_container_width=True)

# --- 🚨 SECTION 3: PRIORITY DISTRICTS ---
elif menu == "🚨 Priority Districts":
    st.markdown("#### High-Urgency Deployment Zones")
    
    priority_top20 = district_summary.head(20).copy()
    priority_top20['label'] = priority_top20['District'] + " (" + priority_top20['State'] + ")"
    
    fig5 = px.bar(priority_top20, x='PRIORITY_SCORE', y='label', orientation='h',
                  color='PRIORITY_SCORE', color_continuous_scale='Reds',
                  labels={'PRIORITY_SCORE': 'Urgency Index', 'label': 'District'})
    fig5.update_layout(yaxis={'categoryorder':'total ascending'}, height=600, showlegend=False)
    st.plotly_chart(fig5, use_container_width=True)
    
    # Professional Table View
    with st.expander("View Full Raw Priority Data"):
        st.dataframe(district_summary, use_container_width=True)

# --- 📈 SECTION 4: ENROLLMENT TRENDS ---
elif menu == "📈 Enrollment Trends":
    monthly = df_filtered.groupby(['month_num', 'month_name']).agg({'age_0_5':'sum', 'age_5_17':'sum'}).reset_index().sort_values('month_num')
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_0_5'], name='Infants (0-5)', line=dict(color='#3b82f6', width=3), mode='lines+markers'))
    fig2.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_5_17'], name='Juveniles (5-17)', line=dict(color='#10b981', width=3), mode='lines+markers'))
    
    fig2.update_layout(
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#e1e4e8')
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- 💫 SECTION 5: PERFORMANCE MATRIX ---
elif menu == "💫 Performance Matrix":
    scatter_data = district_summary[(district_summary['Children'] > 0) & (district_summary['Pincodes'] > 0)].copy()
    
    fig6 = px.scatter(scatter_data, x='Pincodes', y='Children', size='Total', color='PRIORITY_SCORE',
                      hover_name='District', color_continuous_scale='Viridis', 
                      size_max=30, template="plotly_white")
    
    fig6.add_hline(y=scatter_data['Children'].mean(), line_dash="dash", line_color="gray", annotation_text="Avg Output")
    fig6.add_vline(x=scatter_data['Pincodes'].mean(), line_dash="dash", line_color="gray", annotation_text="Avg Reach")
    
    st.plotly_chart(fig6, use_container_width=True)

# --- FOOTER ---
st.markdown("---")
f1, f2 = st.columns(2)
with f1:
    st.caption("© 2026 Aliya Jabbar ")
with f2:
    st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>Contact Support: data-ops@uidai.gov.in</p>", unsafe_allow_html=True)
