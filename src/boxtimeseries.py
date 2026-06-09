import streamlit as st
import pandas as pd
import processing
import plotly.graph_objects as go

st.set_page_config(layout="wide")

@st.cache_data
def load_data(pathfile='../data/df_master.csv'):
    df = processing.load_data(pathfile)
    
    return pd.DataFrame(df)

def ocean_boxplot_widget(data: pd.DataFrame, target_col: str, title: str, y_label: str, line_color: str):
    chronological_order = data['Year_Season'].drop_duplicates().tolist()
    
    season_colors = {
        "Musim Barat": {"solid": "#1f77b4", "alpha": "rgba(31, 119, 180, 0.25)"},
        "Musim Peralihan 1": {"solid": "#e4aa15", "alpha": "rgba(228, 170, 21, 0.25)"},
        "Musim Timur": {"solid": "#e81111", "alpha": "rgba(214, 39, 240, 0.25)"},
        "Musim Peralihan 2": {"solid": "#b214b2", "alpha": "rgba(196, 39, 214, 0.25)"}
    }
    
    def get_color_config(season_val, state="solid"):
        key = str(season_val)
        if key in season_colors:
            return season_colors[key][state]
        for k, v in season_colors.items():
            if k.lower() in key.lower() or key.lower() in k.lower():
                return v[state]
        return "#7f7f7f" if state == "solid" else "rgba(127, 127, 127, 0.5)"

    st.subheader(title)
    
    metric_mean = data[target_col].mean()
    metric_std = data[target_col].std()
    mean_series = data.groupby('Year_Season', sort=False)[target_col].mean()
    
    fig = go.Figure()

    for x_val in chronological_order:
        sub_df = data[data['Year_Season'] == x_val]
        if sub_df.empty:
            continue
            
        season_type = sub_df['season'].iloc[0]
        box_color = get_color_config(season_type, "alpha")
        
        fig.add_trace(go.Box(
            y=sub_df[target_col],
            name=x_val,
            fillcolor=box_color,
            line=dict(color=box_color, width=1.5),
            boxmean=True,
            showlegend=False,
            boxpoints='outliers',
            marker=dict(opacity=0.1)
        ))
        
    for i in range(len(chronological_order) - 1):
        x_start = chronological_order[i]
        x_end = chronological_order[i+1]
        
        fig.add_trace(go.Scatter(
            x=[x_start, x_end],
            y=[mean_series[x_start], mean_series[x_end]],
            mode='lines+markers',
            line=dict(color=line_color, width=3),
            marker=dict(color=line_color, size=6),
            showlegend=False,
            hoverinfo='skip'
        ))

    if target_col == "chlor_a":
        y_range = [0, 1]
    else:
        y_range = [metric_mean - (2.5 * metric_std), metric_mean + (2.5 * metric_std)]

    fig.update_layout(
        yaxis_title=y_label,
        xaxis_tickangle=-45,
        height=500,
        margin=dict(l=40, r=40, t=20, b=80),
        boxgap=0.15,
        boxgroupgap=0.05,
        yaxis=dict(range=y_range, autorange=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def boxtime_main(df_master: pd.DataFrame, selected_years: tuple, target_season: str):
    """Slices the core dataset in-memory and layouts out chart widgets sequentially."""
    
    # 1. Apply Year Filter Mask
    year_mask = (df_master['Season_Year'] >= selected_years[0]) & (df_master['Season_Year'] <= selected_years[1])

    # Dynamic subtitle layout handling text changes cleanly
    if selected_years[0] == selected_years[1]:
        time_label = f"Year: {selected_years[0]}"
    else:
        time_label = f"Years: {selected_years[0]}–{selected_years[1]}"

    # 2. Apply Season Filter Mask
    if target_season == "All Seasons":
        df_season_slice = df_master[year_mask]
    else:
        df_season_slice = df_master[year_mask & (df_master['season'] == target_season)]

    st.markdown(f"**Current Analysis Context:** `{target_season}` | `{time_label}` (Ordinary Spearman Correlation)")

    if df_season_slice.empty:
        st.warning("⚠️ No records match the selected year range and monsoonal season combinations.")
        return

    # 4. Display Charts on Main Page Stack
    ocean_boxplot_widget(df_season_slice, "chlor_a", "Chlorophyll-a Distribution", "Chlorophyll-a (mg/m³)", "#2ca02c")
    st.write("---")
    ocean_boxplot_widget(df_season_slice, "analysed_sst", "Sea Surface Temperature (SST)", "Temperature (°C)", "#d62728")
    st.write("---")
    ocean_boxplot_widget(df_season_slice, "sss", "Sea Surface Salinity (SSS)", "Salinity (psu)", "#1f77b4")


if __name__ == "__main__":
    try:
        df_raw = load_data()

        # ======================================================================== #
        # SIDEBAR FILTERS                                                          #
        # ======================================================================== #
        st.sidebar.title("🎛️ Control Panel")
        
        # Determine temporal boundary metrics dynamically
        min_year = int(df_raw['Season_Year'].min())
        max_year = int(df_raw['Season_Year'].max())

        # Dual-range slider for filtering years
        sidebar_years = st.sidebar.slider(
            "Select Year Range:",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
            step=1
        )

        # Dropdown selection for targeting individual monsoonal variants
        raw_seasons = sorted(df_raw['season'].unique())
        season_options = ["All Seasons"] + raw_seasons

        sidebar_season = st.sidebar.selectbox(
            "Select Monsoonal Season:", 
            options=season_options, 
            index=0
        )

        # ======================================================================== #
        # APPLICATION HEADLINE & EXECUTION ENTRY                                   #
        # ======================================================================== #
        st.title("💡 Oceanographic Time Series Analysis")
        st.markdown("Chronological distributions with connecting monsoonal trend lines.")

        # Run visualization function using standard parameters
        boxtime_main(df_raw, sidebar_years, sidebar_season)

    except FileNotFoundError:
        st.error("❌ The file `../data/df_master.csv` was not found.")
