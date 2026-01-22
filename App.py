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

# --- PROFESSIONAL VIOLET UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    
    /* Insight Box: Light Violet Theme */
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
    # Attempt to load data
    try:
        df = pd.read_parquet("cleaned_data.parquet")
    except:
        # Fallback empty dataframe with expected columns for safety
        df = pd.DataFrame(columns=['state', 'district', 'date', 'total_enrollment', 'children_enrollment', 'age_0_5', 'age_5_17', 'age_18_greater', 'pincode'])
    
    try:
        district_df = pd.read_csv("district_priority.csv")
    except:
        district_df = pd.DataFrame()

    # Normalize column names to avoid KeyErrors
    df.columns = [c.lower() for c in df.columns]
    if not district_df.empty:
        district_df.columns = [c.lower() for c in district_df.columns]

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
    
    df["date"] = pd.to_datetime(df["date"])
    
    return df, district_df

df_clean, district_summary = load_and_clean_data()

# --- SIDEBAR: NAVIGATION & DYNAMIC FILTERS ---
with st.sidebar:
    st.title("📌 Dashboard Menu")
    menu = st.radio("Switch View:", 
        ["📋 Executive Summary", "🗺️ National Heatmap", "🚨 Priority Districts", "📈 Enrollment Trends", "💫 Performance Matrix"])
    
    st.markdown("---")
    st.subheader("Global Filters")

    # 1. Date Range Filter
    if not df_clean.empty:
        min_date = df_clean['date'].min().date()
        max_date = df_clean['date'].max().date()
        selected_date_range = st.date_input("Select Date Range", [min_date, max_date])
    
    # 2. State Filter (Select All Logic)
    all_states = sorted(df_clean['state'].unique())
    select_all_states = st.checkbox("Select All States", value=True)
    
    if select_all_states:
        selected_states = all_states
    else:
        selected_states = st.multiselect("Pick States", all_states)

    # 3. District Filter (Cascading Logic to prevent KeyError)
    # Using .get() or lowercase check to ensure 'district' column is found
    dist_col = 'district' if 'district' in df_clean.columns else 'District'
    
    relevant_districts = sorted(df_clean[df_clean['state'].isin(selected_states)][dist_col].unique())
    select_all_districts = st.checkbox("Select All Districts", value=True)
    
    if select_all_districts:
        selected_districts = relevant_districts
    else:
        selected_districts = st.multiselect("Pick Districts", relevant_districts)

    st.markdown("---")
    st.markdown("Created by: **Aliya Jabbar**")

# --- APPLY GLOBAL FILTERS ---
if len(selected_date_range) == 2:
    start_dt, end_dt = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])
    
    mask = (
        (df_clean['state'].isin(selected_states)) & 
        (df_clean[dist_col].isin(selected_districts)) &
        (df_clean['date'] >= start_dt) & 
        (df_clean['date'] <= end_dt)
    )
    df_final = df_clean.loc[mask]
    
    # Filter district summary (using lowercase 'state' and 'district' as normalized above)
    if not district_summary.empty:
        dist_final = district_summary[
            (district_summary['state'].isin(selected_states)) & 
            (district_summary['district'].isin(selected_districts))
        ]
    else:
        dist_final = pd.DataFrame()
else:
    df_final = df_clean
    dist_final = district_summary

# --- MAIN DASHBOARD INTERFACE ---
st.title("Aadhaar Enrollment Gap Analysis")
st.caption(f"Intelligence Report | 2026 | Filters Applied: {len(selected_states)} States")

if df_final.empty:
    st.warning("No data matches the selected filters. Please adjust the sidebar settings.")
