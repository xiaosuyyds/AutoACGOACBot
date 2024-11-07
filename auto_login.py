import os
import time
import sys
import constants
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

work_path = os.path.dirname(os.path.abspath(__file__))

options = None
service = None


def init():
    global options, service
    options = webdriver.ChromeOptions()
    if sys.platform == 'linux' or sys.platform == 'darwin':
        service = Service(executable_path='./chromedriver')
    else:
        service = Service(executable_path='./chromedriver.exe')


def refresh_cookie():
    global options, service
    if options is None or service is None:
        init()
    print('正在启动浏览器')
    options = webdriver.ChromeOptions()
    if sys.platform == 'linux' or sys.platform == 'darwin':
        # 如果是linux就不显示ui，防止一些系统无gui导致的错误
        options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
    else:
        pass
    options.add_argument("--mute-audio")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options, service=service)
    # driver = webdriver.Chrome(options=options)
    driver.delete_all_cookies()

    print('正在打开网页')
    driver.get("https://www.acgo.cn/discuss")

    driver.implicitly_wait(0.5)

    elements = driver.find_elements(by=By.TAG_NAME, value="button")
    for element in elements:
        if element.text == "发起讨论":
            element.click()
            break

    driver.implicitly_wait(3)
    print('正在登录')
    # 登录界面
    login = driver.find_element(by=By.CLASS_NAME, value="login-form")
    inputs = login.find_element(by=By.CLASS_NAME, value="form_wrap")
    print('正在输入账号密码')
    # 输账号&密码
    element = inputs.find_element(by=By.ID, value="username")
    username = os.environ.get('ACGO_USERNAME')
    if not username:
        username = constants.LOGIN_USERNAME
    element.send_keys(username)
    driver.implicitly_wait(0.5)
    element = inputs.find_element(by=By.ID, value="pwd")
    password = os.environ.get('ACGO_PASSWORD')
    if not password:
        password = constants.LOGIN_PASSWORD
    element.send_keys(password)
    # element.send_keys('test')
    driver.implicitly_wait(2)
    # 点同意协议
    print('正在同意协议')
    element = login.find_element(by=By.CLASS_NAME, value="xmloginant-checkbox-input")
    element.click()
    driver.implicitly_wait(2)
    print('正在登录')
    # 登录！
    element = login.find_element(by=By.ID, value="login")
    element.click()

    driver.implicitly_wait(3)
    time.sleep(1.5)

    cookie = driver.get_cookie('user_token')

    driver.quit()

    if cookie:
        print(f'登录成功 cookie: {cookie.get("value")}')
        return cookie.get('value')
    else:
        print('登录失败')
        return None
