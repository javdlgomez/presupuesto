import streamlit as st
import pandas as pd
import sqlite3

# -------------------------------
# 1️⃣ Conectar con la base de datos
# -------------------------------
def conectar_db():
    conn = sqlite3.connect("database.db")
    return conn

# -------------------------------
# 2️⃣ Crear las tablas si no existen
# -------------------------------
def crear_tablas():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        categoria TEXT,
        monto REAL,
        tipo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingresos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fuente TEXT,
        monto REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presupuesto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT,
        monto REAL
    )
    """)

    conn.commit()
    conn.close()

# -------------------------------
# 3️⃣ Cargar datos desde SQLite
# -------------------------------
def cargar_datos(tabla):
    conn = conectar_db()
    df = pd.read_sql(f"SELECT * FROM {tabla}", conn)
    conn.close()
    return df

# -------------------------------
# 4️⃣ Guardar datos en SQLite
# -------------------------------
def guardar_datos(df, tabla):
    conn = conectar_db()
    df.to_sql(tabla, conn, if_exists="replace", index=False)
    conn.close()

# -------------------------------
# 5️⃣ Iniciar la App en Streamlit
# -------------------------------
def main():
    st.set_page_config(page_title="Gastos y Presupuesto", layout="wide")
    st.title("📊 Control de Gastos con Persistencia en SQLite")

    # Crear base de datos si no existe
    crear_tablas()

    # Cargar datos de la base de datos
    df_gastos = cargar_datos("gastos")
    df_ingresos = cargar_datos("ingresos")
    df_presupuesto = cargar_datos("presupuesto")

    # Si las tablas están vacías, inicializar con valores predeterminados
    if df_gastos.empty:
        df_gastos = pd.DataFrame({"fecha": [], "categoria": [], "monto": [], "tipo": []})
        guardar_datos(df_gastos, "gastos")

    if df_ingresos.empty:
        df_ingresos = pd.DataFrame({"fuente": ["Salario", "Flexible"], "monto": [14000, 1000]})
        guardar_datos(df_ingresos, "ingresos")

    if df_presupuesto.empty:
        df_presupuesto = pd.DataFrame({
            "categoria": ["Renta", "Transporte", "Comida Casa", "Medicinas"],
            "monto": [2000, 150, 1500, 1500]
        })
        guardar_datos(df_presupuesto, "presupuesto")

    # Editar los datos
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Gastos")
        df_gastos_edit = st.data_editor(df_gastos, num_rows="dynamic")
        if st.button("Guardar Gastos"):
            guardar_datos(df_gastos_edit, "gastos")
            st.success("Gastos guardados en SQLite")

    with col2:
        st.subheader("Ingresos")
        df_ingresos_edit = st.data_editor(df_ingresos)
        if st.button("Guardar Ingresos"):
            guardar_datos(df_ingresos_edit, "ingresos")
            st.success("Ingresos guardados en SQLite")

    with col3:
        st.subheader("Presupuesto")
        df_presupuesto_edit = st.data_editor(df_presupuesto)
        if st.button("Guardar Presupuesto"):
            guardar_datos(df_presupuesto_edit, "presupuesto")
            st.success("Presupuesto guardado en SQLite")

    # Mostrar KPIs
    total_gastos = df_gastos["monto"].sum() if not df_gastos.empty else 0
    total_ingresos = df_ingresos["monto"].sum() if not df_ingresos.empty else 0
    saldo = total_ingresos - total_gastos

    st.subheader("💡 Resumen Financiero")
    k1, k2, k3 = st.columns(3)
    k1.metric("Ingresos Totales", f"{total_ingresos:,.0f}")
    k2.metric("Gastos Totales", f"{total_gastos:,.0f}")
    k3.metric("Saldo Disponible", f"{saldo:,.0f}")

if __name__ == "__main__":
    main()
