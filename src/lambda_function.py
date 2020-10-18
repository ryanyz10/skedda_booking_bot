import time
import os
import datetime

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


def lambda_handler(event, context):
    # setup chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.add_argument('--user-data-dir=/tmp/user-data')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--v=99')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--data-path=/tmp/data-path')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--homedir=/tmp')
    chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
    chrome_options.binary_location = os.getcwd() + "/bin/headless-chromium"

    chromedriver_location = os.getcwd() + "/bin/chromedriver"

    driver = webdriver.Chrome(chromedriver_location,
                              chrome_options=chrome_options)

    return main(driver)


def main(driver):
    login(driver)
    change_days(driver)

    booked_times = get_booked_times(driver)

    to_book = get_earliest_booking_time(booked_times)

    if to_book is None:
        raise Exception("lambda_function.main: No times were available")

    td_num = time_to_td(to_book)

    if not book(driver, td_num):
        raise Exception("lambda_function.main: booking failed to go through")

    driver.close()
    driver.quit()


def login(driver):
    BASE_URL = "https://{}.skedda.com/booking".format(
        os.environ["SKEDDA_VENUE_NAME"])
    LOGIN_URL = "https://www.skedda.com/account/login?returnUrl={}".format(
        BASE_URL)

    driver.get(LOGIN_URL)

    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@name='username']"))).send_keys(os.environ["SKEDDA_USERNAME"])
    except:
        raise Exception("lambda_function.login: failed to input username")

    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@name='password']"))).send_keys(os.environ["SKEDDA_PASSWORD"])
    except:
        raise Exception("lambda_function.login: failed to input password")

    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@type='submit']"))).click()
    except:
        raise Exception("lambda_function.login: failed to login")


def change_days(driver, num_days=7):
    # xpath = "//button[@title='Next day']"
    xpath = "(//button[@type='button'])[8]"

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
    except:
        raise Exception(
            "lambda_function.change_days: failed to find next days button")

    next_day_button = driver.find_element_by_xpath(xpath)

    for _ in range(num_days):
        next_day_button.click()
        time.sleep(0.5)


def get_booked_times(driver):
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "booking-div")))
    except:
        return []

    booking_texts = driver.find_elements_by_xpath(
        "//span[@class='font-weight-semi-bold']")

    booking_times = []

    for booking_text in booking_texts:
        start, end = booking_text.text.split('–')
        start = datetime.datetime.strptime(start, "%I:%M %p").time()
        end = datetime.datetime.strptime(end, "%I:%M %p").time()

        booking_times.append((start, end))

    return booking_times


def get_earliest_booking_time(booked_times):
    """
    gets a list of returned times and returns the earliest available time of 7, 7:30 or 8pm
    """
    # the booked times should already be sorted, and there should also be no overlaps
    # find the earliest time of 7, 7:30, 8 to book
    to_book = datetime.time(hour=19, minute=0)
    for (start, end) in booked_times:
        if end.hour < 19 or end.hour > 20:
            continue

        if end.hour == 19:
            if end.minute > 30:
                to_book = to_book.replace(hour=20)
            elif end.minute > 0 and end.minute <= 30:
                to_book = to_book.replace(hour=19, minute=30)

        if end.hour == 20:
            if end.minute > 0:
                to_book = None
                break

    return to_book


def book(driver, td_num):
    tds = driver.find_elements_by_xpath("//td[@role='button']")
    tds[td_num].click()

    WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class, 'btn-success')]"))).click()

    WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class, 'dropdown')]")))

    driver.find_elements_by_xpath(
        "//button[contains(@class, 'dropdown')]")[1].click()

    driver.find_elements_by_xpath(
        "//a[contains(@class, 'dropdown-item')]")[6].click()

    driver.find_elements_by_xpath(
        "(//button[contains(@class, 'btn-success')]")[1].click()

    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'alert-danger')]")))
    except:
        return True

    return False


def time_to_td(time):
    return (time.hour - 7) * 4 + (time.minute // 15)
