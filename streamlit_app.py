import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Help Desk Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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

# Data generation with caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def generate_sample_data():
    """Generate realistic help desk ticket data"""
    np.random.seed(42)
    
    date_range = pd.date_range(start='2026-03-01', end='2026-03-30', freq='h')
    n_tickets = 869
    
    categories = ['Software Issue', 'Hardware Problem', 'Network Issue', 
                  'Access Request', 'Data Recovery', 'Training Request']
    priorities = ['High', 'Medium', 'Low']
    statuses = ['Closed', 'Open', 'Waiting']
    agents = [f'Agent_{i}' for i in range(1, 11)]
    
    data = {
        'ticket_id': range(1, n_tickets + 1),
        'created_date': np.random.choice(date_range, n_tickets),
        'resolved_date': None,
        'first_response_time': np.random.uniform(1, 48, n_tickets),  # hours
        'resolution_time': np.random.uniform(6, 120, n_tickets),    # hours
        'category': np.random.choice(categories, n_tickets, p=[0.25, 0.20, 0.15, 0.20, 0.10, 0.10]),
        'priority': np.random.choice(priorities, n_tickets, p=[0.044, 0.946, 0.010]),
        'status': np.random.choice(statuses, n_tickets, p=[0.857, 0.122, 0.021]),
        'assigned_agent': np.random.choice(agents, n_tickets),
        'satisfaction_score': np.random.randint(1, 6, n_tickets)
    }
    
    df = pd.DataFrame(data)
    
    # Set resolved dates for closed tickets
    closed_mask = df['status'] == 'Closed'
    df.loc[closed_mask, 'resolved_date'] = df.loc[closed_mask, 'created_date'] + \
                                           pd.to_timedelta(df.loc[closed_mask, 'resolution_time'], unit='h')
    
    return df

# Load data
df = generate_sample_data()

# Sidebar filters
st.sidebar.header("🔍 Filters")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime(2026, 3, 1), datetime(2026, 3, 30)),
    min_value=datetime(2026, 3, 1),
    max_value=datetime(2026, 3, 30)
)

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
filtered_df = df[
    (df['assigned_agent'].isin(selected_agents)) &
    (df['category'].isin(selected_categories))
]

# Main dashboard
st.title("🎯 Spiceworks Help Desk Dashboard")
st.caption(f"March 2026 · IOEC · {len(filtered_df):,} tickets")

# KPI Row - Using st.columns for metrics
st.subheader("📈 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Tickets", f"{len(filtered_df):,}", 
              delta=f"{len(filtered_df)/869*100:.1f}% of total")
    
with col2:
    open_tickets = len(filtered_df[filtered_df['status'] == 'Open'])
    st.metric("Open Tickets", open_tickets, 
              delta=f"{open_tickets/len(filtered_df)*100:.1f}%")
    
with col3:
    waiting_tickets = len(filtered_df[filtered_df['status'] == 'Waiting'])
    st.metric("Waiting", waiting_tickets)
    
with col4:
    closed_tickets = len(filtered_df[filtered_df['status'] == 'Closed'])
    closure_rate = closed_tickets/len(filtered_df)*100
    st.metric("Closed ✅", closed_tickets, 
              delta=f"{closure_rate:.1f}% closure rate")
    
with col5:
    avg_response = filtered_df['first_response_time'].mean()
    st.metric("Avg First Response ⚡", f"{avg_response:.1f}h")

col6, col7, col8 = st.columns(3)

with col6:
    avg_resolution = filtered_df['resolution_time'].mean()
    days_per_ticket = avg_resolution / 24
    st.metric("Avg Resolution Time", f"{avg_resolution:.1f}h", 
              delta=f"~{days_per_ticket:.1f} days/ticket")
    
with col7:
    active_agents = len(filtered_df['assigned_agent'].unique())
    st.metric("Active Agents", active_agents)
    
with col8:
    top_agent = filtered_df['assigned_agent'].value_counts().index[0]
    top_agent_count = filtered_df['assigned_agent'].value_counts().iloc[0]
    st.metric("Top Assignee", top_agent, 
              delta=f"{top_agent_count} tickets")

# Charts Row
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Ticket Status")
    status_counts = filtered_df['status'].value_counts()
    fig_status = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Ticket Status Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=0.3  # Donut chart effect
    )
    fig_status.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_status, use_container_width=True)

with col2:
    st.subheader("🎯 Priority Breakdown")
    priority_counts = filtered_df['priority'].value_counts()
    fig_priority = px.bar(
        x=priority_counts.values,
        y=priority_counts.index,
        orientation='h',
        title="Priority Distribution",
        color=priority_counts.index,
        color_discrete_sequence=['#ff4444', '#ffaa44', '#44ff44']
    )
    fig_priority.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_priority, use_container_width=True)

# Second row of charts
col3, col4 = st.columns(2)

with col3:
    st.subheader("📁 Tickets by Category")
    category_counts = filtered_df['category'].value_counts()
    fig_category = px.bar(
        x=category_counts.index,
        y=category_counts.values,
        title="Issues by Category",
        color=category_counts.values,
        color_continuous_scale='Viridis'
    )
    fig_category.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig_category, use_container_width=True)

with col4:
    st.subheader("👥 Agent Performance")
    agent_tickets = filtered_df['assigned_agent'].value_counts().head(10)
    fig_agents = px.bar(
        x=agent_tickets.values,
        y=agent_tickets.index,
        orientation='h',
        title="Top 10 Agents by Ticket Volume",
        color=agent_tickets.values,
        color_continuous_scale='Blues'
    )
    fig_agents.update_layout(height=400)
    st.plotly_chart(fig_agents, use_container_width=True)

# Time series analysis
st.subheader("📈 Ticket Trends Over Time")
daily_tickets = filtered_df.groupby(filtered_df['created_date'].dt.date).size().reset_index(name='count')
fig_trend = px.line(
    daily_tickets,
    x='created_date',
    y='count',
    title='Daily Ticket Creation Trend',
    markers=True
)
fig_trend.update_layout(xaxis_title="Date", yaxis_title="Number of Tickets")
st.plotly_chart(fig_trend, use_container_width=True)

# Data table with expander
with st.expander("📋 View Raw Data"):
    st.dataframe(
        filtered_df,
        column_config={
            "ticket_id": "Ticket ID",
            "created_date": st.column_config.DatetimeColumn("Created"),
            "first_response_time": st.column_config.NumberColumn("First Response (h)"),
            "resolution_time": st.column_config.NumberColumn("Resolution Time (h)"),
            "satisfaction_score": st.column_config.NumberColumn("Satisfaction Score")
        },
        use_container_width=True,
        hide_index=True
    )
