import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


def navigate_to_chatgpt_and_login(username, password):
    # Initialize the WebDriver
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    try:
        # Open ChatGPT website
        driver.get('https://chat.openai.com/')
        time.sleep(5)
        # Log in
        username_field = driver.find_element(By.NAME, 'username')
        password_field = driver.find_element(By.NAME, 'password')
        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)
        print('Logged in successfully')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        driver.quit()
