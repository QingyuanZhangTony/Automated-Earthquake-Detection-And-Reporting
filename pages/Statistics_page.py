import altair as alt
import pandas as pd
import streamlit as st
import plotly.express as px
from logic import render_interactive_map, render_density_mapbox
from streamlit_utils import load_config_to_session, load_summary_to_session, save_config_to_yaml, \
    filtering_options_and_statistics, sidebar_navigation

# 加载配置到 session
load_config_to_session()
# Sidebar navigation
sidebar_navigation()
# 模拟启动时保存设置
if 'settings_initialized' not in st.session_state:
    st.session_state.settings_initialized = True
    save_config_to_yaml(st.session_state)

# 读取汇总数据到 session
summary_status = load_summary_to_session()

# 添加一个变量用于存储选中的点
if "selected_point" not in st.session_state:
    st.session_state.selected_point = None

# Page title
st.title(f"Deployment Statistics for {st.session_state.station_code}")
st.divider()

# 检查 summary 状态
if summary_status == "exist_loaded":

    # 使用expander将过滤选项和统计信息折叠起来
    df_filtered = filtering_options_and_statistics(st.session_state.df.copy(), enable_date_filtering=False)

    # Container for Daily Number of Detected Events Over Station Life Time
    with st.container():
        df_filtered['date'] = pd.to_datetime(df_filtered['date'], errors='coerce').dt.date

        # Ensure data is sorted by date
        df_filtered = df_filtered.sort_values(by='date')

        # Calculate the number of detected events per day
        daily_detected = df_filtered[df_filtered['detected']].groupby('date').size().reset_index(name='daily_detected')

        # Generate the bar chart for daily detected events
        daily_detected_chart = alt.Chart(daily_detected).mark_bar().encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('daily_detected:Q', title='Daily No. Detect'),
            tooltip=['date:T', 'daily_detected:Q']
        ).properties(
            height=300,
            width=700,
            title='Daily Number of Detected Events Over Station Life Time'
        )

        st.altair_chart(daily_detected_chart, use_container_width=True)

    # Scatter Plot for Detected Earthquakes Only
    with st.container():
        df_filtered['date'] = pd.to_datetime(df_filtered['date'], errors='coerce').dt.date

        # Filter for detected and catalogued events
        df_detected = df_filtered[(df_filtered['catalogued'] == True) & (df_filtered['detected'] == True)].copy()

        # Calculate the maximum magnitude and adjust the Y-axis domain
        if not df_detected.empty:
            max_magnitude = df_detected['mag'].max()
            y_max = (max_magnitude // 1) + 1 if pd.notnull(max_magnitude) else 10  # Use a default value if NaN
        else:
            y_max = 10  # Default value if df_detected is empty

        base_chart = alt.Chart(df_detected).mark_point(
            filled=True,
            opacity=1,
            size=50
        ).encode(
            x=alt.X('epi_distance:Q', title=f'Epicentral Distance To Station {st.session_state.station_code} (km)'),
            y=alt.Y('mag:Q', title='Magnitude', scale=alt.Scale(zero=False, domain=[0, y_max]),
                    axis=alt.Axis(tickCount=int(y_max + 1))),
            color=alt.Color('p_confidence:Q', scale=alt.Scale(scheme='blues'), legend=alt.Legend(
                title='Confidence  ', titleOrient='left', orient='right', titleLimit=0, gradientLength=300
            )),
            order=alt.Order(
                'detected',  # Ensures detected events are drawn on top of not detected ones
                sort='ascending'
            ),
            tooltip=[
                alt.Tooltip('time:T', title='Date and Time', format='%Y-%m-%d %H:%M:%S'),
                alt.Tooltip('mag:Q', title='Magnitude'),
                alt.Tooltip('mag_type:N', title='Magnitude Type'),
                alt.Tooltip('lat:Q', title='Latitude'),
                alt.Tooltip('long:Q', title='Longitude'),
                alt.Tooltip('unique_id:N', title='Unique ID'),
                alt.Tooltip('epi_distance:Q', title='Epicentral Distance (km)'),
                alt.Tooltip('depth:Q', title='Depth (km)'),
                alt.Tooltip('p_confidence:Q', title='P-Wave Confidence'),
                alt.Tooltip('p_error:N', title='P-Wave Error'),
                alt.Tooltip('s_confidence:N', title='S-Wave Confidence'),
                alt.Tooltip('s_error:N', title='S-Wave Error')
            ]
        ).properties(
            height=500,
            title='Catalogued Earthquake Detection Overview'
        )

        st.altair_chart(base_chart, use_container_width=True)

    # Density Mapbox Container
    with st.container():
        # Display density mapbox using the provided function
        render_density_mapbox(
            df_filtered,
            station_info={
                "latitude": st.session_state.station_latitude,
                "longitude": st.session_state.station_longitude,
                "code": st.session_state.station_code
            },
            title="Density Map of Detected Earthquakes"
        )

    # Magnitude vs. Confidence Plot
    with st.container():
        mag_vs_confidence_chart = alt.Chart(df_detected).mark_point(
            filled=True,
            opacity=1,
            size=50
        ).encode(
            x=alt.X('mag:Q', title='Magnitude'),
            y=alt.Y('p_confidence:Q', title='P-Wave Confidence'),
            tooltip=[
                alt.Tooltip('time:T', title='Date and Time', format='%Y-%m-%d %H:%M:%S'),
                alt.Tooltip('mag:Q', title='Magnitude'),
                alt.Tooltip('p_confidence:Q', title='P-Wave Confidence')
            ]
        ).properties(
            height=300,
            title='Magnitude vs. Confidence'
        )

        st.altair_chart(mag_vs_confidence_chart, use_container_width=True)

    # Distance vs. Confidence Plot
    with st.container():
        dist_vs_confidence_chart = alt.Chart(df_detected).mark_point(
            filled=True,
            opacity=1,
            size=50
        ).encode(
            x=alt.X('epi_distance:Q', title=f'Epicentral Distance To Station {st.session_state.station_code} (km)'),
            y=alt.Y('p_confidence:Q', title='P-Wave Confidence'),
            tooltip=[
                alt.Tooltip('time:T', title='Date and Time', format='%Y-%m-%d %H:%M:%S'),
                alt.Tooltip('epi_distance:Q', title='Epicentral Distance (km)'),
                alt.Tooltip('p_confidence:Q', title='P-Wave Confidence')
            ]
        ).properties(
            height=300,
            title='Distance vs. Confidence'
        )

        st.altair_chart(dist_vs_confidence_chart, use_container_width=True)

    # Magnitude vs. Distance Histogram
    with st.container():
        magnitude_vs_distance_histogram = alt.Chart(df_detected).mark_rect().encode(
            x=alt.X('epi_distance:Q', bin=alt.Bin(maxbins=30), title=f'Epicentral Distance To Station {st.session_state.station_code} (km)'),
            y=alt.Y('mag:Q', bin=alt.Bin(maxbins=30), title='Magnitude'),
            color=alt.Color('count()', scale=alt.Scale(scheme='blues'), legend=alt.Legend(
                title='Count  ', titleOrient='left', orient='right', titleLimit=0, gradientLength=300
            )),
            tooltip=[
                alt.Tooltip('count():Q', title='Count')
            ]
        ).properties(
            height=400,
            title='Magnitude vs. Distance Histogram'
        )

        st.altair_chart(magnitude_vs_distance_histogram, use_container_width=True)

    # Box Plot of Confidence by Distance Grouped by Magnitude Container
    with st.container():
        # Define bins for epicentral distance and magnitude
        distance_bins = [0, 2000, 4000, 6000, 8000, 10000]
        magnitude_bins = [0, 2, 4, 6, 8]

        # Bin the epicentral distance and magnitude
        df_filtered['distance_bin'] = pd.cut(df_filtered['epi_distance'], bins=distance_bins,
                                             labels=["0-2000", "2000-4000", "4000-6000", "6000-8000", "8000-10000"])
        df_filtered['magnitude_bin'] = pd.cut(df_filtered['mag'], bins=magnitude_bins,
                                              labels=["0-2", "2-4", "4-6", "6-8"])

        # Create box plot
        box_plot = alt.Chart(df_filtered).mark_boxplot(extent='min-max').encode(
            x=alt.X('distance_bin:N', title='Epicentral Distance (km)', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('p_confidence:Q', title='P-Wave Confidence', scale=alt.Scale(zero=False)),
            color=alt.Color('magnitude_bin:N', title='Magnitude Group', scale=alt.Scale(scheme='blues'),
                            legend=alt.Legend(title='Magnitude Group', orient='right')),
        ).properties(
            width=700,
            height=400,
            title='Box Plot of Confidence by Distance Grouped by Magnitude'
        )

        st.altair_chart(box_plot, use_container_width=True)


elif summary_status == "exist_empty":
    st.warning("The summary file is empty. Please check the source or generate new data.")
else:  # summary_status == "not_exist"
    st.warning("The summary file does not exist. Please generate a report first.")
