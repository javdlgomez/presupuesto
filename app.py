import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# ------------------------------
# 1. Datos iniciales
# ------------------------------
def generar_datos_gastos_inicial(n_rows=20):
    """DataFrame ficticio de gastos:
       Fecha, Categoría, Monto, Tipo (tarjeta/otro)."""
    fechas = pd.date_range(start="2025-03-01", end="2025-04-30", freq="D")
    categorias = ["Impuestos", "Renta", "Transporte", "Carro", "Gasolina",
                  "Comida Trabajo", "Comida Casa", "Medicinas", "Suplementos",
                  "Gimnasio", "Aseo", "Internet", "Celular", "Suscripciones",
                  "Pago mensual señora", "Novia", "Ahorro", "Deudas/Pagos Recurrentes"]
    tipos = ["tarjeta", "otro"]
    np.random.seed(42)
    df = pd.DataFrame({
        "Fecha": np.random.choice(fechas, size=n_rows),
        "Categoría": np.random.choice(categorias, size=n_rows),
        "Monto": np.random.randint(50, 500, size=n_rows),
        "Tipo": np.random.choice(tipos, size=n_rows),
    })
    return df

def generar_presupuesto_inicial():
    """Presupuesto mensual (solo gastos) por categoría."""
    data = {
        "Categoría": [
            "Impuestos", "Renta", "Transporte", "Carro", "Gasolina",
            "Comida Trabajo", "Comida Casa", "Medicinas", "Suplementos",
            "Gimnasio", "Aseo", "Internet", "Celular", "Suscripciones",
            "Pago mensual señora", "Novia", "Ahorro", "Deudas/Pagos Recurrentes"
        ],
        "Presupuesto Asignado": [
            700, 2000, 150, 1000, 1000,
            900, 1500, 1500, 500,
            250, 500, 100, 200, 250,
            1500, 1000, 2000, 800
        ]
    }
    return pd.DataFrame(data)

def generar_ingresos_inicial():
    """Tabla separada para manejar Ingresos (Salario / Flexible)."""
    data = {
        "Fuente": ["Salario", "Flexible"],
        "Monto": [14000, 1000]
    }
    return pd.DataFrame(data)

# ------------------------------
# 2. Forecast Semanal (Naive)
# ------------------------------
def forecast_semanal_naive(df, n_weeks=4):
    """
    Calcula promedio semanal y proyecta n_weeks.
    Devuelve DataFrame con 'Semana' y 'Gasto Proyectado'.
    """
    if df.empty:
        return pd.DataFrame(columns=["Semana", "Gasto Proyectado"])
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df_sem = df.groupby(pd.Grouper(key="Fecha", freq="W"))["Monto"].sum().reset_index()
    df_sem.rename(columns={"Monto": "Gasto Semanal"}, inplace=True)
    gasto_promedio = df_sem["Gasto Semanal"].mean()
    ultima_semana = df_sem["Fecha"].max()
    if pd.isnull(ultima_semana):
        ultima_semana = datetime.today()
    fechas_futuras = [ultima_semana + timedelta(weeks=i+1) for i in range(n_weeks)]
    df_forecast = pd.DataFrame({
        "Semana": fechas_futuras,
        "Gasto Proyectado": [gasto_promedio] * n_weeks
    })
    return df_forecast

