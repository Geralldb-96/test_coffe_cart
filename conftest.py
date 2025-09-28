import pytest
from selenium import webdriver

@pytest.fixture
def browser():
    # Inicializa Chrome con Selenium Manager
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    # Cierra el navegador al terminar la prueba
    driver.quit()
