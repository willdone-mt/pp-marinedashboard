import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# =====================================================================
# 1. PAGE CONFIGURATION
# =====================================================================
st.set_page_config(page_title="Dashboard Analisis Oceanografi", layout="wide")

# =====================================================================
# 2. DATA ENGINE (MODULARIZED FOR ALL PARAMETERS)
# =====================================================================
@st.cache_data
def load_raw_data(filepath, skip_units_row=False):
    """Loads raw CSV data safely, with an option to skip unit rows."""
    try:
        if skip_units_row:
            return pd.read_csv(filepath, skiprows=[1])
        return pd.read_csv(filepath)
    except FileNotFoundError:
        return pd.DataFrame()

@st.cache_data
def process_data(df, value_col):
    """
    Generalized processing engine. 
    Cleans timestamps, coordinates, extracts monsoonal timelines, and removes nulls.
    """
    if df.empty or value_col not in df.columns:
        return pd.DataFrame()
        
    df['time'] = pd.to_datetime(df['time'], utc=True, errors='coerce')
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
    
    # Safely parse spatial coordinates for mapping
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])
    
    # Drop rows without valid sensor readings
    df = df[df[value_col].notna()].copy()
    
    df['year'] = df['time'].dt.year
    df['month'] = df['time'].dt.month
    
    def assign_season(month):
        if month in [12, 1, 2]: return 'Musim Barat'
        elif month in [3, 4, 5]: return 'Musim Peralihan 1'
        elif month in [6, 7, 8]: return 'Musim Timur'
        else: return 'Musim Peralihan 2'
        
    df['season'] = df['month'].apply(assign_season)
    season_categories = ['Musim Barat', 'Musim Peralihan 1', 'Musim Timur', 'Musim Peralihan 2']
    df['season'] = pd.Categorical(df['season'], categories=season_categories, ordered=True)
    
    # Shift December into the next year's monsoonal cycle
    df['year_season'] = df.apply(lambda row: row['year'] + 1 if row['month'] == 12 else row['year'], axis=1)
    
    # Filter bounds
    df = df[df['year_season'] >= 2023].copy()
    df['year_season_str'] = df['year_season'].astype(int).astype(str)
    
    return df

# =====================================================================
# 3. UI RENDERING COMPONENTS
# =====================================================================
def render_analysis_tab(df, value_col, title, unit):
    """Generates the interactive charts, maps, and metrics for a specific tab."""
    if df.empty:
        st.warning(f"⚠️ Data untuk {title} tidak tersedia atau kolom `{value_col}` tidak ditemukan.")
        return

    # --- 1. STATISTICAL TABLE ---
    st.markdown(f"### 📈 Statistik {title} per Musim")
    seasonal_stats = df.groupby(['year_season_str', 'season'], observed=True)[value_col].agg(
        Count='count', Mean='mean', Std='std', Min='min', Max='max'
    ).dropna().reset_index()
    st.dataframe(seasonal_stats, use_container_width=True)

    st.divider()

    # --- 2. SPATIAL DISTRIBUTION MAP (Replaces Jupyter Heatmaps) ---
    st.markdown(f"### 🗺️ Peta Distribusi Rata-Rata {title}")
    st.markdown(f"Menampilkan agregasi spasial *{title}* berdasarkan filter musim yang aktif.")
    
    # Calculate the mean parameter value per coordinate grid
    map_df = df.groupby(['latitude', 'longitude'], observed=True)[value_col].mean().reset_index()
    
    # Dynamic constraint logic: prevents Chlorophyll outliers from washing out the color scale
    if value_col == 'chlor_a':
        z_range = [0, 0.5]
    else:
        z_range = [map_df[value_col].min(), map_df[value_col].max()]

    # Render mapping widget
    fig_map = px.scatter_mapbox(
        map_df, lat="latitude", lon="longitude", color=value_col,
        color_continuous_scale="Cividis",
        range_color=z_range,
        zoom=3.8, center={"lat": map_df['latitude'].mean(), "lon": map_df['longitude'].mean()},
        hover_data={"latitude": True, "longitude": True, value_col: ":.4f"},
        labels={value_col: f"{title} ({unit})"}
    )
    
    # Apply solid point tracking and dark-island vector layers
    fig_map.update_traces(marker=dict(size=7, opacity=1.0))
    fig_map.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0}, 
        height=400,
        coloraxis_colorbar=dict(title_side="right", thickness=15),
        mapbox=dict(
            layers=[
                {
                    "sourcetype": "geojson",
                    "source": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson",
                    "type": "fill",
                    "color": "#2b2b2b",
                    "opacity": 1.0,
                    "below": ""
                }
            ]
        )
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.divider()

    # --- 3. TREND & DISTRIBUTION CHARTS ---
    col_left, col_right = st.columns(2)
    season_colors = {
        'Musim Barat': '#FF6B6B', 
        'Musim Peralihan 1': '#4ECDC4',
        'Musim Timur': '#45B7D1', 
        'Musim Peralihan 2': '#FFA07A'
    }
    
    with col_left:
        st.markdown(f"### Trend {title} Musiman")
        mean_df = df.groupby(['year_season_str', 'season'], observed=True)[value_col].mean().reset_index()
        fig_trend = px.line(
            mean_df, x="year_season_str", y=value_col, color="season", markers=True,
            color_discrete_map=season_colors,
            labels={"year_season_str": "Tahun Musim", value_col: f"{title} Mean ({unit})", "season": "Musim"}
        )
        fig_trend.update_traces(line=dict(width=3), marker=dict(size=8))
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.markdown(f"### Distribusi {title}")
        fig_box = px.box(
            df, x="year_season_str", y=value_col, color="season",
            color_discrete_map=season_colors,
            labels={"year_season_str": "Tahun Musim", value_col: f"{title} ({unit})", "season": "Musim"}
        )
        fig_box.update_layout(boxmode='group')
        st.plotly_chart(fig_box, use_container_width=True)

