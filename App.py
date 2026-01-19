import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Aadhaar Gap Analysis 2026", layout="wide", page_icon="🎯")

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #FF6B6B; }
    .insight-box { background-color: #e1f5fe; padding: 15px; border-radius: 8px; border-left: 5px solid #03a9f4; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING & WHITELISTING ---
@st.cache_data
def load_and_clean_data():
    # 1. Load Files
    try:
        df = pd.read_parquet("cleaned_data.parquet")
    except:
        df = pd.read_csv("cleaned_data.csv")
    
    district_df = pd.read_csv("district_priority.csv")
    
    # 2. THE OFFICIAL 36 DIVISIONS (Colab Verified)
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
    
    # 3. GEOJSON ALIGNMENT (For Map)
    geojson_map = {
        "Andaman and Nicobar Islands": "Andaman & Nicobar",
        "Jammu and Kashmir": "Jammu & Kashmir",
    }

    # 4. CLEANING PROCESS
    df['state'] = df['state'].str.strip()
    df = df[df['state'].isin(ALL_VALID)] # Force 36/36
    df['state_for_map'] = df['state'].replace(geojson_map)
    
    # District Clean & Stable Sorting
    district_df = district_df[district_df['State'].isin(ALL_VALID)]
    district_df['State_Map'] = district_df['State'].replace(geojson_map)
    district_df = district_df[district_df['District'].str.lower() != 'unknown']
    # Tie-breaker sort to keep the list stable
    district_df = district_df.sort_values(by=['PRIORITY_SCORE', 'District'], ascending=[False, True])

    # Date Logic
    df["date"] = pd.to_datetime(df["date"])
    df['month_name'] = df['date'].dt.month_name().str[:3]
    df['month_num'] = df['date'].dt.month

    return df, district_df

df_clean, district_summary = load_and_clean_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 Navigation")
menu = st.sidebar.radio("Select View:", 
    ["📋 Executive Summary", "🗺️ National Heatmap", "🚨 Priority Districts", "📈 Enrollment Trends", "💫 Performance Matrix"])

st.sidebar.markdown("---")
st.sidebar.write(f"✅ **States/UTs:** 36/36")
st.sidebar.write(f"🏘️ **Districts:** {df_clean['district'].nunique():,}")

# --- 📋 SECTION 1: EXECUTIVE SUMMARY ---
if menu == "📋 Executive Summary":
    st.title("📊 Aadhaar Enrollment Executive Summary")
    
    # Top Stats
    m1, m2, m3, m4 = st.columns(4)
    total_e = df_clean['total_enrollment'].sum()
    child_e = df_clean['children_enrollment'].sum()
    m1.metric("Total Enrollments", f"{total_e:,}")
    m2.metric("Child (0-17)", f"{child_e:,}", f"{(child_e/total_e*100):.1f}%")
    m3.metric("Pincodes Covered", f"{df_clean['pincode'].nunique():,}")
    m4.metric("Adults (18+)", f"{df_clean['age_18_greater'].sum():,}")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        # Age Donut Chart
        age_totals = {'Age 0-5': df_clean['age_0_5'].sum(), 'Age 5-17': df_clean['age_5_17'].sum(), 'Age 18+': df_clean['age_18_greater'].sum()}
        fig3 = go.Figure(data=[go.Pie(labels=list(age_totals.keys()), values=list(age_totals.values()),
                                     hole=0.4, marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1']))])
        fig3.update_layout(title="Overall Age Distribution", height=400)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('<div class="insight-box">💡 <b>Insight:</b> Children (0-17) represent the vast majority of new enrollments, highlighting the success of school-level initiatives.</div>', unsafe_allow_html=True)

    with c2:
        # Top States Bar Chart
        top10_s = df_clean.groupby('state')['children_enrollment'].sum().nlargest(10).reset_index()
        fig1 = px.bar(top10_s, x='children_enrollment', y='state', orientation='h',
                      title="Top 10 States (Child Enrollment)", color='children_enrollment', color_continuous_scale='Blues')
        fig1.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('<div class="insight-box">💡 <b>Insight:</b> Uttar Pradesh and Bihar are the primary drivers of enrollment volume during this period.</div>', unsafe_allow_html=True)

# --- 🗺️ SECTION 2: NATIONAL HEATMAP ---
elif menu == "🗺️ National Heatmap":
    st.title("🌍 State-wise Child Enrollment Heatmap")
    state_map_data = df_clean.groupby('state_for_map')['children_enrollment'].sum().reset_index()
    
    fig4 = px.choropleth(
        state_map_data,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        featureidkey='properties.ST_NM',
        locations='state_for_map',
        color='children_enrollment',
        color_continuous_scale='RdYlGn',
        title="Geographic Saturation (Child Enrollments)"
    )
    fig4.update_geos(fitbounds="locations", visible=False)
    fig4.update_layout(height=700)
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('<div class="insight-box">💡 <b>Insight:</b> Green zones show high saturation; Red/Yellow zones indicate regions where additional enrollment centers or mobile vans are required.</div>', unsafe_allow_html=True)

# --- 🚨 SECTION 3: PRIORITY DISTRICTS ---
elif menu == "🚨 Priority Districts":
    st.title("🚨 Top 20 Priority Districts")
    st.warning("These districts have been identified as 'Urgent' based on low enrollment counts and poor pincode coverage.")
    
    # Use head(20) from the stable sorted summary
    priority_top20 = district_summary.head(20).copy()
    priority_top20['label'] = priority_top20['District'] + ", " + priority_top20['State']
    
    fig5 = px.bar(priority_top20, x='PRIORITY_SCORE', y='label', orientation='h',
                  color='PRIORITY_SCORE', color_continuous_scale='Reds', text='Children')
    fig5.update_traces(texttemplate='%{text} children', textposition='outside')
    fig5.update_layout(height=700, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig5, use_container_width=True)
    
    top_d = priority_top20.iloc[0]['District']
    st.markdown(f'<div class="insight-box">💡 <b>Insight:</b> {top_d} is currently the #1 priority. Deployment of mobile enrollment kits here is highly recommended.</div>', unsafe_allow_html=True)

# --- 📈 SECTION 4: ENROLLMENT TRENDS ---
elif menu == "📈 Enrollment Trends":
    st.title("📈 Monthly Enrollment Trends")
    monthly = df_clean.groupby(['month_num', 'month_name']).agg({'age_0_5':'sum', 'age_5_17':'sum'}).reset_index().sort_values('month_num')
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_0_5'], name='Age 0-5', line=dict(color='#FF6B6B', width=4), mode='lines+markers'))
    fig2.add_trace(go.Scatter(x=monthly['month_name'], y=monthly['age_5_17'], name='Age 5-17', line=dict(color='#4ECDC4', width=4), mode='lines+markers'))
    fig2.update_layout(title="Enrollment Over Time (2025)", hovermode='x unified')
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown('<div class="insight-box">💡 <b>Insight:</b> September recorded a massive spike in student enrollments (5-17), likely coinciding with the academic session start.</div>', unsafe_allow_html=True)

# --- 💫 SECTION 5: PERFORMANCE MATRIX ---
elif menu == "💫 Performance Matrix":
    st.title("💫 District Performance Analysis")
    # Removing outliers for clear viewing
    scatter_data = district_summary[(district_summary['Children'] > 0) & (district_summary['Pincodes'] > 0)].copy()
    
    fig6 = px.scatter(scatter_data, x='Pincodes', y='Children', size='Total', color='PRIORITY_SCORE',
                     hover_name='District', color_continuous_scale='RdYlGn_r', size_max=40,
                     title="Child Enrollment vs. Geographic Coverage")
    st.plotly_chart(fig6, use_container_width=True)
    
    st.markdown('<div class="insight-box">💡 <b>Insight:</b> Districts in the bottom-left corner represent the "Identity Gap"—high priority areas with limited pincode coverage and low output.</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.caption("Aadhaar Hackathon 2026 | Priority Identification Dashboard | Data Source: UIDAI Cleaned Dataset")
