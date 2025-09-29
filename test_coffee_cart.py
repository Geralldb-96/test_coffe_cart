import pytest
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://coffee-cart.app/"

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def test_agregar_cafes_aleatorios(driver):
    driver.get(URL)
    wait = WebDriverWait(driver, 40)

    # Esperar carga completa
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    # Extraer cafés
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

    # Elegir cantidad aleatoria entre 1 y 9
    cantidad = random.randint(1, len(productos))
    seleccionados = productos[:cantidad]

    print(f"🎲 Seleccionando {cantidad} cafés aleatorios:")
    for nombre, precio in seleccionados:
        print(f"- {nombre}: {precio}")

    # Agregar cafés seleccionados
    for i in range(cantidad):
        try:
            selector = f"li:nth-child({i+1}) div.cup-body"
            cafe_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            cafe_element.click()
            print(f"✅ Café agregado: {productos[i][0]}")
        except Exception as e:
            pytest.fail(f"❌ Error al agregar café #{i+1}: {e}")

    # Ir al carrito
    try:
        cart_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/cart"]')))
        cart_link.click()
        print("🛒 Navegación al carrito realizada")
    except Exception as e:
        pytest.fail(f"❌ Error al ir al carrito: {e}")

    # Validar que los cafés estén en el carrito
    try:
        assert "/cart" in driver.current_url, f"URL inesperada: {driver.current_url}"
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        html = driver.page_source
        for nombre, _ in seleccionados:
            assert nombre in html, f"No se encontró '{nombre}' en el carrito"
            print(f"✅ Validado en carrito: {nombre}")
    except Exception as e:
        driver.save_screenshot("error_validacion_carrito.png")
        pytest.fail(f"❌ Validación del carrito falló: {e}")