# =====================================================================
# 4. MAIN APPLICATION
# =====================================================================
def eda_main(raw_data='../data/raw'):
    # --- GLOBAL FILTERS (ABOVE TABS) ---
    st.markdown("#### 🎛️ Filter Analisis Global")
    season_list = ['Musim Barat', 'Musim Peralihan 1', 'Musim Timur', 'Musim Peralihan 2']
    selected_seasons = st.multiselect(
        "Pilih Musim untuk dianalisis (berlaku untuk semua tab secara otomatis):", 
        season_list, 
        default=season_list
    )
    st.write("") 

    if not selected_seasons:
        st.warning("⚠️ Pilih minimal satu musim di atas untuk melihat visualisasi data.")
        return

    # --- LOAD RAW DATA ---
    df_kloro_raw = load_raw_data(f'{raw_data}/Klorofil2023-2025.csv')
    df_sst_raw = load_raw_data(f'{raw_data}/Suhu2023-2025.csv')
    df_salinitas_raw = load_raw_data(f'{raw_data}/Salinitas2023-2025.csv', skip_units_row=True)

    # --- PROCESS DATA ---
    df_kloro = process_data(df_kloro_raw, 'chlor_a')
    df_sst = process_data(df_sst_raw, 'analysed_sst')
    df_salinitas = process_data(df_salinitas_raw, 'sss')

    # Apply the global season filter dynamically
    if not df_kloro.empty: df_kloro = df_kloro[df_kloro['season'].isin(selected_seasons)]
    if not df_sst.empty: df_sst = df_sst[df_sst['season'].isin(selected_seasons)]
    if not df_salinitas.empty: df_salinitas = df_salinitas[df_salinitas['season'].isin(selected_seasons)]

    # --- TAB NAVIGATION ---
    tab_kloro, tab_sst, tab_salinity, tab_raw = st.tabs([
        "🌿 Klorofil", "🌡️ SST", "🧂 Salinity", "📥 Raw Data & Download"
    ])

    with tab_kloro:
        render_analysis_tab(df_kloro, 'chlor_a', 'Klorofil-a', 'mg/m³')

    with tab_sst:
        render_analysis_tab(df_sst, 'analysed_sst', 'Sea Surface Temperature', '°C')

    with tab_salinity:
        render_analysis_tab(df_salinitas, 'sss', 'Salinitas', 'PSU')

    with tab_raw:
        st.markdown("### Inspeksi dan Unduh Data Mentah")
        st.markdown("Menampilkan struktur *dataset* orisinal sebelum *preprocessing*.")
        
        col1, col2, col3 = st.columns(3)
        
        def render_raw_section(col, title, df):
            with col:
                st.markdown(f"**{title}**")
                if not df.empty:
                    st.dataframe(df, height=450)
                    
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"⬇️ Unduh Data {title} (.csv)",
                        data=csv_data,
                        file_name=f"{title.lower().replace(' ', '_')}_raw_data.csv",
                        mime='text/csv',
                        use_container_width=True
                    )
                else:
                    st.warning(f"File {title} kosong/tidak ditemukan.")
        
        render_raw_section(col1, "Klorofil", df_kloro_raw)
        render_raw_section(col2, "SST", df_sst_raw)
        render_raw_section(col3, "Salinitas", df_salinitas_raw)

if __name__ == '__main__':
    st.title("🌊 Dashboard Analisis Data Oceanografi (2023-2025)")
    eda_main()