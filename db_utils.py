from sqlalchemy import create_engine

def guardar_en_base_de_datos(df, db_path="sqlite:///facturas.db"):
    """Guarda un DataFrame en la base de datos SQLite."""
    engine = create_engine(db_path)
    try:
        df.to_sql("facturas", engine, if_exists="append", index=False)
        print("✅ Datos guardados en la base de datos.")
    except Exception as e:
        print(f"❌ Error al guardar los datos en la base de datos: {e}")
    finally:
        engine.dispose()