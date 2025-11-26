import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(
    page_title="Avistamientos de conejos en Costa Rica",
    layout="wide"
)


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    for enc in ["utf-8", "latin1", "cp1252"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        st.error("Error de lectura de datos (UTF-8/latin1/cp1252).")
        st.stop()


    df.columns = df.columns.str.strip()


    df["Latitud"] = pd.to_numeric(df["Latitud"], errors="coerce")
    df["Longitud"] = pd.to_numeric(df["Longitud"], errors="coerce")
    df["Especie"] = df["Especie"].astype(str)

    if "Altitud" in df.columns:
        df["Altitud"] = pd.to_numeric(df["Altitud"], errors="coerce")

    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")


    df = df.dropna(subset=["Latitud", "Longitud"])

    return df


df = load_data("conejos.csv")

st.title("Especímenes de conejos recolectados")
st.markdown(
    "Datos recolectados entre 2016 y 2021 durante un estudio de 5 años "
    "para describir una nueva especie de conejo en Costa Rica"
)
st.markdown("Proyecto de datos geoespaciales por José Andrés Mora")

if df.empty:
    st.warning("No hay registros con latitud/longitud válidos.")
    st.stop()


species_options = sorted(df["Especie"].dropna().unique().tolist())

has_fecha = ("Fecha" in df.columns) and df["Fecha"].notna().any()
if has_fecha:
    global_min_dt = df["Fecha"].min().to_pydatetime()
    global_max_dt = df["Fecha"].max().to_pydatetime()

has_alt = ("Altitud" in df.columns) and df["Altitud"].notna().any()
if has_alt:
    global_alt_min = int(df["Altitud"].min())
    global_alt_max = int(df["Altitud"].max())


st.sidebar.header("Filtros")


if "species_filter" not in st.session_state:
    st.session_state["species_filter"] = species_options
if "lugar_filter" not in st.session_state:
    st.session_state["lugar_filter"] = ""
if has_fecha and "fecha_filter" not in st.session_state:
    st.session_state["fecha_filter"] = (global_min_dt, global_max_dt)
if has_alt and "alt_filter" not in st.session_state:
    st.session_state["alt_filter"] = (global_alt_min, global_alt_max)

def reset_filters():
    st.session_state["species_filter"] = species_options
    st.session_state["lugar_filter"] = ""
    if has_fecha:
        st.session_state["fecha_filter"] = (global_min_dt, global_max_dt)
    if has_alt:
        st.session_state["alt_filter"] = (global_alt_min, global_alt_max)

st.sidebar.button("Resetear filtros", on_click=reset_filters)


selected_species = st.sidebar.multiselect(
    "Especie",
    options=species_options,
    key="species_filter",
)

lugar_text = st.sidebar.text_input(
    "Lugar contiene",
    placeholder="Ej: San Carlos",
    key="lugar_filter",
)

if has_fecha:
    start_dt, end_dt = st.sidebar.slider(
        "Rango de fechas",
        min_value=global_min_dt,
        max_value=global_max_dt,
        key="fecha_filter",
    )
else:
    start_dt, end_dt = None, None

if has_alt:
    alt_min_sel, alt_max_sel = st.sidebar.slider(
        "Rango de altitud (m)",
        min_value=global_alt_min,
        max_value=global_alt_max,
        step=10,
        key="alt_filter",
    )
else:
    alt_min_sel, alt_max_sel = None, None



filtered_df = df.copy()

if selected_species:
    filtered_df = filtered_df[filtered_df["Especie"].isin(selected_species)]

if lugar_text:
    filtered_df = filtered_df[
        filtered_df["Lugar"].astype(str).str.contains(lugar_text, case=False, na=False)
    ]

if has_fecha and start_dt and end_dt:
    start_ts = pd.to_datetime(start_dt)
    end_ts = pd.to_datetime(end_dt)
    filtered_df = filtered_df[
        filtered_df["Fecha"].between(start_ts, end_ts, inclusive="both")
    ]

if has_alt and alt_min_sel is not None and alt_max_sel is not None:
    filtered_df = filtered_df[
        filtered_df["Altitud"].between(alt_min_sel, alt_max_sel, inclusive="both")
    ]

if filtered_df.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
    st.stop()


tab_info, tab_table, tab_chart, tab_map, tab_lessons = st.tabs(
    [
        "Descripción y preguntas",
        "Tabla de datos",
        "Gráficos",
        "Mapa de ubicaciones",
        "Lecciones y trabajo futuro",
    ]
)


with tab_info:
    st.subheader("Descripción de los datos")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros (totales)", 157)
    c2.metric("Registros (filtrados)", f"{len(filtered_df):,}")
    c3.metric("Especies", f"{df['Especie'].nunique():,}")
    if has_fecha:
        c4.metric("Rango de fechas", f"{df['Fecha'].min().date()} → {df['Fecha'].max().date()}")
    else:
        c4.metric("Rango de fechas", "No disponible")

    st.markdown("#### ¿Qué contiene este conjunto de datos?")
    st.markdown(
        "- Los datos son registros de ~150 especimenes de conejos recolectados en Costa Rica durante 2015-2021, con el objetivo de aprender mas sobre su taxonomía y distribución, y de ser posible utilizar estos datos para describir una nueva especie de conejo\n"
        "- Los datos fueron obtenidos lo mas sistematicamente posible, intentando evitar sesgos\n"
        "- Registros de especímenes con coordenadas (lat/long) para poder mapearlos.\n"
        "- Atributos como Especie, Lugar, Fecha, Altitud, y otros campos morfológicos.\n"
        "- Para este proyecto solo estamos utilizando los especímenes con coordenadas válidas, ya que muchos solo poseen una ubicación general (ej: San Carlos, Costa Rica)"
    )


    st.markdown("#### Preguntas a contestar")
    st.markdown(
        "- ¿En qué zonas aparece cada especie?\n"
        "- ¿Hay especies asociadas a altitudes más altas o bajas?\n"
        "- ¿Cual especia es más común?\n\n"
    )



with tab_table:
    st.subheader("Tabla")
    st.write(
        "Estos son los datos recolectados durante el estudio. El estudio completo comprende unos ~150 especímenes, "
        "sin embargo, solo los mostrados aquí poseen coordenadas válidas."
    )
    st.dataframe(filtered_df, use_container_width=True, height=800)


with tab_chart:
    st.subheader("Visualización de datos")

    opciones = ["Conteo por especie", "Altitud por especie", "Serie temporal (año)"]
    chart_type = st.radio("Tipo de gráfico", opciones, horizontal=True)

    if chart_type == "Conteo por especie":
        counts = filtered_df.groupby("Especie").size().reset_index(name="Conteo")
        counts = counts.sort_values("Conteo", ascending=False)

        fig_bar = px.bar(
            counts,
            x="Especie",
            y="Conteo",
            text="Conteo",
            title="Cantidad de especímenes por especie",
            height=700,
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(xaxis_title="Especie", yaxis_title="Cantidad")
        st.plotly_chart(fig_bar, use_container_width=True)

    elif chart_type == "Altitud por especie":
        if has_alt:
            fig_box = px.box(
                filtered_df.dropna(subset=["Altitud"]),
                x="Especie",
                y="Altitud",
                points="all",
                title="Distribución de altitud por especie",
                height=700,
            )
            fig_box.update_layout(xaxis_title="Especie", yaxis_title="Altitud (m)")
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("No hay columna de altitud disponible.")

    elif chart_type == "Serie temporal (año)":
        if has_fecha:
            tmp = filtered_df.dropna(subset=["Fecha"]).copy()
            tmp["Año"] = tmp["Fecha"].dt.year
            df_year = tmp.groupby("Año").size().reset_index(name="Conteo")

            if df_year.empty:
                st.info("No hay fechas válidas para construir la serie temporal.")
            else:
                fig_line = px.line(
                    df_year,
                    x="Año",
                    y="Conteo",
                    markers=True,
                    title="Cantidad de especímenes por año",
                    height=700,
                )
                fig_line.update_layout(xaxis_title="Año", yaxis_title="Cantidad")
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No hay columna de fecha disponible.")


with tab_map:
    st.subheader("Mapa de ubicaciones")

    map_df = filtered_df

    unique_species = list(map_df["Especie"].unique())
    palette = ["red", "blue", "green", "orange", "purple", "brown"]

    center_lat = map_df["Latitud"].mean()
    center_lon = map_df["Longitud"].mean()

    species_color_map = {
        esp: palette[i % len(palette)] for i, esp in enumerate(unique_species)
    }

    fig_map = px.scatter_mapbox(
        map_df,
        lat="Latitud",
        lon="Longitud",
        color="Especie",
        hover_name="Especie",
        hover_data={col: True for col in map_df.columns if col not in ["Latitud", "Longitud"]},
        zoom=8 if len(map_df) == 1 else 7,
        height=800,
        color_discrete_map=species_color_map,
    )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": center_lat, "lon": center_lon},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01),
    )

    fig_map.update_traces(marker=dict(size=11))
    st.plotly_chart(fig_map, use_container_width=True)


with tab_lessons:
    st.subheader("Lecciones aprendidas y sugerencias de trabajo futuro")

    st.markdown("### 1) Trabajando con datos geoespaciales")
    st.markdown(
        "- Validación y datos de calidad: revisar rangos, outliers y puntos duplicados antes de interpretar patrones.\n"
        "- CRS: aunque aquí usamos lat/long (WGS84), al trabajar en Costa Rica y con ciertas capas oficiales, es mejor usar CR-SIRGAS.\n"
        "- Sesgo de muestreo: un mapa “bonito” no significa distribución real, puede reflejar accesibilidad del muestreo.\n"
    )

    st.markdown("### 2) Con Python y Streamlit")
    st.markdown(
        "- Pandas limpia, Streamlit muestra: normalizar columnas, convertir tipos y manejar NaNs evita bugs de filtros.\n"
        "- Estado (session_state): necesario para resetear filtros y mantener la UI consistente.\n"
        "- Cache (st.cache_data): acelera recargas, sobre todo si se usan joins, shapefiles o calculos pesados.\n"
    )

    st.markdown("### 3) Usando estos datos para el proyecto")
    st.markdown(
        "- Faltantes y cobertura: si solo se incluyen registros con coordenadas, cualquier conclusión espacial es sobre ese subconjunto.\n"
        "- Lugar vs coordenada: el texto de “Lugar” puede ser muy general, para análisis espacial importa mas la coordenada.\n"
        "- Altitud: es una variable importante, pero requiere controlar por sesgo de muestreo y por especie.\n"
    )

    st.markdown("### Para trabajo futuro")
    st.markdown(
        "- Mapa de densidad/heatmap (o clustering) para ver hotspots sin sobrecargar de puntos.\n"
        "- Histograma de altitud (global y por especie) para comparar distribuciones.\n"
        "- Mas capas geoespaciales: El objetivo inicial era utilizar capas como la de covertura forestal para realizar otros analisis, sin embargo debido a problemas de tiempo no pude solucionar el problema de que eran muy pesados, entonces seria algo que me gustaria solucionar en el futuro"
    )


st.caption(
    "Gracias a los dueños de los datos y autores del proyecto: "
    "Dr. José Manuel Mora Benavides, Dr. Luis A. Ruedas, Universidad de Portland, "
    "Universidad de Costa Rica, Universidad Técnica Nacional"
)
