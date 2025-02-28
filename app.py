import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3

# -----------------------------------------------------
# 1. Funciones de Conexión y Manejo de la Base de Datos
# -----------------------------------------------------
def conectar_db():
    """Conecta o crea el archivo 'database.db'."""
    conn = sqlite3.connect("database.db")
    return conn

def crear_tablas():
    """Crea las tablas si no existen."""
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        categoria TEXT,
        monto REAL,
        tipo TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presupuesto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT,
        presupuesto_asignado REAL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingresos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fuente TEXT,
        monto REAL
    );
    """)

    conn.commit()
    conn.close()

def leer_tabla_df(tabla):
    """Lee todos los datos de una tabla y los devuelve en un DataFrame."""
    conn = conectar_db()
    df = pd.read_sql(f"SELECT * FROM {tabla}", conn)
    conn.close()
    return df

def guardar_tabla_df(df, tabla):
    """
    Reemplaza por completo el contenido de una tabla 
    con los datos de un DataFrame (columnas deben coincidir).
    """
    conn = conectar_db()
    df.to_sql(tabla, conn, if_exists="replace", index=False)
    conn.close()

# ------------------------------------------------------
# 2. Generadores de datos iniciales (si la tabla está vacía)
# ------------------------------------------------------
def generar_datos_gastos_inicial(n_rows=20):
    fechas = pd.date_range(start="2025-03-01", end="2025-04-30", freq="D")
    categorias = [
        "Impuestos", "Renta", "Transporte", "Carro", "Gasolina",
        "Comida Trabajo", "Comida Casa", "Medicinas", "Suplementos",
        "Gimnasio", "Aseo", "Internet", "Celular", "Suscripciones",
        "Pago mensual señora", "Novia", "Ahorro", "Deudas/Pagos Recurrentes"
    ]
    tipos = ["tarjeta", "otro"]
    np.random.seed(42)
    df = pd.DataFrame({
        "fecha": np.random.choice(fechas, size=n_rows),
        "categoria": np.random.choice(categorias, size=n_rows),
        "monto": np.random.randint(50, 500, size=n_rows),
        "tipo": np.random.choice(tipos, size=n_rows),
    })
    return df

def generar_presupuesto_inicial():
    data = {
        "categoria": [
            "Impuestos", "Renta", "Transporte", "Carro", "Gasolina",
            "Comida Trabajo", "Comida Casa", "Medicinas", "Suplementos",
            "Gimnasio", "Aseo", "Internet", "Celular", "Suscripciones",
            "Pago mensual señora", "Novia", "Ahorro", "Deudas/Pagos Recurrentes"
        ],
        "presupuesto_asignado": [
            700, 2000, 150, 1000, 1000,
            900, 1500, 1500, 500,
            250, 500, 100, 200, 250,
            1500, 1000, 2000, 800
        ]
    }
    return pd.DataFrame(data)

def generar_ingresos_inicial():
    data = {
        "fuente": ["Salario", "Flexible"],
        "monto": [14000, 1000]
    }
    return pd.DataFrame(data)

# ------------------------------------------------------
# 3. Forecast Semanal (Naive)
# ------------------------------------------------------
def forecast_semanal_naive(df, n_weeks=4):
    """
    Calcula el gasto semanal promedio y proyecta n_weeks semanas.
    Retorna DataFrame con columnas ['Semana', 'Gasto Proyectado'].
    """
    if df.empty:
        return pd.DataFrame(columns=["Semana", "Gasto Proyectado"])

    # Asegurar que la columna 'fecha' sea datetime
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    # Agrupamos por semana
    df_sem = df.groupby(pd.Grouper(key="fecha", freq="W"))["monto"].sum().reset_index()
    df_sem.rename(columns={"monto": "Gasto Semanal"}, inplace=True)
    gasto_promedio = df_sem["Gasto Semanal"].mean()
    ultima_semana = df_sem["fecha"].max()
    if pd.isnull(ultima_semana):
        ultima_semana = datetime.today()

    # Generar semanas futuras
    semanas_futuras = [ultima_semana + timedelta(weeks=i+1) for i in range(n_weeks)]
    return pd.DataFrame({
        "Semana": semanas_futuras,
        "Gasto Proyectado": [gasto_promedio] * n_weeks
    })

# ------------------------------------------------------
# 4. Aplicación Streamlit
# ------------------------------------------------------
def main():
    st.set_page_config(page_title="Gastos + Presupuesto (SQLite)", layout="wide")
    st.title("Control de Gastos y Presupuesto (SQLite)")

    # Crear tablas si no existen
    crear_tablas()

    # Leer datos de la base
    df_gastos = leer_tabla_df("gastos")
    df_presupuesto = leer_tabla_df("presupuesto")
    df_ingresos = leer_tabla_df("ingresos")

    # Si alguna tabla está vacía, generar datos iniciales y guardarlos
    if df_gastos.empty:
        df_gastos = generar_datos_gastos_inicial()
        guardar_tabla_df(df_gastos, "gastos")

    if df_presupuesto.empty:
        df_presupuesto = generar_presupuesto_inicial()
        guardar_tabla_df(df_presupuesto, "presupuesto")

    if df_ingresos.empty:
        df_ingresos = generar_ingresos_inicial()
        guardar_tabla_df(df_ingresos, "ingresos")

    # Mostramos DataFrames en editor para que el usuario pueda editar
    col1, col2, col3 = st.columns([1.2, 1, 1])

    with col1:
        st.subheader("Gastos")
        edit_gastos = st.data_editor(df_gastos, num_rows="dynamic")
        if st.button("Guardar Gastos"):
            guardar_tabla_df(edit_gastos, "gastos")
            st.success("Gastos guardados en la base de datos.")

    with col2:
        st.subheader("Presupuesto")
        edit_presupuesto = st.data_editor(df_presupuesto)
        if st.button("Guardar Presupuesto"):
            guardar_tabla_df(edit_presupuesto, "presupuesto")
            st.success("Presupuesto guardado en la base de datos.")

    with col3:
        st.subheader("Ingresos")
        edit_ingresos = st.data_editor(df_ingresos)
        if st.button("Guardar Ingresos"):
            guardar_tabla_df(edit_ingresos, "ingresos")
            st.success("Ingresos guardados en la base de datos.")

    # Para mostrar gráficas, usamos los últimos dataframes editados
    df_gastos_final = edit_gastos.copy()
    df_presupuesto_final = edit_presupuesto.copy()
    df_ingresos_final = edit_ingresos.copy()

    # KPIs
    total_gastos = df_gastos_final["monto"].sum() if not df_gastos_final.empty else 0
    total_presupuesto = df_presupuesto_final["presupuesto_asignado"].sum() if not df_presupuesto_final.empty else 0
    total_ingresos = df_ingresos_final["monto"].sum() if not df_ingresos_final.empty else 0
    saldo = total_ingresos - total_gastos

    st.subheader("Indicadores Clave")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos Totales", f"{total_ingresos:,.0f}")
    c2.metric("Gastos Totales", f"{total_gastos:,.0f}")
    c3.metric("Saldo (Ing - Gastos)", f"{saldo:,.0f}")
    c4.metric("Presupuesto Mensual (Gastos)", f"{total_presupuesto:,.0f}")

    # Tendencia Semanal de Gastos
    st.subheader("Tendencia Semanal de Gastos")
    if not df_gastos_final.empty:
        df_gastos_final["fecha"] = pd.to_datetime(df_gastos_final["fecha"], errors="coerce")
        df_sem = df_gastos_final.groupby(pd.Grouper(key="fecha", freq="W"))["monto"].sum().reset_index()
        df_sem.rename(columns={"monto": "Gasto Semanal"}, inplace=True)
        fig_sem = px.line(df_sem, x="fecha", y="Gasto Semanal", markers=True, title="Gasto Semanal")
        st.plotly_chart(fig_sem, use_container_width=True)
    else:
        st.info("No hay datos de gastos para graficar.")

    # Comparar Gasto Actual con Presupuesto por Categoría
    st.subheader("Comparar Gasto Actual vs Presupuesto por Categoría")
    if not df_gastos_final.empty:
        df_cat = df_gastos_final.groupby("categoria")["monto"].sum().reset_index()
        df_cat.rename(columns={"monto": "Gasto Actual"}, inplace=True)
        df_comp = pd.merge(df_presupuesto_final, df_cat, on="categoria", how="left").fillna({"Gasto Actual": 0})
        df_comp["Diferencia"] = df_comp["presupuesto_asignado"] - df_comp["Gasto Actual"]
        st.dataframe(df_comp, use_container_width=True)
        fig_comp = px.bar(df_comp, x="categoria", y=["presupuesto_asignado", "Gasto Actual"],
                          barmode="group", title="Presupuesto vs. Gasto por Categoría")
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("No hay gastos para comparar con el presupuesto.")

    # Pivot: Gasto por Categoría y Tipo
    st.subheader("Pivot: Gasto por Categoría y Tipo")
    if not df_gastos_final.empty:
        pivot = pd.pivot_table(
            df_gastos_final,
            values="monto",
            index="categoria",
            columns="tipo",
            aggfunc="sum",
            fill_value=0
        )
        st.dataframe(pivot, use_container_width=True)
        pivot_long = pivot.reset_index().melt(id_vars="categoria", var_name="Tipo", value_name="Monto")
        fig_pivot = px.bar(pivot_long, x="categoria", y="Monto", color="Tipo", barmode="stack")
        st.plotly_chart(fig_pivot, use_container_width=True)

    # Forecast Semanal
    st.subheader("Forecast Semanal (Naive)")
    weeks = st.slider("Semanas a pronosticar", 1, 12, 4)
    df_forecast = forecast_semanal_naive(df_gastos_final, n_weeks=weeks)
    if not df_forecast.empty:
        st.dataframe(df_forecast, use_container_width=True)
        # Unir histórico vs forecast
        df_sem_hist = df_gastos_final.groupby(pd.Grouper(key="fecha", freq="W"))["monto"].sum().reset_index()
        df_sem_hist.rename(columns={"monto": "Gasto Semanal"}, inplace=True)
        df_sem_hist["Tipo"] = "Histórico"
        df_forecast_ren = df_forecast.rename(columns={"Semana": "fecha", "Gasto Proyectado": "Gasto Semanal"})
        df_forecast_ren["Tipo"] = "Forecast"
        df_join = pd.concat([df_sem_hist, df_forecast_ren], ignore_index=True)
        fig_for = px.line(df_join, x="fecha", y="Gasto Semanal", color="Tipo", markers=True,
                          title="Histórico vs. Pronóstico Semanal")
        st.plotly_chart(fig_for, use_container_width=True)
    else:
        st.info("No se pudo generar el forecast (no hay datos).")

    st.caption("App minimalista con persistencia en SQLite. Almacena datos en 'database.db'.")

if __name__ == "__main__":
    main()
