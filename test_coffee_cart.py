import pytest
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def test_extraer_cafes(browser):
    # Abrir la página
    browser.get("https://coffee-cart.app/")

    # Esperar a que la página cargue completamente
    WebDriverWait(browser, 30).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )

    # Extraer todos los cafés y precios usando JavaScript (compatible con SPA)
    productos = browser.execute_script("""
        let items = [];
        document.querySelectorAll('h4').forEach(h4 => {
            let precio = h4.nextElementSibling ? h4.nextElementSibling.innerText : '';
            items.push({nombre: h4.innerText, precio: precio});
        });
        return items;
    """)

    # Mostrar en consola
    print("Cafés encontrados:")
    for cafe in productos:
        print(cafe)

    # Guardar en JSON
    with open("cafes.json", "w", encoding="utf-8") as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)

    # Validar que se haya extraído al menos un café
    assert len(productos) > 0