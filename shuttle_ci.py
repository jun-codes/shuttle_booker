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
import argparse
from datetime import datetime, timedelta


opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=opts)
driver.get('http://ashokauniversity.moveinsync.com/ASHR')


email_input = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "identifierId"))
)

email_input.send_keys(os.environ["ASHOKA_EMAIL"])

next_button1 = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
)

next_button1.click()

password_input = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.NAME, "Passwd"))
)

password_input.send_keys(os.environ["ASHOKA_PASSWORD"])

next_button2 = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
)

next_button2.click()

bus_booking_link = WebDriverWait(driver, 60).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.bus-booking.modern-link.new-link"))
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


    driver.get('https://bus-neo.moveinsync.com/bookings#/')
    time.sleep(3)
    source = source.strip()
    dest = dest.strip()

    driver.get('https://busgreen.moveinsync.com/bookings/#/')

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
