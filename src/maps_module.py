import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import warnings
import processing
warnings.filterwarnings('ignore')

# =====================================================================
# 1. OPTIMIZED DATA LOADING & STATS ENGINE
# =====================================================================
@st.cache_data
def load_data(pathfile='../data/df_master.csv'):
    df = processing.load_data(pathfile)
    
    return pd.DataFrame(df)

@st.cache_data
def calculate_spatial_statistics(df_season):
    """
    Computes point-by-point Ordinary Spearman correlations.
    """
    results = []
    grid_groups = df_season.groupby(['latitude', 'longitude'])
    
    for (lat, lon), group in grid_groups:
        if len(group) < 3: 
            continue
            
        try:
            M_val = group['analysed_sst'].corr(group['chlor_a'], method='spearman')
            
            if np.isnan(M_val):
                continue
                
            results.append({
                'latitude': lat, 
                'longitude': lon,
                'chlor_a': group['chlor_a'].mean(),
                'analysed_sst': group['analysed_sst'].mean(),
                'M': M_val
            })
        except:
            continue
            
    return pd.DataFrame(results)

# =====================================================================
# 2. REUSABLE MAP WIDGET COMPONENTS
# =====================================================================
def configure_dark_islands(fig):
    """
    Adds a public domain GeoJSON layer on top of carto-positron.
    This effectively recolors all landmasses and islands to a sharp dark gray
    while preserving the crisp white ocean background.
    """
    fig.update_layout(
        mapbox=dict(
            style="carto-positron", # Keeps the ocean white/light
            layers=[
                {
                    "sourcetype": "geojson",
                    # Lightweight, reliable open-source land polygon geometry 
                    "source": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson",
                    "type": "fill",
                    "color": "#3a3a3a",    # Dark Charcoal Gray for the islands
                    "opacity": 1.0,        # Fully solid dark color
                    "below": ""            # Forces it on top of the map background canvas
                }
            ]
        )
    )
    return fig

def render_chlorophyll_map(df, center_lat, center_lon, height=250):
    """Renders the Chlorophyll-a Mean Map Widget with adjustable height."""
    fig = px.scatter_mapbox(
        df, lat="latitude", lon="longitude", color="chlor_a",
        color_continuous_scale="Cividis",
        range_color=[0, 0.5],
        zoom=5, center={"lat": center_lat, "lon": center_lon},
        hover_data={"latitude": True, "longitude": True, "chlor_a": ":.4f"}
    )
    fig.update_traces(marker=dict(size=7, opacity=1.0))
    # Height is controlled perfectly here via the layout
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=height)
    
    fig = configure_dark_islands(fig)
    # Fixed: Removed invalid height='stretch' parameter
    st.plotly_chart(fig, use_container_width=True)


def render_sst_map(df, center_lat, center_lon, height=250):
    """Renders the Sea Surface Temperature Mean Map Widget with adjustable height."""
    fig = px.scatter_mapbox(
        df, lat="latitude", lon="longitude", color="analysed_sst",
        color_continuous_scale="Cividis",
        range_color=[df['analysed_sst'].min(), df['analysed_sst'].max()],
        zoom=5, center={"lat": center_lat, "lon": center_lon},
        hover_data={"latitude": True, "longitude": True, "analysed_sst": ":.4f"}
    )
    fig.update_traces(marker=dict(size=7, opacity=1.0))
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=height)
    
    fig = configure_dark_islands(fig)
    # Fixed: Removed invalid height='stretch' parameter
    st.plotly_chart(fig, use_container_width=True)


def render_correlation_map(df, center_lat, center_lon, height=500):
    """Renders the Ordinary Correlation Map Widget with adjustable height."""
    fig = px.scatter_mapbox(
        df, lat="latitude", lon="longitude", color="M",
        # Beautiful clean continuous diverging color scale
        color_continuous_scale=[[0, 'blue'], [0.5, 'white'], [1.0, 'red']], 
        range_color=[-1, 1],
        zoom=5, center={"lat": center_lat, "lon": center_lon},
        hover_data={"latitude": True, "longitude": True, "M": ":.4f"}
    )
    fig.update_traces(marker=dict(size=7, opacity=1.0))
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=height)
    
    fig = configure_dark_islands(fig)
    st.plotly_chart(fig, use_container_width=True)


# =====================================================================
# 3. INDEPENDENT EXECUTION ENGINE (MAIN)
# =====================================================================

def map_main(df_master, selected_years, target_season):
    
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
    
    # Dynamic subtitle layout handling text changes cleanly
    if selected_years[0] == selected_years[1]:
        time_label = f"Year: {selected_years[0]}"
    else:
        time_label = f"Years: {selected_years[0]}–{selected_years[1]}"
        
    st.markdown(f"**Current Analysis Context:** `{target_season}` | `{time_label}` (Ordinary Spearman Correlation)")

    if df_season_slice.empty:
        st.warning(f"⚠️ No data records found matching '{target_season}' within the selected period {selected_years[0]}-{selected_years[1]}.")
    else:
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
            
            # Form UI layout columns
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("### A: Chlorophyll-a Mean (0-0.5 mg/m³)")
                render_chlorophyll_map(df_plot, c_lat, c_lon, height=380)
                
            with col_right:
                st.markdown("### B: Sea Surface Temperature Mean (°C)")
                render_sst_map(df_plot, c_lat, c_lon, height=380)
                
            st.markdown("### C: Ordinary Corr [SST vs Chl-a]")
            render_correlation_map(df_plot, c_lat, c_lon, height=550)

if __name__ == '__main__':
    st.set_page_config(page_title="Dynamic Oceanographic Mosaic", layout="wide")
    
    # Load dataset using your cached wrapper function
    data_path = '../data/df_master.csv'
    try:
        df_master = load_data(data_path)
    except FileNotFoundError:
        st.error(f"⚠️ Dataset file not found at `{data_path}`.")
        st.stop()
        
    # --- 1. SIDEBAR UI CONTROLS ---
    st.sidebar.title("🗺️ Map Controls")
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
    
    # --- 3. RENDERING ENGINE ---
    st.title("🗺️ Interactive Oceanographic Mosaic Board")

    map_main(df_master, selected_years, target_season)