import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from weather_capstone.database import get_connection
from weather_capstone.config import DEFAULT_SQLITE_PATH
from weather_capstone.logging_config import configure_logging

configure_logging()

st.set_page_config(
    page_title="Weather Insight Platform",
    page_icon="☀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, .stMetric, .stSelectbox, .stMultiSelect, .stSlider, button {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #111418; /* Blueprint deep slate carbon */
        color: #F5F8FA; /* Blueprint off-white primary text */
    }

    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 2rem !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0c0e11 !important; /* Blueprint darkest steel sidebar */
        border-right: 1px solid #30404D; /* Blueprint low-contrast blue-gray divider */
    }

    /* Tabular aligning for digits */
    .metric-value, .stApp table, [data-testid="stTable"] td {
        font-variant-numeric: tabular-nums !important;
    }
    
    .metric-card {
        background-color: #182026; /* Blueprint dark cobalt gray card */
        border: 1px solid #30404D;
        border-top: 3px solid #137CBD; /* Accent cobalt blue header indicator */
        border-radius: 4px; /* Blueprint strict 4px corners */
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .metric-title {
        font-size: 0.75rem;
        color: #A7B6C2; /* Blueprint slate grey-blue muted text */
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2px;
    }

    .metric-subtitle {
        font-size: 0.75rem;
        color: #A7B6C2;
    }

    /* Flat Tabs Blueprint Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px !important;
        border-bottom: 2px solid #30404D !important;
        padding-bottom: 2px !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: auto !important;
        background-color: transparent !important;
        color: #A7B6C2 !important;
        border: none !important;
        padding: 8px 4px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: color 0.15s ease !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #F5F8FA !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: #137CBD !important; /* Active cobalt indicator */
        font-weight: 600 !important;
        border-bottom: 2px solid #137CBD !important;
    }

    /* Stretch buttons inside sidebar */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stDownloadButton > button {
        width: 100% !important;
    }

    /* Export buttons styling - prevents side overflows */
    .stDownloadButton > button {
        background-color: #0F9960 !important; /* Blueprint success forest green */
        color: #ffffff !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        border: none !important;
        padding: 10px 12px !important;
        height: auto !important;
        min-height: 40px !important;
        white-space: normal !important;
        word-break: break-word !important;
        transition: background-color 0.2s ease, transform 0.1s ease !important;
    }
    .stDownloadButton > button:hover {
        background-color: #0D8050 !important;
        transform: translateY(-1px);
    }
    .stDownloadButton > button:active {
        transform: translateY(1px);
    }

    /* Standard blueprint button styling */
    .stButton > button {
        background-color: #137CBD !important; /* Blueprint cobalt */
        color: #ffffff !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        border: none !important;
        padding: 8px 16px !important;
        height: 38px !important;
        transition: background-color 0.2s ease, transform 0.1s ease !important;
    }
    .stButton > button:hover {
        background-color: #106BA3 !important;
        transform: translateY(-1px);
    }
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Hide Streamlit element toolbar completely to prevent overlap and duplicate buttons */
    [data-testid="stElementToolbar"] {
        display: none !important;
    }

    /* Style Multiselect Tags (Chips) to match Palantir Blueprint JS slate theme */
    div[data-baseweb="tag"] {
        background-color: #293742 !important; /* Blueprint dark slate tag background */
        border: 1px solid #30404D !important; /* Low-contrast border */
        border-radius: 3px !important;
        padding: 2px 6px !important;
    }
    
    div[data-baseweb="tag"] span {
        color: #F5F8FA !important; /* High-contrast light text */
    }

    div[data-baseweb="tag"] svg {
        fill: #A7B6C2 !important; /* Muted close 'x' icon */
    }
    
    div[data-baseweb="tag"]:hover {
        background-color: #30404D !important;
        border-color: #137CBD !important; /* Accent border on hover */
    }

    .js-plotly-plot .plotly .modebar {
        background-color: rgba(24, 32, 38, 0.95) !important;
        border: 1px solid #30404D !important;
        border-radius: 4px !important;
        padding: 4px 6px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
        transform: scale(1.2) !important;
        transform-origin: top right !important;
    }
    
    .js-plotly-plot .plotly .modebar-btn {
        padding: 4px 6px !important;
        transition: all 0.15s ease !important;
    }
    
    .js-plotly-plot .plotly .modebar-btn path {
        fill: #A7B6C2 !important;
        transition: fill 0.15s ease !important;
    }
    
    .js-plotly-plot .plotly .modebar-btn:hover path {
        fill: #137CBD !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_all_data(db_path: Path, db_mtime: float) -> pd.DataFrame:
    with get_connection(db_path) as conn:
        query = """
            SELECT city, country, temperature_celsius, condition, 
                   humidity_percent, wind_speed_kmh, pressure_hpa, local_time, scraped_at
            FROM weather_observations
        """
        df = pd.read_sql_query(query, conn)
    return df


def main():
    st.markdown("""
    <div style='display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #30404D; padding-bottom: 12px; margin-bottom: 24px;'>
        <div>
            <h1 style='margin: 0; font-size: 2.1rem; font-weight: 700; color: #F5F8FA;'>Weather Insight Platform</h1>
            <p style='margin: 4px 0 0 0; color: #A7B6C2; font-size: 0.95rem;'>Live planetary intelligence database and predictive weather patterns</p>
        </div>
        <div style='text-align: right;'>
            <span style='background-color: #182026; color: #137CBD; border: 1px solid #30404D; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;'>
                ● Telemetry Online
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    db_path = DEFAULT_SQLITE_PATH

    if not db_path.exists():
        st.error("Database not found. Please run the data pipeline first:")
        st.code("""
python scripts/scrape_weather.py --limit 5
python scripts/clean_weather.py
python scripts/load_database.py
        """, language="bash")
        st.stop()

    db_mtime = db_path.stat().st_mtime if db_path.exists() else 0.0
    df = load_all_data(db_path, db_mtime)

    if df.empty:
        st.warning("No data found in database. Please run the data pipeline first.")
        st.stop()

    from weather_capstone.cleaner import categorize_condition
    df["Condition Category"] = df["condition"].apply(categorize_condition)

    st.sidebar.header("Settings")
    unit_system = st.sidebar.radio(
        "Unit System",
        options=["Metric (°C, km/h, hPa)", "Imperial (°F, mph, inHg)"],
        index=0
    )
    is_imperial = unit_system.startswith("Imperial")

    if is_imperial:
        df["temp_display"] = (df["temperature_celsius"] * 9 / 5 + 32).round(1)
        df["wind_display"] = (df["wind_speed_kmh"] / 1.60934).round(1)
        df["pressure_display"] = (df["pressure_hpa"] / 33.8639).round(2)
        temp_suffix = "°F"
        wind_suffix = "mph"
        pressure_suffix = "inHg"
    else:
        df["temp_display"] = df["temperature_celsius"]
        df["wind_display"] = df["wind_speed_kmh"]
        df["pressure_display"] = df["pressure_hpa"]
        temp_suffix = "°C"
        wind_suffix = "km/h"
        pressure_suffix = "hPa"

    st.sidebar.markdown("---")
    st.sidebar.header("Filters")

    if st.sidebar.button("Reset Filters"):
        for key in ["countries_filter", "city_filter", "temp_filter", "wind_filter", "humidity_filter", "conditions_filter"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    country_list = sorted(df["country"].dropna().unique().tolist())
    
    popular_defaults = ["USA", "Canada", "China", "India", "Germany", "United Kingdom", "UK", "Japan", "France", "Brazil", "Australia"]
    default_countries = [c for c in popular_defaults if c in country_list]
    if not default_countries:
        default_countries = country_list[:5] if len(country_list) >= 5 else country_list

    selected_countries = st.sidebar.multiselect(
        "Countries",
        options=country_list,
        default=default_countries,
        key="countries_filter",
        help="Select countries to analyze. Leave empty to show all."
    )

    city_search = st.sidebar.text_input("Search City", placeholder="Type city name...", key="city_filter")

    valid_temps = df["temp_display"].dropna()
    if not valid_temps.empty:
        temp_min = float(valid_temps.min())
        temp_max = float(valid_temps.max())
        if temp_min == temp_max:
            temp_min -= 1.0
            temp_max += 1.0
    else:
        temp_min, temp_max = (0.0, 40.0) if not is_imperial else (32.0, 104.0)

    temp_range = st.sidebar.slider(
        f"Temperature Range ({temp_suffix})",
        min_value=temp_min,
        max_value=temp_max,
        value=(temp_min, temp_max),
        step=0.5,
        key="temp_filter"
    )

    valid_winds = df["wind_display"].dropna()
    if not valid_winds.empty:
        wind_min = float(valid_winds.min())
        wind_max = float(valid_winds.max())
        if wind_min == wind_max:
            wind_min -= 1.0
            wind_max += 1.0
    else:
        wind_min, wind_max = (0.0, 100.0) if not is_imperial else (0.0, 60.0)

    wind_range = st.sidebar.slider(
        f"Wind Speed Range ({wind_suffix})",
        min_value=wind_min,
        max_value=wind_max,
        value=(wind_min, wind_max),
        step=1.0,
        key="wind_filter"
    )

    valid_humidity = df["humidity_percent"].dropna()
    if not valid_humidity.empty:
        humidity_min = float(valid_humidity.min())
        humidity_max = float(valid_humidity.max())
        if humidity_min == humidity_max:
            humidity_min -= 5.0
            humidity_max += 5.0
    else:
        humidity_min, humidity_max = (0.0, 100.0)

    humidity_range = st.sidebar.slider(
        "Humidity Range (%)",
        min_value=humidity_min,
        max_value=humidity_max,
        value=(humidity_min, humidity_max),
        step=1.0,
        key="humidity_filter"
    )

    condition_list = sorted(df["Condition Category"].dropna().unique().tolist())
    selected_conditions = st.sidebar.multiselect(
        "Conditions",
        options=condition_list,
        default=[],
        key="conditions_filter",
        help="Filter by general weather categories."
    )

    df_filtered = df.copy()

    if selected_countries:
        df_filtered = df_filtered[df_filtered["country"].isin(selected_countries)]

    if city_search:
        df_filtered = df_filtered[
            df_filtered["city"].str.contains(city_search, case=False, na=False)
        ]

    df_filtered = df_filtered[
        (df_filtered["temp_display"] >= temp_range[0])
        & (df_filtered["temp_display"] <= temp_range[1])
    ]

    df_filtered = df_filtered[
        (df_filtered["wind_display"] >= wind_range[0])
        & (df_filtered["wind_display"] <= wind_range[1])
    ]

    df_filtered = df_filtered[
        (df_filtered["humidity_percent"] >= humidity_range[0])
        & (df_filtered["humidity_percent"] <= humidity_range[1])
    ]

    if selected_conditions:
        df_filtered = df_filtered[df_filtered["Condition Category"].isin(selected_conditions)]

    if df_filtered.empty:
        st.markdown("""
        <div style='background-color: #182026; border: 1px solid #c53030; border-top: 3px solid #c53030; border-radius: 4px; padding: 24px; text-align: center; margin-top: 20px;'>
            <h3 style='color: #F5F8FA; margin-top: 0;'>No Records Match Active Filters</h3>
            <p style='color: #A7B6C2; margin-bottom: 20px;'>The selected geographic, range, or weather condition filters have narrowed the dataset down to 0 rows. Adjust the sliders or dropdowns in the sidebar, or reset to defaults below.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        col_btn_l, col_btn_m, col_btn_r = st.columns([2, 1, 2])
        with col_btn_m:
            if st.button("Reset All Filters", key="empty_state_reset_btn"):
                for key in ["countries_filter", "city_filter", "temp_filter", "wind_filter", "humidity_filter", "conditions_filter"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        st.stop()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Export Options")

    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        label=f"Export ({len(df_filtered)} rows)",
        data=csv,
        file_name="weather_data_filtered.csv",
        mime="text/csv",
        key="sidebar_download_btn"
    )

    last_scrape_raw = df["scraped_at"].max()
    last_scrape = last_scrape_raw.split(" ")[0] if isinstance(last_scrape_raw, str) and " " in last_scrape_raw else str(last_scrape_raw)

    st.sidebar.markdown(f"""
    <div style='background-color: #182026; border: 1px solid #30404D; border-radius: 4px; padding: 12px; margin-top: 20px;'>
        <div style='font-size: 0.72rem; color: #A7B6C2; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;'>System Telemetry</div>
        <div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>
            <span style='font-size: 0.78rem; color: #A7B6C2;'>Status:</span>
            <span style='font-size: 0.78rem; color: #0F9960; font-weight: bold;'>● ONLINE</span>
        </div>
        <div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>
            <span style='font-size: 0.78rem; color: #A7B6C2;'>Database Rows:</span>
            <span style='font-size: 0.78rem; color: #F5F8FA; font-weight: bold; font-family: monospace;'>{len(df)}</span>
        </div>
        <div style='display: flex; justify-content: space-between;'>
            <span style='font-size: 0.78rem; color: #A7B6C2;'>Last Scrape:</span>
            <span style='font-size: 0.78rem; color: #F5F8FA; font-family: monospace;'>{last_scrape}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Observations</div>
            <div class="metric-value">{len(df_filtered)}</div>
            <div class="metric-subtitle">Total records: {len(df)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Countries</div>
            <div class="metric-value">{df_filtered["country"].nunique()}</div>
            <div class="metric-subtitle">Total monitored: {df["country"].nunique()}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        avg_temp = df_filtered["temp_display"].mean()
        val_str = f"{avg_temp:.1f} {temp_suffix}" if pd.notna(avg_temp) else "N/A"
        global_avg_temp = df["temp_display"].mean()
        diff = avg_temp - global_avg_temp if pd.notna(avg_temp) and pd.notna(global_avg_temp) else 0.0
        diff_str = f"{diff:+.1f} {temp_suffix} vs global" if diff != 0.0 else "Matches global avg"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg Temperature</div>
            <div class="metric-value">{val_str}</div>
            <div class="metric-subtitle">{diff_str}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        avg_humidity = df_filtered["humidity_percent"].mean()
        val_humidity = f"{avg_humidity:.0f}%" if pd.notna(avg_humidity) else "N/A"
        avg_wind = df_filtered["wind_display"].mean()
        val_wind = f"{avg_wind:.1f} {wind_suffix}" if pd.notna(avg_wind) else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Humidity & Wind</div>
            <div class="metric-value">{val_humidity} / {val_wind}</div>
            <div class="metric-subtitle">Average values</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    heat_cities = df_filtered[df_filtered["temperature_celsius"] > 35]
    cold_cities = df_filtered[df_filtered["temperature_celsius"] < 5]
    wind_cities = df_filtered[df_filtered["wind_speed_kmh"] > 40]

    alerts = []
    for _, row in heat_cities.iterrows():
        alerts.append(f"**Extreme Heat Warning**: {row['city']}, {row['country']} is reporting {row['temp_display']}{temp_suffix} (threshold > 35°C)")
    for _, row in cold_cities.iterrows():
        alerts.append(f"**Freeze Warning**: {row['city']}, {row['country']} is reporting {row['temp_display']}{temp_suffix} (threshold < 5°C)")
    for _, row in wind_cities.iterrows():
        alerts.append(f"**High Wind Advisory**: {row['city']}, {row['country']} is reporting wind speeds of {row['wind_display']} {wind_suffix} (threshold > 40 km/h)")

    if alerts:
        with st.expander("Active Environmental Anomalies", expanded=False):
            st.markdown(f"**The system has detected {len(alerts)} active environmental anomalies matching your current filters:**")
            for alert in alerts:
                st.markdown(alert)
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview & Map", "Temperature Analysis", "Wind & Humidity", "Weather Conditions", "Data Explorer & Pipeline"]
    )

    plotly_layout_args = dict(
        font_family="Inter",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#A7B6C2",
        title_font_size=14,
        title_font_family="Inter",
        title_font_color="#F5F8FA",
        legend=dict(
            bgcolor="#182026",
            bordercolor="#30404D",
            borderwidth=1,
            font=dict(color="#A7B6C2")
        ),
        margin=dict(l=40, r=20, t=50, b=40)
    )

    with tab1:
        st.subheader("Global Temperature & Ranking")
        col_map, col_ranking = st.columns([3, 2])

        avg_by_country = (
            df_filtered.groupby("country")["temp_display"]
            .mean()
            .reset_index()
            .sort_values("temp_display", ascending=False)
        )

        avg_by_country_map = avg_by_country.copy()
        country_mappings = {
            "USA": "United States",
            "UK": "United Kingdom",
            "UAE": "United Arab Emirates"
        }
        avg_by_country_map["country"] = avg_by_country_map["country"].replace(country_mappings)

        with col_map:
            fig_map = px.choropleth(
                avg_by_country_map,
                locations="country",
                locationmode="country names",
                color="temp_display",
                color_continuous_scale="sunsetdark",
                labels={"temp_display": f"Temp ({temp_suffix})", "country": "Country"},
                title="Global Temperature Heatmap"
            )
            fig_map.update_layout(**plotly_layout_args)
            fig_map.update_layout(
                margin=dict(l=0, r=0, t=40, b=0),
                height=450,
                geo=dict(
                    bgcolor="rgba(0,0,0,0)",
                    showframe=False,
                    showcoastlines=True, coastlinecolor="rgba(255,255,255,0.15)",
                    showland=True, landcolor="#1e293b",
                    showocean=True, oceancolor="#090d16",
                    showlakes=False,
                    showcountries=True, countrycolor="rgba(255,255,255,0.1)",
                    projection_type="natural earth"
                )
            )
            st.plotly_chart(fig_map, use_container_width=True)

        with col_ranking:
            col_warm, col_cool = st.columns(2)
            
            with col_warm:
                warmest_countries = avg_by_country.head(10)
                fig_warm = px.bar(
                    warmest_countries,
                    x="temp_display",
                    y="country",
                    orientation="h",
                    title=f"Warmest Regions ({temp_suffix})",
                    labels={"temp_display": f"Temp ({temp_suffix})", "country": "Country"},
                    color="temp_display",
                    color_continuous_scale="sunsetdark"
                )
                fig_warm.update_layout(**plotly_layout_args)
                fig_warm.update_layout(showlegend=False, coloraxis_showscale=False)
                fig_warm.update_traces(
                    hovertemplate="<b>%{y}</b><br>Avg Temperature: %{x:.1f} " + temp_suffix + "<extra></extra>"
                )
                fig_warm.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
                fig_warm.update_yaxes(showgrid=False, linecolor="rgba(255,255,255,0.1)", categoryorder="total ascending")
                st.plotly_chart(fig_warm, use_container_width=True)
                
            with col_cool:
                coolest_countries = avg_by_country.tail(10)
                fig_cool = px.bar(
                    coolest_countries,
                    x="temp_display",
                    y="country",
                    orientation="h",
                    title=f"Coolest Regions ({temp_suffix})",
                    labels={"temp_display": f"Temp ({temp_suffix})", "country": "Country"},
                    color="temp_display",
                    color_continuous_scale="ice"
                )
                fig_cool.update_layout(**plotly_layout_args)
                fig_cool.update_layout(showlegend=False, coloraxis_showscale=False)
                fig_cool.update_traces(
                    hovertemplate="<b>%{y}</b><br>Avg Temperature: %{x:.1f} " + temp_suffix + "<extra></extra>"
                )
                fig_cool.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
                fig_cool.update_yaxes(showgrid=False, linecolor="rgba(255,255,255,0.1)", categoryorder="total ascending")
                st.plotly_chart(fig_cool, use_container_width=True)

    with tab2:
        st.subheader("Temperature Distribution & Statistical Spreads")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            fig2 = px.histogram(
                df_filtered,
                x="temp_display",
                nbins=15,
                title=f"Temperature Frequency Distribution ({temp_suffix})",
                labels={"temp_display": f"Temperature ({temp_suffix})"},
                marginal=None,
                color_discrete_sequence=["#137CBD"]
            )
            fig2.update_layout(**plotly_layout_args)
            fig2.update_xaxes(showgrid=False, linecolor="rgba(255,255,255,0.1)")
            fig2.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
            st.plotly_chart(fig2, use_container_width=True)

        with col_chart2:
            fig5 = px.scatter(
                df_filtered,
                x="temp_display",
                y="humidity_percent",
                color="Condition Category",
                hover_data=["city", "country", "condition"],
                title=f"Humidity vs. Temperature ({temp_suffix})",
                labels={
                    "temp_display": f"Temperature ({temp_suffix})",
                    "humidity_percent": "Humidity (%)"
                },
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig5.update_layout(**plotly_layout_args)
            fig5.update_layout(legend_title_text="Condition Category")
            fig5.update_traces(
                customdata=df_filtered[["city", "country", "condition"]].values,
                hovertemplate="<b>%{customdata[0]}, %{customdata[1]}</b><br>Temp: %{x:.1f}" + temp_suffix + "<br>Humidity: %{y}%<br>Condition: %{customdata[2]}<extra></extra>"
            )
            fig5.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
            fig5.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
            st.plotly_chart(fig5, use_container_width=True)

        temp_std = df_filtered["temp_display"].std()
        temp_var = df_filtered["temp_display"].var()
        temp_median = df_filtered["temp_display"].median()
        
        st.markdown(f"""
        <div style='background-color: #182026; border: 1px solid #30404D; border-radius: 4px; padding: 16px; margin-top: 15px;'>
            <div style='font-size: 0.78rem; color: #A7B6C2; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;'>Statistical Analytics Summary</div>
            <div style='display: flex; gap: 3rem;'>
                <div>
                    <span style='color: #A7B6C2; font-size: 0.85rem;'>Median Temperature:</span>
                    <span style='color: #F5F8FA; font-size: 1.1rem; font-weight: bold; margin-left: 6px; font-family: monospace;'>{temp_median:.1f} {temp_suffix}</span>
                </div>
                <div>
                    <span style='color: #A7B6C2; font-size: 0.85rem;'>Standard Deviation:</span>
                    <span style='color: #F5F8FA; font-size: 1.1rem; font-weight: bold; margin-left: 6px; font-family: monospace;'>{temp_std:.2f}</span>
                </div>
                <div>
                    <span style='color: #A7B6C2; font-size: 0.85rem;'>Variance:</span>
                    <span style='color: #F5F8FA; font-size: 1.1rem; font-weight: bold; margin-left: 6px; font-family: monospace;'>{temp_var:.2f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.subheader("Wind Speed & Atmospheric Pressure Telemetry")
        col_wind1, col_wind2 = st.columns(2)

        with col_wind1:
            fig_wind = px.box(
                df_filtered,
                x="country",
                y="wind_display",
                title=f"Wind Speed Variation by Country ({wind_suffix})",
                labels={"wind_display": f"Wind Speed ({wind_suffix})", "country": "Country"},
                color="country",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_wind.update_layout(**plotly_layout_args)
            fig_wind.update_layout(showlegend=False)
            fig_wind.update_xaxes(showgrid=False, linecolor="rgba(255,255,255,0.1)")
            fig_wind.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
            st.plotly_chart(fig_wind, use_container_width=True)

        with col_wind2:
            fig_wind_press = px.scatter(
                df_filtered,
                x="pressure_display",
                y="wind_display",
                color="Condition Category",
                hover_data=["city", "country", "condition"],
                title=f"Wind Speed vs. Atmospheric Pressure ({wind_suffix} vs {pressure_suffix})",
                labels={
                    "pressure_display": f"Pressure ({pressure_suffix})",
                    "wind_display": f"Wind Speed ({wind_suffix})"
                },
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_wind_press.update_layout(**plotly_layout_args)
            fig_wind_press.update_layout(legend_title_text="Condition Category")
            fig_wind_press.update_traces(
                customdata=df_filtered[["city", "country", "condition"]].values,
                hovertemplate="<b>%{customdata[0]}, %{customdata[1]}</b><br>Pressure: %{x:.2f} " + pressure_suffix + "<br>Wind: %{y:.1f} " + wind_suffix + "<br>Condition: %{customdata[2]}<extra></extra>"
            )
            fig_wind_press.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
            fig_wind_press.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
            st.plotly_chart(fig_wind_press, use_container_width=True)

    with tab4:
        st.subheader("Weather Conditions Distribution & Spreads")
        col_cond1, col_cond2 = st.columns(2)

        with col_cond1:
            condition_counts = (
                df_filtered["Condition Category"].value_counts().reset_index()
            )
            condition_counts.columns = ["Condition Category", "count"]

            fig3 = px.pie(
                condition_counts,
                names="Condition Category",
                values="count",
                title="Weather Condition Frequency Share",
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig3.update_layout(**plotly_layout_args)
            fig3.update_layout(legend_title_text="Condition Category")
            fig3.update_traces(
                textposition="inside", 
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>"
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col_cond2:
            fig4 = px.box(
                df_filtered,
                x="Condition Category",
                y="temp_display",
                title=f"Temperature Spreads by Weather Condition ({temp_suffix})",
                labels={"temp_display": f"Temperature ({temp_suffix})"},
                color="Condition Category",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig4.update_layout(**plotly_layout_args)
            fig4.update_layout(showlegend=False)
            fig4.update_xaxes(showgrid=False, linecolor="rgba(255,255,255,0.1)")
            fig4.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)")
            st.plotly_chart(fig4, use_container_width=True)

    with tab5:
        st.subheader("Database Explorer & Architecture")
        
        col_explorer, col_methodology = st.columns([3, 2])
        
        with col_explorer:
            st.markdown(f"**Showing {len(df_filtered)} records** matching your active filters.")
            
            csv_data = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"Export table ({len(df_filtered)} rows)",
                data=csv_data,
                file_name="weather_explorer_data.csv",
                mime="text/csv",
                key="tab4_download_btn"
            )
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

            df_explorer = df_filtered[
                [
                    "city",
                    "country",
                    "temp_display",
                    "condition",
                    "humidity_percent",
                    "wind_display",
                    "pressure_display",
                    "local_time",
                ]
            ].rename(columns={
                "city": "City",
                "country": "Country",
                "temp_display": "Temperature",
                "condition": "Condition",
                "humidity_percent": "Humidity",
                "wind_display": "Wind Speed",
                "pressure_display": "Pressure",
                "local_time": "Observation Time"
            })
            
            st.dataframe(
                df_explorer,
                column_config={
                    "Humidity": st.column_config.ProgressColumn(
                        label="Humidity (%)",
                        min_value=0,
                        max_value=100,
                        format="%d%%"
                    ),
                    "Temperature": st.column_config.NumberColumn(
                        label=f"Temperature ({temp_suffix})",
                        format="%.1f"
                    ),
                    "Wind Speed": st.column_config.NumberColumn(
                        label=f"Wind Speed ({wind_suffix})",
                        format="%.1f"
                    ),
                    "Pressure": st.column_config.NumberColumn(
                        label=f"Pressure ({pressure_suffix})",
                        format="%.2f" if is_imperial else "%.1f"
                    )
                },
                use_container_width=True,
                hide_index=True,
            )

        with col_methodology:
            st.markdown(r"""
            ### Data Pipeline Architecture
            
            This application processes global weather data through a clean four-step pipeline:
            
            1. Scraping: A headless Selenium script gathers current weather pages from TimeAndDate.com. It waits dynamically for elements to render and simulates user browsing to ensure reliable scraping.
            2. Cleaning: A Pandas pipeline standardizes column headers, strips extra whitespace, and parses numeric readings from raw text using regular expressions. Calm wind speeds are safely normalized.
            3. Warehousing: Clean records are loaded into a local SQLite database. Uniqueness constraints on the city name and local observation timestamp prevent duplicate entries.
            4. Dashboard: Streamlit queries the database, handles unit conversions, and renders charts using Plotly.
            
            ### Calculations and Conversions
            
            1. Temperature: Converted from Fahrenheit to Celsius where Celsius equals Fahrenheit minus 32, multiplied by five-ninths.
            2. Wind Speed: Converted from miles per hour to kilometers per hour where 1 mph equals 1.60934 km/h.
            3. Pressure: Converted from inches of Mercury to hectopascals where 1 inHg equals 33.8639 hPa.
            """)


if __name__ == "__main__":
    main()