# ------------------------------
# 3. Aplicación Streamlit
# ------------------------------
def main():
    st.set_page_config(page_title="Control de Gastos", layout="wide")
    st.title("Control Semanal de Gastos y Presupuesto")

    # Estado de sesión
    if "df_gastos" not in st.session_state:
        st.session_state["df_gastos"] = generar_datos_gastos_inicial()
    if "df_presupuesto" not in st.session_state:
        st.session_state["df_presupuesto"] = generar_presupuesto_inicial()
    if "df_ingresos" not in st.session_state:
        st.session_state["df_ingresos"] = generar_ingresos_inicial()

    # Edición de tablas
    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1:
        st.subheader("Gastos")
        edit_gastos = st.data_editor(st.session_state["df_gastos"], num_rows="dynamic")
        if st.button("Guardar Gastos"):
            st.session_state["df_gastos"] = edit_gastos
            st.success("Gastos actualizados")

    with col2:
        st.subheader("Presupuesto Mensual")
        edit_presupuesto = st.data_editor(st.session_state["df_presupuesto"])
        if st.button("Guardar Presupuesto"):
            st.session_state["df_presupuesto"] = edit_presupuesto
            st.success("Presupuesto actualizado")

    with col3:
        st.subheader("Ingresos")
        edit_ingresos = st.data_editor(st.session_state["df_ingresos"])
        if st.button("Guardar Ingresos"):
            st.session_state["df_ingresos"] = edit_ingresos
            st.success("Ingresos actualizados")

    df_gastos = st.session_state["df_gastos"].copy()
    df_presupuesto = st.session_state["df_presupuesto"].copy()
    df_ingresos = st.session_state["df_ingresos"].copy()

    # KPIs
    total_gastos = df_gastos["Monto"].sum() if not df_gastos.empty else 0
    total_presupuesto = df_presupuesto["Presupuesto Asignado"].sum() if not df_presupuesto.empty else 0
    total_ingresos = df_ingresos["Monto"].sum() if not df_ingresos.empty else 0
    saldo = total_ingresos - total_gastos

    st.subheader("Indicadores Clave")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ingresos Totales", f"{total_ingresos:,.0f}")
    k2.metric("Gastos Totales", f"{total_gastos:,.0f}")
    k3.metric("Saldo (Ingresos - Gastos)", f"{saldo:,.0f}")
    k4.metric("Presupuesto Mensual (Gastos)", f"{total_presupuesto:,.0f}")

    st.subheader("Tendencia Semanal de Gastos")
    if not df_gastos.empty:
        df_gastos["Fecha"] = pd.to_datetime(df_gastos["Fecha"], errors="coerce")
        df_sem = df_gastos.groupby(pd.Grouper(key="Fecha", freq="W"))["Monto"].sum().reset_index()
        df_sem.rename(columns={"Monto": "Gasto Semanal"}, inplace=True)
        fig_sem = px.line(df_sem, x="Fecha", y="Gasto Semanal", markers=True, title="Gasto Semanal")
        st.plotly_chart(fig_sem, use_container_width=True)
        st.dataframe(df_sem, use_container_width=True)
    else:
        st.info("No hay gastos registrados.")

    st.subheader("Comparar Gasto Actual con Presupuesto por Categoría")
    if not df_gastos.empty:
        df_cat = df_gastos.groupby("Categoría")["Monto"].sum().reset_index()
        df_cat.rename(columns={"Monto": "Gasto Actual"}, inplace=True)
        df_comp = pd.merge(df_presupuesto, df_cat, on="Categoría", how="left").fillna({"Gasto Actual": 0})
        df_comp["Diferencia"] = df_comp["Presupuesto Asignado"] - df_comp["Gasto Actual"]
        st.dataframe(df_comp, use_container_width=True)

        fig_comp = px.bar(
            df_comp, 
            x="Categoría", 
            y=["Presupuesto Asignado", "Gasto Actual"], 
            barmode="group",
            title="Presupuesto vs. Gasto por Categoría"
        )
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("No se puede comparar porque no hay datos de gastos.")

    st.subheader("Pivot: Gasto por Categoría y Tipo")
    if not df_gastos.empty:
        pivot = pd.pivot_table(df_gastos, values="Monto", index="Categoría", columns="Tipo", aggfunc="sum", fill_value=0)
        st.dataframe(pivot, use_container_width=True)
        pivot_long = pivot.reset_index().melt(id_vars="Categoría", var_name="Tipo", value_name="Monto")
        fig_pivot = px.bar(pivot_long, x="Categoría", y="Monto", color="Tipo", barmode="stack")
        st.plotly_chart(fig_pivot, use_container_width=True)

    st.subheader("Forecast Semanal (Naive)")
    weeks = st.slider("Semanas a pronosticar", 1, 12, 4)
    df_forecast = forecast_semanal_naive(df_gastos, n_weeks=weeks)
    if not df_forecast.empty:
        st.dataframe(df_forecast, use_container_width=True)
        df_sem_hist = df_gastos.groupby(pd.Grouper(key="Fecha", freq="W"))["Monto"].sum().reset_index()
        df_sem_hist.rename(columns={"Monto": "Gasto Semanal"}, inplace=True)
        df_sem_hist["Tipo"] = "Histórico"
        df_forecast_ren = df_forecast.rename(columns={"Semana": "Fecha", "Gasto Proyectado": "Gasto Semanal"})
        df_forecast_ren["Tipo"] = "Forecast"
        df_join = pd.concat([df_sem_hist, df_forecast_ren], ignore_index=True)
        fig_for = px.line(df_join, x="Fecha", y="Gasto Semanal", color="Tipo", markers=True,
                          title="Histórico vs. Pronóstico Semanal")
        st.plotly_chart(fig_for, use_container_width=True)

    st.subheader("Descargar Datos")
    colA, colB, colC = st.columns(3)
    colA.download_button("Descargar Gastos", df_gastos.to_csv(index=False), "gastos.csv", "text/csv")
    colB.download_button("Descargar Presupuesto", df_presupuesto.to_csv(index=False), "presupuesto.csv", "text/csv")
    colC.download_button("Descargar Ingresos", df_ingresos.to_csv(index=False), "ingresos.csv", "text/csv")

if __name__ == "__main__":
    main()
