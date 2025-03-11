import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Olist Sales Funnel Analysis",
    page_icon=None,
    layout="wide"
)

# Professional CSS styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Dashboard title */
    .dashboard-title {
        font-size: 2.5rem !important;
        color: #2c3e50 !important;
        font-weight: 700 !important;
        margin-bottom: 30px !important;
        padding-bottom: 10px;
        border-bottom: 3px solid #4a90e2;
    }
    
    /* Metric cards */
    .metric-frame {
        background: white;
        border-radius: 10px;
        padding: 25px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #dee2e6;
        transition: transform 0.2s;
    }
    
    .metric-frame:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    .metric-frame h3 {
        color: #2c3e50;
        margin-bottom: 12px;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    /* Visualization containers */
    .custom-frame {
        background: white;
        border-radius: 12px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #dee2e6;
    }
    
    /* Titles */
    .visual-title {
        font-size: 1.3rem;
        color: #2c3e50;
        margin-bottom: 20px;
        font-weight: 600;
        letter-spacing: -0.5px;
        border-left: 4px solid #4a90e2;
        padding-left: 15px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
        border-right: 1px solid #dee2e6;
    }
    
    /* Header styling */
    .st-emotion-cache-1avcm0n {
        background: #2c3e50 !important;
    }
    
    /* Button styling */
    .st-emotion-cache-7ym5gk {
        background: #4a90e2 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* General typography */
    body {
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        color: #495057;
    }
</style>
""", unsafe_allow_html=True)

# Color palette
COLOR_PALETTE = {
    'primary': '#4a90e2',
    'secondary': '#7c4dff',
    'success': '#00c853',
    'warning': '#ff9100',
    'info': '#00b8d4',
    'converted': '#2e7d32',
    'not_converted': '#b71c1c'
}

def clean_data(uploaded_files):
    data_dict = {}
    
    for file in uploaded_files:
        df = pd.read_csv(file)
        if 'mql_id' in df.columns:
            if 'seller_id' in df.columns:
                data_dict['cld'] = process_cld(df)
            else:
                data_dict['mql'] = process_mql(df)
        elif 'order_id' in df.columns:
            data_dict['order'] = process_orders(df)
    
    if 'cld' in data_dict and 'mql' in data_dict:
        data_dict['merged'] = pd.merge(
            data_dict['cld'][['mql_id', 'won_date', 'business_segment', 'lead_type']],
            data_dict['mql'][['mql_id', 'first_contact_date', 'origin']],
            on='mql_id'
        )
        data_dict['merged']['time_to_close'] = (
            pd.to_datetime(data_dict['merged']['won_date']) - 
            pd.to_datetime(data_dict['merged']['first_contact_date'])
        ).dt.days
    
    return data_dict

def process_cld(df):
    df = df.dropna(subset=['business_segment', 'lead_type', 'business_type'])
    df['won_date'] = pd.to_datetime(df['won_date'])
    df = df.drop(columns=['has_company', 'has_gtin', 'average_stock', 'declared_product_catalog_size'])
    df['lead_behaviour_profile'] = df['lead_behaviour_profile'].apply(
        lambda x: x if x in {'cat', 'eagle', 'wolf', 'shark', np.nan} else np.nan
    )
    df['lead_behaviour_profile'] = df['lead_behaviour_profile'].fillna(df['lead_behaviour_profile'].mode()[0])
    return df

def process_mql(df):
    df = df.dropna(subset=['origin'])
    df['first_contact_date'] = pd.to_datetime(df['first_contact_date'])
    return df

def process_orders(df):
    df = df.dropna(subset=['order_approved_at', 'order_delivered_carrier_date'])
    date_cols = ['order_purchase_timestamp', 'order_approved_at', 
                'order_delivered_carrier_date', 'order_delivered_customer_date']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col])
    return df

def plot_conversion_metrics(mql_filtered, cld_filtered, merged_filtered):
    with st.container():
        st.markdown('<div class="custom-frame">', unsafe_allow_html=True)
        st.markdown('<div class="visual-title">Conversion Metrics</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            total_mql = len(mql_filtered)
            total_closed = len(cld_filtered)
            fig = go.Figure(go.Pie(
                labels=['Converted', 'Not Converted'],
                values=[total_closed, total_mql - total_closed],
                hole=.4,
                marker_colors=[COLOR_PALETTE['converted'], COLOR_PALETTE['not_converted']]
            ))
            fig.update_layout(title='Overall Conversion Rate')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not merged_filtered.empty:
                conv_by_origin = (merged_filtered.groupby('origin').size() / 
                                 mql_filtered['origin'].value_counts()).reset_index(name='rate')
                conv_by_origin = conv_by_origin.sort_values('rate', ascending=False)
                fig = px.bar(conv_by_origin, 
                            x='rate', 
                            y='origin', 
                            orientation='h',
                            title='Conversion Rate by Marketing Channel',
                            color_discrete_sequence=[COLOR_PALETTE['primary']])
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def plot_business_metrics(cld_filtered):
    with st.container():
        st.markdown('<div class="custom-frame">', unsafe_allow_html=True)
        st.markdown('<div class="visual-title">Business Metrics</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            business_dist = cld_filtered['business_segment'].value_counts().reset_index()
            business_dist = business_dist.sort_values('count', ascending=False)
            fig = px.bar(business_dist, 
                        x='count', 
                        y='business_segment',
                        orientation='h',
                        title='Closed Deals by Business Segment',
                        color_discrete_sequence=[COLOR_PALETTE['secondary']])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            lead_dist = cld_filtered['lead_type'].value_counts().reset_index()
            lead_dist = lead_dist.sort_values('count', ascending=False)
            fig = px.bar(lead_dist, 
                        x='count', 
                        y='lead_type',
                        orientation='h',
                        title='Closed Deals by Lead Type',
                        color_discrete_sequence=[COLOR_PALETTE['info']])
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def plot_time_metrics(merged_filtered):
    with st.container():
        st.markdown('<div class="custom-frame">', unsafe_allow_html=True)
        st.markdown('<div class="visual-title">Time Metrics</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if not merged_filtered.empty:
                fig = px.histogram(merged_filtered, 
                                  x='time_to_close',
                                  nbins=20,
                                  title='Deal Closing Time Distribution',
                                  color_discrete_sequence=[COLOR_PALETTE['warning']])
                mean_time = merged_filtered['time_to_close'].mean()
                fig.add_vline(x=mean_time, 
                             line_dash="dash",
                             annotation_text=f"Mean: {mean_time:.1f} days")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not merged_filtered.empty:
                bins = [0,7,15,30,60,365]
                labels = ['0-7 days', '8-15 days', '16-30 days', '31-60 days', '60+ days']
                merged = merged_filtered.copy()
                merged['time_segment'] = pd.cut(merged['time_to_close'], bins=bins, labels=labels)
                time_seg_counts = merged['time_segment'].value_counts().sort_index().reset_index()
                time_seg_counts = time_seg_counts.sort_values('count', ascending=False)
                fig = px.bar(time_seg_counts,
                            x='count',
                            y='time_segment',
                            orientation='h',
                            title='Conversion Velocity by Time Segments',
                            color_discrete_sequence=[COLOR_PALETTE['primary']])
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def plot_team_performance(cld_filtered):
    with st.container():
        st.markdown('<div class="custom-frame">', unsafe_allow_html=True)
        st.markdown('<div class="visual-title">Team Performance</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if not cld_filtered.empty:
                top_sdrs = cld_filtered['sdr_id'].value_counts().nlargest(10).reset_index()
                top_sdrs = top_sdrs.sort_values('count', ascending=False)
                fig = px.bar(top_sdrs,
                            x='count',
                            y='sdr_id',
                            orientation='h',
                            title='Top 10 SDRs by Closed Deals',
                            color_discrete_sequence=[COLOR_PALETTE['primary']])
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not cld_filtered.empty:
                top_srs = cld_filtered['sr_id'].value_counts().nlargest(10).reset_index()
                top_srs = top_srs.sort_values('count', ascending=False)
                fig = px.bar(top_srs,
                            x='count',
                            y='sr_id',
                            orientation='h',
                            title='Top 10 SRs by Closed Deals',
                            color_discrete_sequence=[COLOR_PALETTE['secondary']])
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def plot_order_analysis(order_filtered):
    with st.container():
        st.markdown('<div class="custom-frame">', unsafe_allow_html=True)
        st.markdown('<div class="visual-title">Order Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if not order_filtered.empty:
                delivered = order_filtered[order_filtered['order_status'] == 'delivered'].copy()
                delivered['delivery_time'] = (delivered['order_delivered_customer_date'] - 
                                             delivered['order_purchase_timestamp']).dt.days
                
                fig = px.histogram(delivered, 
                                 x='delivery_time',
                                 nbins=20,
                                 title='Delivery Time Distribution',
                                 color_discrete_sequence=[COLOR_PALETTE['warning']])
                fig.add_vline(x=delivered['delivery_time'].mean(), 
                             line_dash="dash",
                             annotation_text=f"Mean: {delivered['delivery_time'].mean():.1f} days")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not order_filtered.empty:
                delivered = order_filtered[order_filtered['order_status'] == 'delivered'].copy()
                delivered['is_delayed'] = delivered['order_delivered_customer_date'] > delivered['order_estimated_delivery_date']
                delay_pct = delivered['is_delayed'].mean() * 100
                fig = go.Figure(go.Indicator(
                    mode="number",
                    value=delay_pct,
                    title="Delayed Orders Percentage",
                    number={"suffix": "%"},
                    gauge={'axis': {'range': [0, 100]}},
                    domain={'x': [0, 1], 'y': [0, 1]}
                ))
                fig.update_layout(margin=dict(t=50, b=0))
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    st.markdown('<div class="dashboard-title">Olist Sales Funnel Analysis</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("Data Upload")
        uploaded_files = st.file_uploader(
            "Upload Olist datasets (CSV format)",
            type="csv",
            accept_multiple_files=True
        )
    
    if uploaded_files:
        with st.spinner('Processing data...'):
            data = clean_data(uploaded_files)
        
        mql_raw = data.get('mql', pd.DataFrame())
        cld_raw = data.get('cld', pd.DataFrame())
        order_raw = data.get('order', pd.DataFrame())
        merged_raw = data.get('merged', pd.DataFrame())

        with st.sidebar:
            st.header("Filters")
            
            if not mql_raw.empty:
                min_date = mql_raw['first_contact_date'].min()
                max_date = mql_raw['first_contact_date'].max()
                start_date, end_date = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                mql_filtered = mql_raw[
                    (mql_raw['first_contact_date'] >= pd.to_datetime(start_date)) &
                    (mql_raw['first_contact_date'] <= pd.to_datetime(end_date))
                ]
            else:
                mql_filtered = pd.DataFrame()

            if not cld_raw.empty:
                business_segments = st.multiselect(
                    "Business Segments",
                    options=cld_raw['business_segment'].unique(),
                    default=cld_raw['business_segment'].unique()
                )
                cld_filtered = cld_raw[cld_raw['business_segment'].isin(business_segments)]
            else:
                cld_filtered = pd.DataFrame()

            merged_filtered = pd.merge(
                cld_filtered[['mql_id']],
                merged_raw,
                on='mql_id',
                how='inner'
            ) if not cld_filtered.empty and not merged_raw.empty else pd.DataFrame()

            if not order_raw.empty:
                order_filtered = order_raw[
                    (order_raw['order_purchase_timestamp'] >= pd.to_datetime(start_date)) &
                    (order_raw['order_purchase_timestamp'] <= pd.to_datetime(end_date))
                ]
            else:
                order_filtered = pd.DataFrame()

        st.header("Key Performance Indicators")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f'<div class="metric-frame"><h3>Total MQLs</h3>{len(mql_filtered):,}</div>', 
                       unsafe_allow_html=True)
        
        with kpi2:
            st.markdown(f'<div class="metric-frame"><h3>Closed Deals</h3>{len(cld_filtered):,}</div>', 
                       unsafe_allow_html=True)
        
        with kpi3:
            conversion_rate = (len(cld_filtered)/len(mql_filtered)*100) if len(mql_filtered) > 0 else 0
            st.markdown(f'<div class="metric-frame"><h3>Conversion Rate</h3>{conversion_rate:.1f}%</div>', 
                       unsafe_allow_html=True)
        
        with kpi4:
            avg_time = merged_filtered['time_to_close'].mean() if not merged_filtered.empty else 0
            st.markdown(f'<div class="metric-frame"><h3>Avg Time to Close</h3>{avg_time:.1f} days</div>', 
                       unsafe_allow_html=True)

        plot_conversion_metrics(mql_filtered, cld_filtered, merged_filtered)
        plot_business_metrics(cld_filtered)
        plot_time_metrics(merged_filtered)
        plot_team_performance(cld_filtered)
        plot_order_analysis(order_filtered)
        
    else:
        st.info("Please upload datasets through the sidebar to begin analysis")

if __name__ == "__main__":
    main()