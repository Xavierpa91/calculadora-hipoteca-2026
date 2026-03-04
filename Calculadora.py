import math
import openpyxl
from openpyxl.utils import get_column_letter

def calcular_cuota(capital, TIN, plazo_hipoteca):
    r = TIN / 100 / 12
    n = plazo_hipoteca * 12
    cuota = (capital * r * math.pow(1 + r, n)) / (math.pow(1 + r, n) - 1)
    total_pagado = cuota * n
    intereses_totales = total_pagado - capital
    return cuota, total_pagado, intereses_totales

def crear_excel_y_mostrar(coste_vivienda, ahorros, TIN, plazo_hipoteca, inicio_hipoteca):
    impuesto_compra = coste_vivienda * 0.075  # 7.5% ITP
    gastos_gestion = 1960 + 560 + 400 # Escritura + Registro de la Propiedad + Tasación del Inmueble

    capital = coste_vivienda - ahorros + impuesto_compra + gastos_gestion
    
    entrada = ahorros - impuesto_compra - gastos_gestion

    cuota, total_pagado, intereses_totales = calcular_cuota(capital, TIN, plazo_hipoteca)
    fin_hipoteca = inicio_hipoteca + plazo_hipoteca

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumen Hipoteca"

    # Cabecera con datos generales
    ws["A1"] = "Parámetro"
    ws["B1"] = "Valor"
    datos_cabecera = {
        "Coste vivienda (€)": coste_vivienda,
        "Ahorros aportados (€)": ahorros,
        "Impuestos compra (€)": round(impuesto_compra, 2),
        "Gastos gestión (€)": gastos_gestion,
        "Cantidad hipotecada (€)": round(capital, 2),
        "TIN (%)": TIN,
        "Plazo hipoteca (años)": plazo_hipoteca,
        "Cuota fija mensual (€)": round(cuota, 2),
        "Intereses totales (€)": round(intereses_totales, 2),
        "Total pagado (€)": round(total_pagado, 2),
        "Fin de hipoteca (año)": fin_hipoteca,
    }
    fila = 2
    for clave, valor in datos_cabecera.items():
        ws[f"A{fila}"] = clave
        ws[f"B{fila}"] = valor
        fila += 1

    # Hoja con cuotas para varios plazos
    ws2 = wb.create_sheet("Cuotas según plazo")
    ws2.append(["Plazo (años)", "Cuota mensual (€)", "Total pagado (€)", "Intereses totales (€)", "Coste total vivienda (€)", "Fin hipoteca (año)"])

    for plazo in range(5, 36, 5):
        c, total, intereses = calcular_cuota(capital, TIN, plazo)
        fin = inicio_hipoteca + plazo
        coste_total = coste_vivienda + intereses + gastos_gestion + impuesto_compra
        ws2.append([plazo, round(c, 2), round(total, 2), round(intereses, 2), round(coste_total, 2), fin])

    # Ajustar ancho columnas
    for ws_ in [ws, ws2]:
        for col in ws_.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws_.column_dimensions[col_letter].width = max_len + 2

    archivo = "hipoteca_resumen.xlsx"
    wb.save(archivo)
    print(f"Archivo Excel generado: {archivo}")

    # Solo imprimir resumen del plazo elegido (no la tabla completa)
    print("\n📊 Resumen de la hipoteca para el plazo seleccionado:")
    print(f"📉 TIN anual: {TIN}%")
    print(f"💶 Cuota mensual: {round(cuota, 2)} €")
    print(f"🏠 Coste vivienda: {coste_vivienda} €")
    print(f"💸 Entrada: {entrada} €")
    print(f"💰 Ahorros aportados: {ahorros} €")
    print(f"🏦 Cantidad hipotecada: {round(capital, 2)} €")
    print(f"🏠 Coste total vivienda (incl. impuestos y gestión): {round(coste_vivienda + intereses_totales + gastos_gestion + impuesto_compra, 2)} €")
    print(f"💸 Intereses totales: {round(intereses_totales, 2)} €")
    print(f"📈 Total pagado: {round(total_pagado, 2)} €")
    print(f"⏳ Plazo de la hipoteca: {plazo_hipoteca} años")
    print(f"📅 Fin de hipoteca: {fin_hipoteca}")

if __name__ == "__main__":
    print("🏠 Calculadora de Hipoteca 🏠")
    print("--------------------------------------")
    
    coste_vivienda = float(input("¿Cuánto vale tu futura vivienda? (en euros): "))
    ahorros = float(input("¿De cuántos ahorros dispones? (en euros): "))
    TIN = float(input("Introduce el TIN anual (en porcentaje): "))
    plazo_hipoteca = int(input("Introduce el plazo del préstamo (en años): "))
    inicio_hipoteca = int(input("¿Cuándo vas a firmar la hipoteca? (año de la firma): "))

    crear_excel_y_mostrar(coste_vivienda, ahorros, TIN, plazo_hipoteca, inicio_hipoteca)
