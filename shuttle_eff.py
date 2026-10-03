"""from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(ChromeDriverManager().install())

"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pyautogui
from datetime import datetime, timedelta
from selenium.webdriver.chrome.service import Service




driver = webdriver.Chrome()
driver.get('http://ashokauniversity.moveinsync.com/ASHR')


email_input = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "identifierId"))
)

email_input.send_keys("arjun.singh_ug2023@ashoka.edu.in")

next_button1 = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
)

next_button1.click()

password_input = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.NAME, "Passwd"))
)

password_input.send_keys("")

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
    
    print(driver.page_source)
    
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
        """screen_width, screen_height = pyautogui.size()
        x = screen_width * 0.08
        y = (screen_height / 1.98) - 40
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.click()
       
        today = datetime.today()
        tomorrow = today + timedelta(days=1)
        formatted_tomorrow = tomorrow.strftime("%B ") + str(tomorrow.day) + tomorrow.strftime(", %Y")
       
        aria_label = formatted_tomorrow
        print(f"Trying to select date: {aria_label}")  # Debug print to check the aria-label format
        date_cell = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//td[@aria-label='{aria_label}']"))
        )
        date_cell.click()
        time.sleep(0.5)
        date_cell.click()"""

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

    while True:
        try:
            source = input("Enter Source (A for Ashoka, AZ for Azadpur): ").strip().upper()
            if source == 'A':
                source = "Ashoka University"
                break
            elif source == 'AZ':
                source = "Azadpur"
                break
            else:
                print("Invalid input. Please enter A or J.")
        except Exception as e:
            print(f"Error: {e}")

    while True:
        try:
            dest = input("Enter Destination (A for Ashoka, AZ for Azadpur): ").strip().upper()
            if dest == 'A':
                dest = "Ashoka University"
                break
            elif dest == 'AZ':
                dest = "Azadpur"
                break
            else:
                print("Invalid input. Please enter A or J.")
        except Exception as e:
            print(f"Error: {e}")

    change_date = False
   
    while True:
        try:
            date_choice = input("Book for today or tomorrow? (today/tomorrow): ").strip().lower()
            if date_choice in ["tomorrow", "tom"]:
                change_date = True
                break
            if date_choice == 'today':
                break
            else:
                print("Invalid choice. Enter 'today' or 'tomorrow'.")
        except Exception as e:
            print(f"Error: {e}")


    while True:
        try:
            user_time = input("Enter the time you want to book the shuttle (e.g., '10:00'): ").strip()
            if user_time:
                break
            else:
                print("Time cannot be empty.")
        except Exception as e:
            print(f"Error: {e}")

    while True:
        try:
            time_window_plus = int(input("Enter the number of additional minutes to search for (multiple of 15) "))
            if time_window_plus:
                break
            else:
                print("Time cannot be empty.")
        except Exception as e:
            print(f"Error: {e}")

    while True:
        try:
            time_window_minus = int(input("Enter the number of additional negative minutes to search for (multiple of 15) "))
            if time_window_minus:
                break
            else:
                print("Time cannot be empty.")
        except Exception as e:
            print(f"Error: {e}")


    while True:
        try:
            seat_number = int(input("Enter number of seats (1-3): "))
            if seat_number in [1, 2, 3]:
                break
            else:
                print("Please enter a value between 1 and 3.")
        except Exception:
            print("Please enter a valid integer.")
           

    bookshuttle(user_time, source, dest, seat_number, change_date, time_window_plus, time_window_minus)
