"""
Genera un archivo Excel de ejemplo con datos de prueba.
Ejecutar: python generate_sample_excel.py
"""

import os
import pandas as pd


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    filepath = os.path.join(data_dir, "datos.xlsx")

    data = {
        "OT": [f"OT-{1000 + i}" for i in range(25)],
        "Tienda": [
            "Tienda Centro", "Tienda Norte", "Tienda Sur",
            "Tienda Este", "Tienda Oeste", "Tienda Mall",
            "Tienda Plaza", "Tienda Market",
        ] * 3 + ["Tienda Centro"],
        "Tipo de servicio": [
            "Instalación", "Mantenimiento", "Reparación",
            "Soporte Técnico", "Configuración",
        ] * 5,
        # Columnas adicionales que NO se mostrarán
        "Fecha": pd.date_range("2026-01-01", periods=25, freq="D"),
        "Técnico": [f"Técnico {i}" for i in range(1, 26)],
        "Estado": ["Completado"] * 12 + ["En Proceso"] * 8 + ["Pendiente"] * 5,
    }

    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False, engine="openpyxl")
    print(f"✅ Excel de ejemplo creado en: {filepath}")
    print(f"   Total de registros: {len(df)}")
    print(f"   Columnas: {list(df.columns)}")


if __name__ == "__main__":
    main()
