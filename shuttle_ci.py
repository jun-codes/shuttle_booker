"""CI copy of shuttle_eff.py. Booking logic is identical; only these differ:
 - email/password come from env vars (GitHub Secrets)
 - Chrome runs headless
 - inputs come from CLI args instead of input()
 - pyautogui import and page_source dump removed
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
import base64
import sys
import argparse
import urllib.request
from datetime import datetime, timedelta


opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1920,1080")
opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
opts.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=opts)


def _debug_dump(exc_type, exc, tb):
    # On any crash, save what the browser was showing (uploaded as an artifact by the workflow)
    try:
        os.makedirs("debug", exist_ok=True)
        driver.save_screenshot("debug/failure.png")
        with open("debug/failure.txt", "w", encoding="utf-8") as f:
            f.write(driver.current_url + "\n\n" + driver.find_element(By.TAG_NAME, "body").text)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc, tb)


sys.excepthook = _debug_dump
BOOKING_LINK = "a.bus-booking.modern-link.new-link"


def load_cookies():
    # Reuse a logged-in session exported by export_cookies.py (secret MIS_COOKIES)
    blob = os.environ.get("MIS_COOKIES")
    if not blob:
        print("MIS_COOKIES not set; will log in with Google")
        return False
    try:
        cookies = json.loads(base64.b64decode(blob))
        for c in cookies:
            c = dict(c)
            if c.get("expires", -1) in (-1, 0, None):
                c.pop("expires", None)  # session cookie
            driver.execute_cdp_cmd("Network.setCookie", c)
        print(f"Loaded {len(cookies)} cookies")
        return True
    except Exception as e:
        print(f"Could not load cookies: {e}")
        return False


def google_login():
    email_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "identifierId"))
    )
    email_input.send_keys(os.environ["ASHOKA_EMAIL"])
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
    ).click()

    password_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "Passwd"))
    )
    password_input.send_keys(os.environ["ASHOKA_PASSWORD"])
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
    ).click()


HOME = 'https://busgreen.moveinsync.com/bookings/#/'

used_cookies = load_cookies()
logged_in = False
driver.get('http://ashokauniversity.moveinsync.com/ASHR')
if used_cookies:
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, BOOKING_LINK))
        )
        logged_in = True
        print("Cookie session is valid; skipping Google login")
    except Exception:
        print("Cookie session rejected or expired (re-run export_cookies.py); falling back to Google login")
        driver.get('http://ashokauniversity.moveinsync.com/ASHR')

if not logged_in:
    google_login()


def notify(msg):
    print(msg, flush=True)
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print("NTFY_TOPIC secret is not set; nothing sent to the website")
        return
    try:
        req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=msg.encode(),
                                     headers={"Title": "Shuttle bot"})
        print("ntfy response:", urllib.request.urlopen(req, timeout=20).status, flush=True)
    except Exception as e:
        print(f"ntfy failed: {e}")


def handle_2fa():
    # If Google shows the "tap the number on your phone" screen, push that number to the phone.
    end = time.time() + 15
    while time.time() < end:
        if driver.find_elements(By.CSS_SELECTOR, "a.bus-booking.modern-link.new-link"):
            return
        try:
            lines = driver.find_element(By.TAG_NAME, "body").text.splitlines()
        except Exception:
            lines = []
        nums = [l.strip() for l in lines if l.strip().isdigit() and len(l.strip()) <= 3]
        if nums:
            break
        time.sleep(1)
    else:
        nums = []
    notify(f"Tap {nums[0]} on your phone" if nums else "Approve the Google login on your phone")


if not logged_in:
    handle_2fa()

bus_booking_link = WebDriverWait(driver, 180).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, BOOKING_LINK))
)
bus_booking_link.click()

def bookshuttle(user_time, source, dest, seat_number, change_date, time_window_plus, time_window_minus):

    base_time = datetime.strptime(user_time, "%H:%M")
    time_list = []
    time_window = []

    for i in range(0, (-time_window_minus)-1, -1):
        if i%15 == 0:
            time_window.append(i)

    for i in range(time_window_plus+1):
        if i%15 ==0:
            time_window.append(i)

    print(time_window)

    for offset in time_window:
        t = base_time + timedelta(minutes=offset)
        time_list.append(t.strftime("%H:%M"))


    source = source.strip()
    dest = dest.strip()

    driver.get(HOME)

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//button[@aria-label='{source}']")
        )
    ).click()

    time.sleep(1)

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//button[@aria-label='{dest}']")
        )
    ).click()

    if change_date ==  True:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@role='button' and starts-with(@aria-label, 'Date selection')]")
            )
        ).click()

        tomorrow = (datetime.now() + timedelta(days=1)).day

        element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
                (By.XPATH, f"//span[contains(@class, 'mat-calendar-body-cell-content') and normalize-space()='{tomorrow}']")
            )
        )

        element.click()
        time.sleep(0.2)
        element.click()


    while True:
        try:
            dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[starts-with(@aria-label, 'Pickup Time')]"))
                )

            dropdown.click()
            timing = None

            print("checking the following:", time_list)

            for t in time_list:
                try:
                    timing = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, f"//button[starts-with(@aria-label, '{t},')]")
                        )
                    )
                    break
                except:
                    pass

            if timing is None:
                raise Exception("no time found")

            timing.click()
            break

        except Exception as e:
            print(f"Error occurred: {e}")
            print(f"Time {user_time} not available or error occurred, reloading the page and starting over...")
            try:
                cancel_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[normalize-space()='Cancel']")
                    )
                )
                cancel_button.click()
            except:
                continue
            continue


    apply = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Apply')]"))
    )
    apply.click()

    showshuttle = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show Shuttles')]"))
    )
    showshuttle.click()

    seats_count = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "seats-count"))
    ).text

    seats_count = (int((seats_count.split())[0]))

    if seats_count >= 3 and seat_number == 3:
        seatnumber = 3
    elif seats_count >= 2 and seat_number >= 2:
        seatnumber = 2
    elif seats_count >= 1 and seat_number >= 1:
        seatnumber = 1

    increase_seat = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable(
        (By.XPATH, "//mat-icon[normalize-space()='add']")
        )
    )

    if seatnumber == 3:
        increase_seat.click()
        increase_seat.click()
    elif seatnumber == 2:
        increase_seat.click()

    seat = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button[aria-label='Request a seat']")
        )
    )
    seat.click()

    if seatnumber > 1:

        reason = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='radio'][name='selectedReason']"))
        )
        reason.click()

        proceed = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Proceed']")
            )
        )
        proceed.click()

    confirm = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable(
        (By.CSS_SELECTOR, ".rsd__btn.rsd__btn--confirm")
        )
    )
    confirm.click()
    print("Booked a seat on: ")
    print(time.ctime())

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--dest", required=True)
    p.add_argument("--date", choices=["today", "tomorrow"], default="today")
    p.add_argument("--time", required=True)
    p.add_argument("--before", type=int, default=0)  # minutes, positive number
    p.add_argument("--after", type=int, default=0)
    p.add_argument("--seats", type=int, choices=[1, 2, 3], default=1)
    a = p.parse_args()

    bookshuttle(a.time, a.source, a.dest, a.seats, a.date == "tomorrow", a.after, -a.before)
