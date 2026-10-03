"""Run this LOCALLY (not in CI). Opens a visible Chrome, you log in to MoveInSync via Google,
then press Enter. The MoveInSync cookies are written to cookies.b64.txt; paste its contents
into the GitHub secret MIS_COOKIES. Re-run whenever the CI session expires.
"""

import base64
import json
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("http://ashokauniversity.moveinsync.com/ASHR")
input("Log in with Google (until you see the bus-booking link), then press Enter here... ")

driver.get("https://busgreen.moveinsync.com/bookings/#/")
input("Open the bus-booking link if this page didn't load logged in; once the booking home page shows, press Enter... ")

cookies = driver.execute_cdp_cmd("Network.getAllCookies", {})["cookies"]
cookies = [c for c in cookies if "moveinsync" in c["domain"]]
driver.quit()

keep = ("name", "value", "domain", "path", "secure", "httpOnly", "sameSite", "expires")
slim = [{k: c[k] for k in keep if k in c} for c in cookies]
blob = base64.b64encode(json.dumps(slim).encode()).decode()

with open("cookies.b64.txt", "w") as f:
    f.write(blob)
print(f"Saved {len(slim)} cookies ({len(blob)} chars) to cookies.b64.txt")
print("Paste that file's contents into the repo secret MIS_COOKIES (limit is 48 KB).")
