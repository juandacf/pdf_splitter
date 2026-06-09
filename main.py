import os
import argparse
import pandas as pd
from pypdf import PdfReader, PdfWriter

def parse_range(page_str):
    """
    Parsea el string de la página o rango.
    Ejemplos:
    - "1-27" -> retorna (0, 27) -> páginas de la 1 a la 27 (0-indexed, inclusive)
    - "71"   -> retorna (70, 71) -> solo la página 71 (índice 70)
    """
    page_str = str(page_str).strip()
    if '-' in page_str:
        start, end = page_str.split('-')
        # En pypdf, los índices empiezan en 0. 
        # Al pasar (start - 1, end), el ciclo range(start_idx, end_idx) tomará desde start-1 hasta end-1.
        return int(start) - 1, int(end)
    else:
        val = int(page_str)
        return val - 1, val

def split_pdf(pdf_path, excel_path, output_dir=None):
    if not os.path.exists(pdf_path):
        print(f"Error: El archivo PDF '{pdf_path}' no existe.")
        return
    if not os.path.exists(excel_path):
        print(f"Error: El archivo de datos '{excel_path}' no existe.")
        return

    if output_dir is None:
        output_dir = os.getcwd()
    else:
        os.makedirs(output_dir, exist_ok=True)

    # DETECCIÓN AUTOMÁTICA DE FORMATO (CSV o Excel)
    try:
        if excel_path.lower().endswith('.csv'):
            # Si el CSV usa punto y coma (;), puedes cambiar sep=',' por sep=';'
            df = pd.read_csv(excel_path, sep=None, engine='python')
        else:
            df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error al leer el archivo de datos: {e}")
        return

    # Normalizar nombres de columnas
    df.columns = [str(col).strip().upper() for col in df.columns]

    if 'CONSECUTIVO' not in df.columns or 'PAGINA' not in df.columns:
        print("Error: El archivo debe contener las columnas 'CONSECUTIVO' y 'PAGINA'.")
        print(f"Columnas encontradas: {list(df.columns)}")
        return

    # Leer el PDF original
    print(f"Abriendo el archivo PDF: {pdf_path}...")
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        print(f"Total de páginas detectadas: {total_pages}")
    except Exception as e:
        print(f"Error al leer el archivo PDF: {e}")
        return

    # Procesar filas
    for index, row in df.iterrows():
        consecutivo = str(row['CONSECUTIVO']).strip()
        pagina_raw = str(row['PAGINA']).strip()

        if pd.isna(row['CONSECUTIVO']) or pd.isna(row['PAGINA']) or consecutivo == 'nan' or pagina_raw == 'nan':
            continue

        try:
            start_idx, end_idx = parse_range(pagina_raw)
            
            if start_idx < 0 or end_idx > total_pages or start_idx >= end_idx:
                print(f"⚠️ Advertencia [Fila {index+2}]: Rango inválido '{pagina_raw}' para {consecutivo}. Se omitirá.")
                continue

            writer = PdfWriter()
            for page_num in range(start_idx, end_idx):
                writer.add_page(reader.pages[page_num])

            output_filename = f"{consecutivo}.pdf"
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, "wb") as f_out:
                writer.write(f_out)
            
            print(f"✅ Creado: {output_filename} (Páginas {pagina_raw})")

        except ValueError:
            print(f"⚠️ Advertencia [Fila {index+2}]: Formato de página no reconocible '{pagina_raw}' en {consecutivo}.")
        except Exception as e:
            print(f"❌ Error en fila {index+2} ({consecutivo}): {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para separar un PDF por rangos usando un archivo Excel.")
    parser.add_argument("-p", "--pdf", required=True, help="Ruta del archivo PDF original.")
    parser.add_argument("-e", "--excel", required=True, help="Ruta del archivo Excel (.xlsx).")
    parser.add_argument("-o", "--output", help="Carpeta de salida para los PDFs (opcional).", default=None)

    args = parser.parse_args()

    split_pdf(pdf_path=args.pdf, excel_path=args.excel, output_dir=args.output)