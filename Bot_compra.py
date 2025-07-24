import os
import re
import json
import pdfplumber

def extraer_datos_pdf(nombre_archivo):
    with pdfplumber.open(nombre_archivo) as pdf:
        texto = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    proveedor = re.search(r"^(AGRONORTE S\.R\.L\.)", texto, re.MULTILINE)
    proveedor = proveedor.group(1).strip() if proveedor else ""

    comprobante_match = re.search(r"Nro\.:?\s*(\d{4})-(\d+)", texto)
    pto_venta = comprobante_match.group(1) if comprobante_match else ""
    nro_comp = comprobante_match.group(2) if comprobante_match else ""

    fecha_match = re.search(r"Fecha:\s*(\d{2}/\d{2}/\d{4})", texto)
    fecha = fecha_match.group(1) if fecha_match else "01/01/2000"
    dia, mes, anio = fecha.split("/")

    tipo_cambio_match = re.search(r"Tipo de cambio:\s*(\d+[.,]?\d*)", texto)
    tipo_cambio = float(tipo_cambio_match.group(1).replace(",", ".")) if tipo_cambio_match else 1.0

    iva_match = re.search(r"IVA\s+21\.00%\s+U\$S\s*([\d.,]+)", texto)
    iva_pesos = round(float(iva_match.group(1).replace(",", ".")) * tipo_cambio, 2) if iva_match else 0.0

    percep_match = re.search(r"Percepciones\s+U\$S\s*([\d.,]+)", texto)
    percep_pesos = round(float(percep_match.group(1).replace(",", ".")) * tipo_cambio, 2) if percep_match else 0.0

    productos = []
    patron = re.compile(
        r"^([A-Z0-9]{4,})\s+.+?\s+(\d+(?:[.,]\d+)?)\s+U\$S\s+[\d.,]+\s+U\$S\s+-?[\d.,]+\s+U\$S\s+([\d.,]+)",
        re.MULTILINE
    )
    for match in patron.finditer(texto):
        codigo, cantidad, importe_usd = match.groups()
        importe_pesos = round(float(importe_usd.replace(",", ".")) * tipo_cambio, 2)
        productos.append({
            "codigo": codigo,
            "cantidad": float(cantidad.replace(",", ".")),
            "importe_pesos": importe_pesos
        })

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

# === Ejecutar ===
archivos_pdf = [f for f in os.listdir() if f.lower().endswith(".pdf")]
if not archivos_pdf:
    print("❌ No se encontraron archivos PDF.")
    exit()

archivo_pdf = max(archivos_pdf, key=os.path.getctime)
datos = extraer_datos_pdf(archivo_pdf)

archivo_json = os.path.splitext(archivo_pdf)[0] + ".json"
with open(archivo_json, "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)

print(f"✅ Datos exportados a: {archivo_json}")
