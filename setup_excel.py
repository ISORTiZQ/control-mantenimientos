"""
Detecta y copia el archivo Excel existente a data/datos.xlsx.
Si hay un archivo .xlsx en la raíz del proyecto, lo usa.
"""

import os
import shutil
import glob


def setup_excel():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")
    target = os.path.join(data_dir, "datos.xlsx")

    os.makedirs(data_dir, exist_ok=True)

    # Si ya existe data/datos.xlsx, no hacer nada
    if os.path.exists(target):
        print(f"✅ Excel ya existe en: {target}")
        return target

    # Buscar archivos .xlsx en la raíz
    xlsx_files = glob.glob(os.path.join(base_dir, "*.xlsx"))
    # Excluir archivos temporales
    xlsx_files = [f for f in xlsx_files if not f.startswith("~$")]

    if xlsx_files:
        source = xlsx_files[0]
        shutil.copy2(source, target)
        print(f"✅ Excel copiado de: {source}")
        print(f"   a: {target}")
        return target

    print("⚠️  No se encontró ningún archivo .xlsx.")
    print("   Ejecuta: python generate_sample_excel.py")
    return None


if __name__ == "__main__":
    setup_excel()