else:
    # --- SECTION 1: EXECUTIVE SUMMARY ---
    if menu == "📋 Executive Summary":
        m1, m2, m3, m4 = st.columns(4)
        total_v = df_final['total_enrollment'].sum()
        child_v = df_final['children_enrollment'].sum()
        
        m1.metric("Total Enrollments", f"{total_v:,}")
        m2.metric("Child Enrollment", f"{child_v:,}", f"{(child_v/total_v*100 if total_v>0 else 0):.1f}%")
        m3.metric("Pincodes Covered", f"{df_final['pincode'].nunique():,}")
        m4.metric("Active Regions", f"{df_final['state'].nunique():,}")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            # Multi-color Pie Chart
            age_map = {
                'Age 0-5': df_final['age_0_5'].sum(), 
                'Age 5-17': df_final['age_5_17'].sum(), 
                'Age 18+': df_final['age_18_greater'].sum()
            }
            fig_pie = px.pie(
                names=list(age_map.keys()), 
                values=list(age_map.values()),
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel # Professional Multi-color
            )
            fig_pie.update_layout(title="Enrollment by Demographic")
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('<div class="insight-box">Demographic Insight: Children and teenagers represent the largest volume of new registrations in the filtered dataset.</div>', unsafe_allow_html=True)

        with c2:
            top_states = df_final.groupby('state')['children_enrollment'].sum().nlargest(10).reset_index()
            fig_bar = px.bar(top_states, x='children_enrollment', y='state', orientation='h',
                             title="Leading States (Child Enrollment)", color='children_enrollment', 
                             color_continuous_scale='Purples') # Violet theme bar
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('<div class="insight-box">Operational Focus: Top states indicate high demand; resources should be scaled to match these volumes.</div>', unsafe_allow_html=True)

    # --- SECTION 2: NATIONAL HEATMAP ---
    elif menu == "🗺️ National Heatmap":
        st.header("National Enrollment Density")
        map_df = df_final.groupby('state_for_map')['children_enrollment'].sum().reset_index()
        
        fig_map = px.choropleth(
            map_df,
            geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
            featureidkey='properties.ST_NM',
            locations='state_for_map',
            color='children_enrollment',
            color_continuous_scale='RdYlGn', 
            title="State-wise Saturation Gap"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(height=700)
        st.plotly_chart(fig_map, use_container_width=True)
        st.markdown('<div class="insight-box">Geospatial Analysis: Red zones indicate areas where enrollment density is low relative to child population.</div>', unsafe_allow_html=True)

    # --- SECTION 3: PRIORITY DISTRICTS ---
    elif menu == "🚨 Priority Districts":
        st.header("Action Zones (High Gap)")
        if not dist_final.empty:
            p_top = dist_final.sort_values('priority_score', ascending=False).head(20)
            p_top['label'] = p_top['district'] + " (" + p_top['state'] + ")"
            
            fig_p = px.bar(p_top, x='priority_score', y='label', orientation='h',
                          color='priority_score', color_continuous_scale='Reds')
            fig_p.update_layout(height=700, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_p, use_container_width=True)
            st.markdown('<div class="insight-box">Priority Alert: These districts require immediate intervention to bridge the enrollment gap.</div>', unsafe_allow_html=True)
        else:
            st.info("No priority data available for the current selection.")

    # --- SECTION 4: ENROLLMENT TRENDS ---
    elif menu == "📈 Enrollment Trends":
        st.header("Registration Timeline")
        # Ensure 'date' is used for the trend
        trend = df_final.groupby('date').agg({'age_0_5':'sum', 'age_5_17':'sum'}).reset_index()
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=trend['date'], y=trend['age_0_5'], name='Age 0-5', line=dict(color='#7b1fa2', width=3)))
        fig_trend.add_trace(go.Scatter(x=trend['date'], y=trend['age_5_17'], name='Age 5-17', line=dict(color='#ce93d8', width=3)))
        fig_trend.update_layout(title="Daily Enrollment Trends (Filtered Range)", hovermode='x unified')
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('<div class="insight-box">Timeline Note: Spikes often align with regional school admission cycles.</div>', unsafe_allow_html=True)

    # --- SECTION 5: PERFORMANCE MATRIX ---
    elif menu == "💫 Performance Matrix":
        st.header("District Saturation Analysis")
        if not dist_final.empty:
            fig_mat = px.scatter(dist_final, x='pincodes', y='children', size='total', color='priority_score',
                              hover_name='district', color_continuous_scale='RdYlGn_r', size_max=40)
            st.plotly_chart(fig_mat, use_container_width=True)
            st.markdown('<div class="insight-box">Matrix View: Bottom-left (Red) points represent districts with low pincode coverage and low enrollment volume.</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #757575;'>Aadhaar Enrollment Analysis | 2026 | Created by Aliya Jabbar</p>", unsafe_allow_html=True)
