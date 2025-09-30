import pytest
import random
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://coffee-cart.app/"
CARPETA_CAPTURAS = "capturas"

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def guardar_captura(driver, nombre):
    if not os.path.exists(CARPETA_CAPTURAS):
        os.makedirs(CARPETA_CAPTURAS)
    ruta = os.path.join(CARPETA_CAPTURAS, nombre)
    driver.save_screenshot(ruta)
    return ruta

def test_cafe_completo(driver):
    driver.get(URL)
    wait = WebDriverWait(driver, 40)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Asegurar que cargue el DOM
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    # Extraer cafés disponibles
    productos = driver.execute_script("""
        let productos = [];
        document.querySelectorAll('h4').forEach(function(h4) {
            let texto = h4.innerText.trim();
            let partes = texto.split('\\n');
            let nombre = partes[0].trim();
            let precio = partes[1] ? partes[1].trim() : '';

            if (!precio) {
                let siguiente = h4.nextElementSibling;
                while (siguiente) {
                    if (/\\d/.test(siguiente.innerText)) {
                        precio = siguiente.innerText.trim();
                        break;
                    }
                    siguiente = siguiente.nextElementSibling;
                }
            }
            productos.push([nombre, precio]);
        });
        return productos.slice(0, 9);
    """)

    assert len(productos) > 0, "No se extrajo ningún café"
    cantidad = random.randint(3, len(productos))
    seleccionados = productos[:cantidad]
    errores = []
    capturas = []
    nombre_eliminado = ""

    # -----------------------
    # Agregar cafés
    # -----------------------
    for i in range(cantidad):
        try:
            selector = f"li:nth-child({i+1}) div.cup-body"
            cafe_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            cafe_element.click()
            time.sleep(0.3)
        except Exception as e:
            errores.append(f"❌ Error al agregar café #{i+1}: {e}")
    capturas.append(guardar_captura(driver, "agregado.png"))

    # Ir al carrito
    try:
        cart_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/cart"]')))
        cart_link.click()
    except Exception as e:
        errores.append(f"❌ Error al ir al carrito: {e}")

    # -----------------------
    # Validar inserciones
    # -----------------------
    try:
        assert "/cart" in driver.current_url, f"URL inesperada: {driver.current_url}"
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        html = driver.page_source
        for nombre, _ in seleccionados:
            assert nombre in html, f"No se encontró '{nombre}' en el carrito"
    except Exception as e:
        ruta_error = guardar_captura(driver, "error_validacion_carrito.png")
        capturas.append(ruta_error)
        errores.append(f"❌ Validación del carrito falló: {e}")

    # -----------------------
    # Modificar cantidades (random entre 2 y 10 usando +)
    # -----------------------
    try:
        filas = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.cart_item")))
        assert filas, "No se encontraron productos en el carrito"

        for fila in filas:
            nombre = fila.find_element(By.CSS_SELECTOR, ".product-name").text
            cantidad_deseada = random.randint(2, 10)

            input_cantidad = fila.find_element(By.CSS_SELECTOR, "input[type='number']")
            valor_actual = int(input_cantidad.get_attribute("value"))

            boton_mas = fila.find_element(By.CSS_SELECTOR, ".quantity .plus")

            while valor_actual < cantidad_deseada:
                boton_mas.click()
                time.sleep(0.3)
                valor_actual = int(input_cantidad.get_attribute("value"))

            assert valor_actual == cantidad_deseada, (
                f"❌ {nombre}: esperado {cantidad_deseada}, quedó {valor_actual}"
            )

    except Exception as e:
        ruta_error = guardar_captura(driver, "error_modificacion_carrito.png")
        capturas.append(ruta_error)
        errores.append(f"❌ Error al modificar cantidades dinámicas: {e}")

    capturas.append(guardar_captura(driver, "modificado.png"))

    # -----------------------
    # Eliminar aleatorio
    # -----------------------
    try:
        filas = driver.find_elements(By.CSS_SELECTOR, "tr.cart_item")
        assert filas, "No se encontraron filas de productos en el carrito"

        fila_eliminar = random.choice(filas)
        nombre_eliminado = fila_eliminar.find_element(By.CSS_SELECTOR, ".product-name").text
        boton_x = fila_eliminar.find_element(By.CSS_SELECTOR, ".remove")

        boton_x.click()
        WebDriverWait(driver, 10).until_not(lambda d: nombre_eliminado in d.page_source)
    except Exception as e:
        ruta_error = guardar_captura(driver, "error_eliminacion.png")
        capturas.append(ruta_error)
        errores.append(f"❌ Error al eliminar producto: {e}")

    capturas.append(guardar_captura(driver, "eliminado.png"))

    # -----------------------
    # Reporte TXT
    # -----------------------
    with open("reporte_prueba.txt", "w", encoding="utf-8") as txt:
        txt.write(f"Prueba automatizada: Agregar, modificar y eliminar cafés\n\n")
        txt.write(f"Fecha de ejecución: {fecha}\n")
        txt.write(f"URL: {URL}\n\n")
        txt.write("Cafés seleccionados:\n")
        for nombre, precio in seleccionados:
            txt.write(f"- {nombre}: {precio}\n")
        txt.write(f"\nCantidad seleccionada: {cantidad}\n")
        txt.write("\nAcciones realizadas:\n")
        txt.write("- Se agregaron los cafés al carrito\n")
        txt.write("- Se validó su presencia en el carrito\n")
        txt.write("- Se modificaron las cantidades a valores aleatorios (2–10)\n")
        txt.write(f"- Se eliminó aleatoriamente usando ❌: {nombre_eliminado}\n")
        txt.write("- Se validó que el café eliminado ya no esté en el carrito\n\n")
        if errores:
            txt.write("Resultado: ❌ Fallos detectados\n")
            txt.write("Errores:\n")
            for err in errores:
                txt.write(f"{err}\n")
        else:
            txt.write("Resultado: ✅ Prueba completada exitosamente\n")
        txt.write("\nCapturas guardadas en carpeta 'capturas':\n")
        for ruta in capturas:
            txt.write(f"- {ruta}\n")

    # -----------------------
    # Reporte HTML
    # -----------------------
    with open("reporte_prueba.html", "w", encoding="utf-8") as html:
        html.write(f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Prueba - Coffee Cart</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #4CAF50; }}
        .error {{ color: red; }}
        .exito {{ color: green; }}
        img {{ margin: 10px 0; border: 1px solid #ccc; }}
    </style>
</head>
<body>
    <h1>Reporte de Prueba Automatizada</h1>
    <p><strong>Fecha:</strong> {fecha}</p>
    <p><strong>URL:</strong> <a href="{URL}">{URL}</a></p>

    <h2>Cafés seleccionados (aleatorio = {cantidad}):</h2>
    <ul>
""")
        for nombre, precio in seleccionados:
            html.write(f"<li>{nombre}: {precio}</li>\n")

        html.write(f"""</ul>
    <h2>Acciones realizadas:</h2>
    <ul>
        <li>Se agregaron los cafés al carrito</li>
        <li>Se validó su presencia en el carrito</li>
        <li>Se modificaron las cantidades a valores aleatorios (2–10)</li>
        <li>Se eliminó aleatoriamente usando ❌: {nombre_eliminado}</li>
        <li>Se validó que el café eliminado ya no esté en el carrito</li>
    </ul>
""")

        if errores:
            html.write("<p class='error'><strong>Resultado:</strong> ❌ Fallos detectados</p>\n")
            html.write("<h3>Errores:</h3><ul>\n")
            for err in errores:
                html.write(f"<li>{err}</li>\n")
            html.write("</ul>\n")
        else:
            html.write("<p class='exito'><strong>Resultado:</strong> ✅ Prueba completada exitosamente</p>\n")

        html.write("""
        <h2>Capturas de pantalla:</h2>
        <ul>
            <li>Después de agregar cafés:<br><img src='capturas/agregado.png' width='400'></li>
            <li>Después de modificar cantidades:<br><img src='capturas/modificado.png' width='400'></li>
            <li>Después de eliminar café:<br><img src='capturas/eliminado.png' width='400'></li>
        """)
        if any("error" in ruta for ruta in capturas):
            for ruta in capturas:
                if "error" in ruta:
                    html.write(f"<li>Error:<br><img src='{ruta}' width='400'></li>\n")
        html.write("""
        </ul>
    </body>
</html>
""")
