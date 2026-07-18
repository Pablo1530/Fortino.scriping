# -*- coding: utf-8 -*-
import csv
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# ======================================
# CONFIGURACIÓN ONLINE
# ======================================
URL = "https://www.fortunatofortino.com/usados/"
# ======================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

fecha = datetime.now()
fecha_archivo = fecha.strftime("%d_%m_%Y")
fecha_hora = fecha.strftime("%d/%m/%Y %H:%M")

# Guardamos directamente en la raíz para facilitar la visualización online
archivo_html = Path("index.html") 

def limpiar_precio(texto):
    if not texto:
        return 0
    texto = texto.replace("$", "").replace(".", "").replace(",", "").strip()
    try:
        return int(texto)
    except ValueError:
        return 0

def obtener_pagina():
    r = requests.get(URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text

def extraer_datos(html):
    soup = BeautifulSoup(html, "html.parser")
    tarjetas = soup.select(".listing-car-item-meta")
    resultado = []

    for tarjeta in tarjetas:
        try:
            enlace = tarjeta.find_parent("a", href=True)
            if not enlace: continue
            url = enlace["href"]

            titulo_tag = tarjeta.select_one(".car-title")
            if not titulo_tag: continue

            titulo = titulo_tag.get_text(" ", strip=True).upper()
            partes = titulo.split()
            if not partes: continue

            marca = partes[0]
            modelo = " ".join(partes[1:])

            precio_tag = tarjeta.select_one(".sale-price")  
            if not precio_tag:
                precio_tag = tarjeta.select_one(".regular-price")
            if not precio_tag:
                precio_tag = tarjeta.select_one(".normal-price")
            
            precio = limpiar_precio(precio_tag.get_text(strip=True)) if precio_tag else 0

            spans = tarjeta.select(".car-meta-bottom span")
            anio = ""
            km = ""

            if len(spans) >= 1: anio = spans[0].get_text(strip=True)
            if len(spans) >= 2: km = spans[1].get_text(strip=True)

            resultado.append({
                "marca": marca,
                "modelo": modelo,
                "anio": anio,
                "km": km,
                "precio": precio,
                "link": url,
            })
        except Exception as e:
            print(f"Error procesando tarjeta: {e}")

    resultado.sort(key=lambda x: (x["marca"], x["modelo"]))
    return resultado

def generar_html(datos):
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buscador de Usados</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; color: #333; background-color: #f9f9f9; }}
    h1 {{ color: #111; font-size: 24px; margin-bottom: 5px; }}
    .meta-info {{ color: #666; font-size: 13px; margin-bottom: 20px; }}
    .filter-panel {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 15px; }}
    .filter-group {{ display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 140px; }}
    .filter-group label {{ font-size: 11px; font-weight: bold; color: #555; text-transform: uppercase; }}
    .filter-group input, .filter-group select {{ padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }}
    .table-container {{ overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
    table {{ border-collapse: collapse; width: 100%; }}
    th {{ background: #0078d7; color: white; text-align: left; padding: 12px; font-size: 14px; }}
    td {{ border-bottom: 1px solid #eee; padding: 12px; font-size: 14px; }}
    tr:nth-child(even) {{ background: #fcfcfc; }}
    tr:hover {{ background: #f5f9ff; }}
    a {{ color: #0078d7; text-decoration: none; font-weight: bold; }}
    .no-results {{ display: none; padding: 20px; text-align: center; color: #888; font-style: italic; background: white; border-radius: 8px; }}
</style>
</head>
<body>

<h1>Stock de Usados</h1>
<div class="meta-info">
    Actualizado: <b>{fecha_hora} ART</b> | Total: <b id="total-original">{len(datos)}</b> | Filtrados: <b id="total-filtrado">{len(datos)}</b>
</div>

<div class="filter-panel">
    <div class="filter-group">
        <label>Buscar</label>
        <input type="text" id="searchBox" placeholder="Marca o modelo..." oninput="filtrarTabla()">
    </div>
    <div class="filter-group">
        <label>Año Mín</label>
        <input type="number" id="anioMin" placeholder="2015" oninput="filtrarTabla()">
    </div>
    <div class="filter-group">
        <label>Km Máx</label>
        <input type="number" id="kmMax" placeholder="100000" oninput="filtrarTabla()">
    </div>
    <div class="filter-group">
        <label>Precio</label>
        <select id="ordenPrecio" onchange="filtrarTabla()">
            <option value="default">Por defecto</option>
            <option value="asc">Menor precio</option>
            <option value="desc">Mayor precio</option>
        </select>
    </div>
</div>

<div class="table-container">
    <table id="tablaAutos">
        <thead>
            <tr>
                <th>Marca</th>
                <th>Modelo</th>
                <th>Año</th>
                <th>Km</th>
                <th>Precio</th>
            </tr>
        </thead>
        <tbody id="cuerpoTabla">
"""

    for d in datos:
        try:
            km_numerico = d['km'].replace('.', '').replace(' ', '').replace('KM', '').strip()
            km_numerico = int(km_numerico) if km_numerico.isdigit() else 0
        except:
            km_numerico = 0
            
        link_html = f'<a href="{d["link"]}" target="_blank">{d["modelo"]}</a>'
        
        html += f"""
        <tr class="auto-row" data-marca="{d['marca']}" data-modelo="{d['modelo']}" data-anio="{d['anio']}" data-km="{km_numerico}" data-precio="{d['precio']}">
            <td>{d['marca']}</td>
            <td>{link_html}</td>
            <td>{d['anio']}</td>
            <td>{d['km']}</td>
            <td>${d['precio']:,}</td>
        </tr>"""

    html += """
        </tbody>
    </table>
</div>

<div id="noResults" class="no-results">No se encontraron vehículos.</div>

<script>
function filtrarTabla() {
    const buscar = document.getElementById('searchBox').value.toUpperCase();
    const anioMin = parseInt(document.getElementById('anioMin').value) || 0;
    const kmMax = parseInt(document.getElementById('kmMax').value) || Infinity;
    const orden = document.getElementById('ordenPrecio').value;
    
    const tbody = document.getElementById('cuerpoTabla');
    const filas = Array.from(document.getElementsByClassName('auto-row'));
    let visibles = 0;

    filas.forEach(fila => {
        const marca = fila.getAttribute('data-marca').toUpperCase();
        const modelo = fila.getAttribute('data-modelo').toUpperCase();
        const anio = parseInt(fila.getAttribute('data-anio')) || 0;
        const km = parseInt(fila.getAttribute('data-km')) || 0;
        
        const coincideTexto = marca.includes(buscar) || modelo.includes(buscar);
        const coincideAnio = anio >= anioMin;
        const coincideKm = km <= kmMax;

        if (coincideTexto && coincideAnio && coincideKm) {
            fila.style.display = "";
            visibles++;
        } else {
            fila.style.display = "none";
        }
    });

    if (orden === 'asc' || orden === 'desc') {
        filas.sort((a, b) => {
            const precioA = parseInt(a.getAttribute('data-precio')) || 0;
            const precioB = parseInt(b.getAttribute('data-precio')) || 0;
            return orden === 'asc' ? precioA - precioB : precioB - precioA;
        });
        filas.forEach(fila => tbody.appendChild(fila));
    }

    document.getElementById('total-filtrado').innerText = visibles;
    document.getElementById('noResults').style.display = visibles === 0 ? "block" : "none";
}
</script>
</body>
</html>
"""
    with open(archivo_html, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    try:
        pagina = obtener_pagina()
        datos = extraer_datos(pagina)
        if datos:
            generar_html(datos)
            print("HTML actualizado correctamente.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
