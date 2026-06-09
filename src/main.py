# contents of an alternate_dashboard.py file
import streamlit as st
from maps_module import *
from boxtimeseries import *

# Load dataset using your cached wrapper function
try:
    df_master = load_data()
except FileNotFoundError:
    st.error(f"⚠️ Dataset file not found at `x` aka the load data doesnt work.")
    st.stop()
    

# ==========================================
# 1. PAGE INITIALIZATION & CONFIG
# ==========================================
st.set_page_config(
    page_title="Dashboard of Marine Sea Surface Primary Productivity and Temperature",
    page_icon="⚓",
    layout="wide"
)

# ======================================================================== #
# SIDEBAR                                                                  #
# ======================================================================== #
st.sidebar.title("Navigation & Settings")

app_mode = st.sidebar.radio(
    label="Choose Workspace",
    options=[
        "Quick-display",
        "Boxplot Time Series",
        "Exploratory Spatial Data Analysis",
        "Information & About"
    ]
)

st.sidebar.header("🎛️ Filter Options")

# Year Range Slider Setup
min_year = int(df_master['Season_Year'].min())
max_year = int(df_master['Season_Year'].max())

selected_years = st.sidebar.slider(
    "Select Year Range:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),  # Defaults to the full period available
    step=1
)

# Independent Season Dropdown Setup with "All Seasons" option injected
raw_seasons = sorted(df_master['season'].unique())
season_options = ["All Seasons"] + raw_seasons # Places "All Seasons" at the top of the list

target_season = st.sidebar.selectbox(
    "Select Monsoonal Season:", 
    options=season_options, 
    index=0 # Defaults to "All Seasons"
)

# --- 2. MULTI-VARIABLE DYNAMIC FILTERING ---
# First, always filter by the year range selected on the slider
year_mask = (df_master['Season_Year'] >= selected_years[0]) & (df_master['Season_Year'] <= selected_years[1])

# Second, conditionally handle the season filter
if target_season == "All Seasons":
    # Do not filter out any seasons; take the entire year's data blocks
    df_season_slice = df_master[year_mask]
else:
    # Match only the specifically chosen monsoonal season string
    df_season_slice = df_master[year_mask & (df_master['season'] == target_season)]

# Processing The Year ---------------------------------------------------- #

with st.spinner("Calculating spatial statistical matrices..."):
    # If "All Seasons" is chosen, the engine aggregates all coordinates 
    # collected across every single season inside that year bracket
    df_plot = calculate_spatial_statistics(df_season_slice)
    
if df_plot.empty:
    st.error(f"❌ Insufficient overlapping spatial data coordinates to run correlation calculations.")
else:
    # Constrain parameters
    df_plot['chlor_a'] = df_plot['chlor_a']
    
    # Dynamically target the map viewport centers
    c_lat = df_plot['latitude'].mean()
    c_lon = df_plot['longitude'].mean()

# ======================================================================== #
# MAIN LAYOUT                                                              #
# ======================================================================== #
if app_mode == "Quick-display":
    st.title(
        body="Dashboard of Marine Sea Surface Primary Productivity and Temperature"
    )
    st.markdown(
        body="Northen Ocean of Papua"
    )

    column1, column2 = st.columns(
        spec=[0.4,0.6],
        vertical_alignment='center'
    )

    with column2:
        render_correlation_map(
            df=df_plot,
            center_lat=c_lat,
            center_lon=c_lon
        )
    with column1:
        render_chlorophyll_map(
            df=df_plot,
            center_lat=c_lat,
            center_lon=c_lon
        )
        render_sst_map(
            df=df_plot,
            center_lat=c_lat,
            center_lon=c_lon
        )


elif app_mode == "Boxplot Time Series":
    st.title(
        body="Time Series and Data Distribution"
    )
    st.markdown(
        body="Northen Ocean of Papua"
    )

    column1, column2 = st.columns(
        spec=[0.7,0.3]
    )

    with column1:
        boxtime_main(
            df_master=df_master,
            selected_years=selected_years,
            target_season=target_season
        )

# ==========================================
# 4. GLOBAL FOOTER
# ==========================================
st.divider()
st.caption("Streamlit Unified Catalog Application | Science 4.0 Prototyping | 2026")  
