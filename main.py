import re, os
import pytesseract
import time
import random
import string
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance, ImageFilter
from playwright.sync_api import Playwright, sync_playwright
from io import BytesIO

def generate_random_string(length, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))
    
def generate_random_username():
    username = ''.join(random.choices(string.ascii_lowercase, k=10))
    return username

def generate_random_email(username):
    api_address = "https://api.mail.tm"
    domains = requests.get(f"{api_address}/domains").json()["hydra:member"]
    domain = random.choice(domains)["domain"]
    return f"{username}@{domain}"

def generate_random_string(length, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))
def generate_random_password():
    return generate_random_string(random.randint(8, 32))

def fill_input_slowly(page, locator, text, delay=1):
    input_box = page.frame_locator("#signup_popup_text iframe").locator(locator)
    for char in text:
        input_box.evaluate(f"""(input, char) => {{
            return new Promise(resolve => {{
                setTimeout(() => {{
                    input.value += char;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    resolve();
                }}, {int(delay * 1000)});
            }});
        }}""", char)


def run(playwright: Playwright) -> None:
    ran_user = generate_random_username()
    ran_email = generate_random_email(ran_user)
    ran_pass = generate_random_password()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    time.sleep(0.2)
    page.goto("https://seo-rank.my-addr.com/")
    time.sleep(0.2)
    page.get_by_role("link", name="Sign UP", exact=True).click()
    time.sleep(0.2)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"username\"]").click()
    time.sleep(2)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"username\"]").fill(ran_user)
    time.sleep(2)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"email\"]").click()
    time.sleep(2)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"news\"]").check()
    time.sleep(2)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"email\"]").fill(ran_email)
    time.sleep(6)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"password1\"]").click()
    time.sleep(2)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"password1\"]").fill(ran_pass)
    time.sleep(2)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"password2\"]").click()
    time.sleep(3)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"password2\"]").fill(ran_pass)
    time.sleep(3)
    captcha_image_locator = page.frame_locator("#signup_popup_text iframe").get_by_role("cell", name="Input sum of", exact=True).get_by_role("img").element_handle()
    captcha_image_screenshot_bytes = captcha_image_locator.screenshot()
    captcha_image = Image.open(BytesIO(captcha_image_screenshot_bytes))
    captcha_image.save("captcha.png")
    captcha_text = solve_captcha("captcha.png")
    os.remove("captcha.png")
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"image_string\"]").click()
    time.sleep(5)
    captcha_input_locator = "input[name=\"image_string\"]"
    fill_input_slowly(page, captcha_input_locator, captcha_text)
    #page.frame_locator("#signup_popup_text iframe").locator("input[name=\"image_string\"]").fill(captcha_text)
    time.sleep(0.2)
    page.frame_locator("#signup_popup_text iframe").locator("input[name=\"agreement\"]").check()
    time.sleep(0.2)
    page.frame_locator("#signup_popup_text iframe").get_by_role("button", name="Submit").click()
    time.sleep(5)
    page.get_by_role("link", name="My Dashboard").click()
    time.sleep(0.2)
    html_content = page.evaluate('document.documentElement.outerHTML')
    time.sleep(0.2)
    soup = BeautifulSoup(html_content, 'html.parser')
    element = soup.find(True, {'style': 'padding:10px 10px 10px 2px; text-align:center; color:#000000; '})
    key = element.get_text(strip=True)
    print(key)
    red_span = soup.find('span', class_='red')
    if red_span:
        if "increase your balance" in red_span.get_text():
            print("Balance: 0")
            open('Used.txt', "a").write(f"Username: {ran_user}  \nUsermail: {ran_email} \nPassword: {ran_pass} \nKEY: {key} \nBalance: 0 \n ")
        else:
            print("Balance: Not 0")
            open('Valid.txt', "a").write(
                f"Username: {ran_user}  \nUsermail: {ran_email} \nPassword: {ran_pass} \nKEY: {key} \nBalance: 100 \n ")
    else:
        print("Balance: 0")
        open('Used.txt', "a").write(
            f"Username: {ran_user}  \nUsermail: {ran_email} \nPassword: {ran_pass} \nKEY: {key} \nBalance: 0 \n ")
        
    time.sleep(10)
    context.close()
    browser.close()


def preprocess_image(image):
    image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    image = image.filter(ImageFilter.GaussianBlur(radius=1))
    return image

def post_process_captcha_text(text):
    text = text.replace('4+', '+')
    return text


def solve_captcha_sum(captcha_text):
    pattern = r'(\d+)\s*([+\-*/])\s*(\d+)'
    match = re.search(pattern, captcha_text)
    if match:
        operand1 = int(match.group(1))
        operator = match.group(2)
        operand2 = int(match.group(3))
        if operator == '+':
            result = operand1 + operand2
        elif operator == '-':
            result = operand1 - operand2
        elif operator == '*':
            result = operand1 * operand2
        elif operator == '/':
            result = operand1 / operand2
        else:
            result = None

        return result
    else:
        return None
def solve_captcha(image_path: str) -> float | int | None | str:
    try:
        custom_config = r'--oem 3 --psm 6'
        captcha_text = pytesseract.image_to_string(Image.open(image_path), config=custom_config)
        captcha_text = post_process_captcha_text(captcha_text)
        captcha_text = solve_captcha_sum(captcha_text)
        return str(captcha_text)
    except Exception as e:
        print("Error :", e)
        return ""

with sync_playwright() as playwright:
    while True:
        run(playwright)
