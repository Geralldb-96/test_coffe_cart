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
    capturas.append(guardar_captura(driver, "01_agregado.png"))

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
    # Modificar cantidades con + y -
    # -----------------------
    try:
        filas = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.list-item")))
        assert filas, "No se encontraron productos en el carrito"

        fila = random.choice(filas)
        nombre = fila.find_element(By.CSS_SELECTOR, "div").text.strip()
        print(f"➡️ Se trabajará sobre el producto: {nombre}")

        boton_mas = fila.find_element(By.CSS_SELECTOR, "button[aria-label^='Add one']")
        boton_menos = fila.find_element(By.CSS_SELECTOR, "button[aria-label^='Remove one']")
        span_cantidad = fila.find_element(By.CSS_SELECTOR, "span.unit-desc")

        def obtener_cantidad():
            texto = span_cantidad.text
            return int(texto.split("x")[-1].strip())

        cantidad_objetivo_mas = random.randint(3, 6)
        valor_actual = obtener_cantidad()

        print(f"🔼 Aumentando {nombre} hasta {cantidad_objetivo_mas}...")
        while valor_actual < cantidad_objetivo_mas:
            boton_mas.click()
            time.sleep(0.3)
            valor_actual = obtener_cantidad()
        print(f"✅ {nombre} aumentado a {valor_actual}")

        ruta_suma = guardar_captura(driver, "02_aumentado.png")
        capturas.append(ruta_suma)

        cantidad_objetivo_menos = random.randint(1, valor_actual - 1)
        print(f"🔽 Disminuyendo {nombre} hasta {cantidad_objetivo_menos}...")
        while valor_actual > cantidad_objetivo_menos:
            boton_menos.click()
            time.sleep(0.3)
            valor_actual = obtener_cantidad()
        print(f"✅ {nombre} disminuido a {valor_actual}")

        ruta_resta = guardar_captura(driver, "03_disminuido.png")
        capturas.append(ruta_resta)

        assert valor_actual == cantidad_objetivo_menos, (
            f"❌ {nombre}: esperado {cantidad_objetivo_menos}, quedó {valor_actual}"
        )

    except Exception as e:
        ruta_error = guardar_captura(driver, "error_modificacion.png")
        capturas.append(ruta_error)
        errores.append(f"❌ Error al modificar cantidades con '+/-': {e}")

    # -----------------------
    # Eliminar aleatorio
    # -----------------------
    try:
        filas = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.list-item")))
        assert filas, "No se encontraron productos en el carrito"

        fila = random.choice(filas)
        nombre = fila.find_element(By.CSS_SELECTOR, "div").text.strip()
        print(f"➡️ Se trabajará sobre el producto: {nombre}")       
        boton_remove_all = fila.find_element(By.CSS_SELECTOR, "button[aria-label^='Remove all']")
        boton_remove_all.click()
        time.sleep(0.3)  # esperar que el DOM se actualice


        # Validar que ya no aparece en el carrito
        html = driver.page_source
        assert nombre not in html, f"❌ El producto '{nombre}' sigue apareciendo después de 'Remove all'"
        print(f"✅ Producto eliminado con 'Remove all': {nombre}")

    except Exception as e:
        ruta_error = guardar_captura(driver, "error_remove_all.png")
        capturas.append(ruta_error)
        errores.append(f"❌ Error en la fase de eliminación con remove all: {e}")

    capturas.append(guardar_captura(driver, "04_eliminado.png"))

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
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f8f8f8; }}
        h1 {{ color: #4CAF50; }}
        .error {{ color: red; }}
        .exito {{ color: green; }}
        .accion {{ margin: 15px 0; padding: 10px; background: #fff; border-left: 4px solid #4CAF50; }}
        img {{ margin: 10px 0; border: 1px solid #ccc; max-width: 500px; display:block; }}
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

        html.write("</ul><h2>Acciones realizadas:</h2>")

        # Acción 1: agregar cafés
        html.write(f"""
        <div class='accion'>
            <p>✅ Se agregaron {cantidad} cafés al carrito.</p>
            <img src='capturas/01_agregado.png' alt='Agregar cafés'>
        </div>
        """)

        # Acción 2: aumentar cantidad
        if "02_aumentado.png" in [os.path.basename(r) for r in capturas]:
            html.write(f"""
            <div class='accion'>
                <p>🔼 Se aumentó la cantidad de un café.</p>
                <img src='capturas/02_aumentado.png' alt='Aumentado'>
            </div>
            """)

        # Acción 3: disminuir cantidad
        if "03_disminuido.png" in [os.path.basename(r) for r in capturas]:
            html.write(f"""
            <div class='accion'>
                <p>📉 Se disminuyó la cantidad del mismo café.</p>
                <img src='capturas/03_disminuido.png' alt='Disminuido'>
            </div>
            """)

        # Acción 4: eliminación
        html.write(f"""
        <div class='accion'>
            <p>🗑️ Se eliminó aleatoriamente el café: <strong>{nombre_eliminado}</strong>.</p>
            <img src='capturas/04_eliminado.png' alt='Eliminado'>
        </div>
        """)

        # Errores
        if errores:
            html.write("<h2 class='error'>❌ Fallos detectados</h2><ul>")
            for err in errores:
                html.write(f"<li>{err}</li>")
            html.write("</ul>")
        else:
            html.write("<h2 class='exito'>✅ Prueba completada exitosamente</h2>")

        # Capturas adicionales de error
        for ruta in capturas:
            if "error" in ruta:
                html.write(f"""
                <div class='accion'>
                    <p class='error'>⚠️ Captura de error:</p>
                    <img src='{ruta}' alt='Error'>
                </div>
                """)

        html.write("""
</body>
</html>
""")
