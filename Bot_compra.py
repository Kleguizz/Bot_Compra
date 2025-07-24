import os           # Manejo de archivos y carpetas
import re           # Expresiones regulares para buscar texto dentro del PDF
import json         # Para guardar los datos extraídos en formato JSON
import pdfplumber   # Librería para extraer texto desde archivos PDF

# Función que recibe el nombre de un archivo PDF y devuelve los datos extraídos
def extraer_datos_pdf(nombre_archivo):
    # Abre el archivo PDF y concatena el texto de todas sus páginas
    with pdfplumber.open(nombre_archivo) as pdf:
        texto = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # Buscar el nombre del proveedor
    proveedor = re.search(r"^(AGRONORTE S\.R\.L\.)", texto, re.MULTILINE)
    proveedor = proveedor.group(1).strip() if proveedor else ""

    # Buscar el número de comprobante, separado en punto de venta y número
    comprobante_match = re.search(r"Nro\.:?\s*(\d{4})-(\d+)", texto)
    pto_venta = comprobante_match.group(1) if comprobante_match else ""
    nro_comp = comprobante_match.group(2) if comprobante_match else ""

    # Buscar la fecha del comprobante
    fecha_match = re.search(r"Fecha:\s*(\d{2}/\d{2}/\d{4})", texto)
    fecha = fecha_match.group(1) if fecha_match else "01/01/2000"
    dia, mes, anio = fecha.split("/")

    # Buscar el tipo de cambio si existe
    tipo_cambio_match = re.search(r"Tipo de cambio:\s*(\d+[.,]?\d*)", texto)
    tipo_cambio = float(tipo_cambio_match.group(1).replace(",", ".")) if tipo_cambio_match else 1.0

    # Buscar el valor del IVA en dólares y convertirlo a pesos
    iva_match = re.search(r"IVA\s+21\.00%\s+U\$S\s*([\d.,]+)", texto)
    iva_pesos = round(float(iva_match.group(1).replace(",", ".")) * tipo_cambio, 2) if iva_match else 0.0

    # Buscar percepciones en dólares y convertirlas a pesos
    percep_match = re.search(r"Percepciones\s+U\$S\s*([\d.,]+)", texto)
    percep_pesos = round(float(percep_match.group(1).replace(",", ".")) * tipo_cambio, 2) if percep_match else 0.0

    # Lista donde se almacenarán los productos extraídos
    productos = []

    # Patrón para extraer cada producto del texto del PDF
    patron = re.compile(
        r"^([A-Z0-9]{4,})\s+.+?\s+(\d+(?:[.,]\d+)?)\s+U\$S\s+[\d.,]+\s+U\$S\s+-?[\d.,]+\s+U\$S\s+([\d.,]+)",
        re.MULTILINE
    )

    # Iterar sobre todos los productos encontrados y agregarlos a la lista
    for match in patron.finditer(texto):
        codigo, cantidad, importe_usd = match.groups()
        importe_pesos = round(float(importe_usd.replace(",", ".")) * tipo_cambio, 2)
        productos.append({
            "codigo": codigo,
            "cantidad": float(cantidad.replace(",", ".")),
            "importe_pesos": importe_pesos
        })

    # Devolver toda la información en un diccionario
    return {
        "archivo_pdf": nombre_archivo,
        "proveedor": proveedor,
        "comprobante": {
            "pto_venta": pto_venta,
            "nro_comprobante": nro_comp
        },
        "fecha": {
            "dia": int(dia),
            "mes": int(mes),
            "anio": int(anio)
        },
        "tipo_cambio": tipo_cambio,
        "iva": iva_pesos,
        "percepciones": percep_pesos,
        "productos": productos
    }

# === BLOQUE PRINCIPAL ===

# Buscar todos los archivos PDF en la carpeta actual
archivos_pdf = [f for f in os.listdir() if f.lower().endswith(".pdf")]

# Si no hay PDFs, mostrar mensaje y salir
if not archivos_pdf:
    print("❌ No se encontraron archivos PDF.")
    exit()

# Obtener el PDF más reciente (último modificado)
archivo_pdf = max(archivos_pdf, key=os.path.getctime)

# Extraer los datos del PDF
datos = extraer_datos_pdf(archivo_pdf)

# Generar el nombre del archivo JSON de salida
archivo_json = os.path.splitext(archivo_pdf)[0] + ".json"

# Guardar los datos extraídos en formato JSON
with open(archivo_json, "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)

# Mostrar mensaje final
print(f"✅ Datos exportados a: {archivo_json}")
