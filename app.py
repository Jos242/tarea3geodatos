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
        st.error(
            "Error de lectura de datos"
            "(UTF-8/latin1/cp1252)."
        )
        st.stop()

    df = df.dropna(subset=["Latitud", "Longitud"])
    df["Latitud"] = df["Latitud"].astype(float)
    df["Longitud"] = df["Longitud"].astype(float)
    df["Especie"] = df["Especie"].astype(str)
    return df

df = load_data("conejos.csv")

st.title("Especimens de conejos recolectados")
st.markdown("Datos recolectados entre 2016 y 2021 durante un estudio de 5 años para describir una nueva especie de conejo en Costa Rica")
st.markdown("Tarea 3 de datos geoespaciales por José Andrés Mora")

if df.empty:
    st.warning("No hay long o lat")
    st.stop()


tab_table, tab_chart, tab_map = st.tabs(
    ["Tabla de datos", "Gráfico de especies", "Mapa de ubicaciones"]
)

with tab_table:
    st.subheader("Tabla")
    st.write("Estos son los datos recolectados durante el estudio. El estudio completo comprende unos ~150 especimens, sin embargo, solo los mostrados aqui poseen coordenadas válidas, el resto solo poseen una ubicación general (ej: San Carlos, Costa Rica), por lo tanto solo estos son mostrados")
    st.dataframe(
        df,
        use_container_width=True,
        height=800
    )

with tab_chart:
    st.subheader("Distribución por especie")

    counts = (
        df.groupby("Especie")
        .size()
        .reset_index(name="Conteo")
    )

    counts = counts.sort_values("Conteo", ascending=False)

    fig_bar = px.bar(
        counts,
        x="Especie",
        y="Conteo",
        text="Conteo",
        title="Cantidad de especimens por especie supuesta",
        height=800
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(
        xaxis_title="Especie",
        yaxis_title="Cantidad",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )

    st.plotly_chart(fig_bar, use_container_width=True)


with tab_map:
    st.subheader("Mapa de ubicaciones")

    # st.markdown(
    #     "Se puede seleccionar un especimen especifico para solo ver ese"
    # )

 
    # event = st.dataframe(
    #     df,
    #     use_container_width=True,
    #     hide_index=True,
    #     on_select="rerun",        
    #     selection_mode="multi-row"  
    # )
    


    selected_rows = []
    # if event is not None and hasattr(event, "selection"):
    #     selected_rows = event.selection.rows

    if selected_rows:
        map_df = df.iloc[selected_rows]
        #st.info(f"Mostrando {len(map_df)} especimen(s) seleccionados.")
    else:
        map_df = df
    #     st.info("No hay filas seleccionadas")

    unique_species = list(map_df["Especie"].unique())
    palette = ["red", "blue", "green"]

    center_lat = map_df["Latitud"].mean()
    center_lon = map_df["Longitud"].mean()

    species_color_map = {
        esp: palette[i % len(palette)]
        for i, esp in enumerate(unique_species)
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
        color_discrete_map=species_color_map
    )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": center_lat, "lon": center_lon},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(
            orientation="h",          
            yanchor="bottom",
            y=0.01,                   
            xanchor="left",
            x=0.01,                  
            # bgcolor="rgba(255,255,255,0.7)" 
        ),
    )


    fig_map.update_traces(
        marker=dict(
            size=11,
            # opacity=1
        )
    )


    st.plotly_chart(fig_map, use_container_width=True)


st.caption(
    "Gracias a los dueños de los datos y autores del proyecto: Dr. José Manuel Mora Benavides, Dr. Luis A. Ruedas, Universidad de Portland, Universidad de Costa Rica, Universidad Técnica Nacional"
)
