import pandas as pd
import plotly.express as px
import numpy as np
import streamlit as st

def plot_bar_status(df: pd.DataFrame) -> None:

    if df is None or df.empty:
        st.warning("Sem dados para gerar o gráfico.")
        return

    df_status = df[df['Status'].isin(['APROVADO (SEM ODD)', 'ALERTA (VOLUME BAIXO)', 'ALERTA (ODD BAIXA)'])]

    df_agrupado = df_status.groupby('Status')['VALOR'].sum().reset_index()

    if df_agrupado.empty:
        st.warning("Sem dados para gerar o gráfico.")
        return

    fig = px.bar(
        df_agrupado,
        x='Status',
        y='Valores',
        title='Tendencias do mercado de gols',
        orientation='h'
    )

    fig.update_traces(
        textfont=dict(weight="bold", family="Arial", color="black", size=14),
        textposition="inside",
        texttemplate="R$ %{x:.1f}",
        cliponaxis=False  
    )

    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})