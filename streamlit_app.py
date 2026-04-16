import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

# Page configuration
st.set_page_config(
    page_title="Help Desk Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric:hover {
        transform: translateY(-2px);
        transition: transform 0.2s;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# Data Loading / Upload
# ------------------------------
def generate_sample_data():
    """Generate realistic sample data when no CSV is uploaded"""
    np.random.seed(42)
    n_tickets = 869
    date_range = pd.date_range(start='2026-03-01', end='2026-03-30', freq='h')
    
    categories = ['Software Issue', 'Hardware Problem', 'Network Issue', 
                  'Access Request', 'Data Recovery', 'Training Request']
    priorities = ['High', 'Medium', 'Low']
    statuses = ['Closed', 'Open', 'Waiting']
    agents = [f'Agent_{i}' for i in range(1, 11)]
    
    data = {
        'ticket_id': range(1, n_tickets + 1),
        'created_date': np.random.choice(date_range, n_tickets),
        'resolved_date': [None] * n_tickets,
        'first_response_time': np.random.uniform(1, 48, n_tickets),
        'resolution_time': np.random.uniform(6, 120, n_tickets),
        'category': np.random.choice(categories, n_tickets, p=[0.25,0.20,0.15,0.20,0.10,0.10]),
        'priority': np.random.choice(priorities, n_tickets, p=[0.044,0.946,0.010]),
        'status': np.random.choice(statuses, n_tickets, p=[0.857,0.122,0.021]),
        'assigned_agent': np.random.choice(agents, n_tickets),
        'satisfaction_score': np.random.randint(1, 6, n_tickets)
    }
    df = pd.DataFrame(data)
    closed_mask = df['status'] == 'Closed'
    df.loc[closed_mask, 'resolved_date'] = df.loc[closed_mask, 'created_date'] + \
                                           pd.to_timedelta(df.loc[closed_mask, 'resolution_time'], unit='h')
    return df

def load_data(uploaded_file):
    """Load CSV if provided, else generate sample data"""
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            # Convert date columns if present
            if 'created_date' in df.columns:
                df['created_date'] = pd.to_datetime(df['created_date'])
            if 'resolved_date' in df.columns:
                df['resolved_date'] = pd.to_datetime(df['resolved_date'])
            st.success(f"Loaded {len(df)} records from CSV")
            return df
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
            return generate_sample_data()
    else:
        st.info("No CSV uploaded. Using sample data. Upload your own CSV to replace it.")
        return generate_sample_data()

# ------------------------------
# Sidebar - CSV upload & filters
# ------------------------------
st.sidebar.header("📂 Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload your help desk CSV (optional)",
    type=["csv"],
    help="CSV should contain columns: ticket_id, created_date, status, priority, category, assigned_agent, first_response_time, resolution_time, etc."
)

# Load data
df = load_data(uploaded_file)

# Ensure required columns exist for filtering
required_cols = ['assigned_agent', 'category', 'created_date']
for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column: {col}. Please check your CSV format.")
        st.stop()

st.sidebar.header("🔍 Filters")
# Date range filter
if 'created_date' in df.columns:
    min_date = df['created_date'].min().date()
    max_date = df['created_date'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

selected_agents = st.sidebar.multiselect(
    "Select Agents",
    options=df['assigned_agent'].unique(),
    default=df['assigned_agent'].unique()
)

selected_categories = st.sidebar.multiselect(
    "Categories",
    options=df['category'].unique(),
    default=df['category'].unique()
)

# Apply filters
filtered_df = df.copy()
if 'created_date' in filtered_df.columns and date_range and len(date_range) == 2:
    start_date, end_date = date_range
    mask = (filtered_df['created_date'].dt.date >= start_date) & (filtered_df['created_date'].dt.date <= end_date)
    filtered_df = filtered_df[mask]

filtered_df = filtered_df[
    (filtered_df['assigned_agent'].isin(selected_agents)) &
    (filtered_df['category'].isin(selected_categories))
]

# ------------------------------
# Export Button for Filtered Data
# ------------------------------
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv_data = convert_df_to_csv(filtered_df)
st.sidebar.download_button(
    label="📥 Export Filtered Data as CSV",
    data=csv_data,
    file_name=f"helpdesk_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
    help="Download the currently filtered data as a CSV file"
)

# ------------------------------
# Main Dashboard
# ------------------------------
st.title("🎯 Spiceworks Help Desk Dashboard")
st.caption(f"Data period: {filtered_df['created_date'].min().date()} to {filtered_df['created_date'].max().date()} · {len(filtered_df):,} tickets")

# KPI Row
st.subheader("📈 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Tickets", f"{len(filtered_df):,}")
with col2:
    open_tickets = len(filtered_df[filtered_df['status'] == 'Open']) if 'status' in filtered_df else 0
    st.metric("Open Tickets", open_tickets, delta=f"{open_tickets/len(filtered_df)*100:.1f}%" if len(filtered_df)>0 else "0%")
with col3:
    waiting_tickets = len(filtered_df[filtered_df['status'] == 'Waiting']) if 'status' in filtered_df else 0
    st.metric("Waiting", waiting_tickets)
with col4:
    closed_tickets = len(filtered_df[filtered_df['status'] == 'Closed']) if 'status' in filtered_df else 0
    closure_rate = closed_tickets/len(filtered_df)*100 if len(filtered_df)>0 else 0
    st.metric("Closed ✅", closed_tickets, delta=f"{closure_rate:.1f}% closure rate")
with col5:
    avg_response = filtered_df['first_response_time'].mean() if 'first_response_time' in filtered_df else 0
    st.metric("Avg First Response ⚡", f"{avg_response:.1f}h" if avg_response else "N/A")

col6, col7, col8 = st.columns(3)
with col6:
    avg_resolution = filtered_df['resolution_time'].mean() if 'resolution_time' in filtered_df else 0
    days_per_ticket = avg_resolution / 24 if avg_resolution else 0
    st.metric("Avg Resolution Time", f"{avg_resolution:.1f}h" if avg_resolution else "N/A", delta=f"~{days_per_ticket:.1f} days/ticket" if days_per_ticket else None)
with col7:
    active_agents = len(filtered_df['assigned_agent'].unique()) if 'assigned_agent' in filtered_df else 0
    st.metric("Active Agents", active_agents)
with col8:
    if 'assigned_agent' in filtered_df and len(filtered_df) > 0:
        top_agent = filtered_df['assigned_agent'].value_counts().index[0]
        top_agent_count = filtered_df['assigned_agent'].value_counts().iloc[0]
        st.metric("Top Assignee", top_agent, delta=f"{top_agent_count} tickets")
    else:
        st.metric("Top Assignee", "N/A")

# Charts (only if required columns exist)
if 'status' in filtered_df:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Ticket Status")
        status_counts = filtered_df['status'].value_counts()
        fig_status = px.pie(values=status_counts.values, names=status_counts.index, title="Ticket Status Distribution", hole=0.3)
        st.plotly_chart(fig_status, use_container_width=True)
    with col2:
        if 'priority' in filtered_df:
            st.subheader("🎯 Priority Breakdown")
            priority_counts = filtered_df['priority'].value_counts()
            fig_priority = px.bar(x=priority_counts.values, y=priority_counts.index, orientation='h', title="Priority Distribution")
            st.plotly_chart(fig_priority, use_container_width=True)

if 'category' in filtered_df:
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("📁 Tickets by Category")
        category_counts = filtered_df['category'].value_counts()
        fig_category = px.bar(x=category_counts.index, y=category_counts.values, title="Issues by Category")
        fig_category.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_category, use_container_width=True)
    with col4:
        if 'assigned_agent' in filtered_df:
            st.subheader("👥 Agent Performance")
            agent_tickets = filtered_df['assigned_agent'].value_counts().head(10)
            fig_agents = px.bar(x=agent_tickets.values, y=agent_tickets.index, orientation='h', title="Top 10 Agents by Ticket Volume")
            st.plotly_chart(fig_agents, use_container_width=True)

# Time series
if 'created_date' in filtered_df:
    st.subheader("📈 Ticket Trends Over Time")
    daily_tickets = filtered_df.groupby(filtered_df['created_date'].dt.date).size().reset_index(name='count')
    fig_trend = px.line(daily_tickets, x='created_date', y='count', title='Daily Ticket Creation Trend', markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# Raw data expander
with st.expander("📋 View Filtered Data"):
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
