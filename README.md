# Shuttle Booker

Books an Ashoka University MoveInSync shuttle seat with Selenium. It runs on a free GitHub Actions
runner, triggered from a static website on GitHub Pages. No server and no paid hosting.

```
docs/index.html (GitHub Pages)
   │  POST workflow_dispatch (GitHub API, fine-grained token kept in the browser's localStorage)
   ▼
.github/workflows/book.yml  ──►  shuttle_ci.py (headless Chrome + Selenium)  ──►  MoveInSync
   ▲                                   │
   │ polls run status                  └─ posts the Google 2FA number to ntfy.sh
   └──────── docs/index.html listens to the same ntfy topic and shows the number on screen
```

## Files
| File | Purpose |
|---|---|
| `shuttle_eff.py` | Original local script (interactive `input()`, visible Chrome). Untouched. |
| `shuttle_ci.py` | CI copy. Same booking logic; see "Differences" below. |
| `.github/workflows/book.yml` | `workflow_dispatch` workflow. Inputs: source, dest, date, time, before, after, seats. |
| `docs/index.html` | The website: form, run status (🟡/🟢/🔴), and the 2FA number display. |
| `requirements.txt` | `selenium` only (Chrome is preinstalled on `ubuntu-latest`). |

## Differences between `shuttle_ci.py` and `shuttle_eff.py`
- Email and password come from env vars `ASHOKA_EMAIL` and `ASHOKA_PASSWORD`.
- Chrome is headless (`--headless=new`, `--no-sandbox`, and so on) with a normal desktop user-agent.
- Inputs come from CLI args (`--source --dest --date --time --before --after --seats`), not `input()`.
  `--before` is a positive number, and it's negated before it reaches `bookshuttle`.
- Removed `pyautogui` and the `page_source` dump (public repo logs).
- Added `handle_2fa()` and `notify()` (see below).
- A crash hook saves `debug/failure.png` and `debug/failure.txt` (the URL and page text).
  The workflow uploads them as the `debug` artifact when a run fails.
- The wait for the bus-booking link is 180 s (it was 60 s) to leave time for the 2FA tap.

## One-time setup
1. Push the repo. Check the default branch name (`main` or `master`), since the site's Branch setting must match it.
2. Repo → Settings → Secrets and variables → Actions → **Repository secrets**:
   - `ASHOKA_EMAIL`
   - `ASHOKA_PASSWORD`
   - `NTFY_TOPIC`, a long random string such as `shuttle-yourname-8f3k29xq`. It acts as a shared secret for the topic.
3. Repo → Settings → Pages → Deploy from a branch → your default branch, folder `/docs`.
   The site is at `https://<user>.github.io/<repo>/`.
4. Create a fine-grained personal access token. Limit it to this repo only, with Actions: Read and write.
5. Open the site → Settings: enter `owner/repo`, the token, the branch, and the same ntfy topic. Click Save.
   These are stored only in that browser's localStorage.

## Google 2FA (the main gotcha)
The runner is a new device on a datacenter IP every time, so Google always asks for "Verify it's you",
a number-match prompt on the phone. It can't be bypassed. The flow is:
1. The bot enters the email and password, then `handle_2fa()` polls the page for up to 15 s for a line that is 1 to 3 digits.
2. It calls `notify("Tap NN on your phone")`, which prints to the logs and POSTs to `https://ntfy.sh/<NTFY_TOPIC>`.
3. The website listens with `EventSource(https://ntfy.sh/<topic>/sse?since=<now>)` and shows the number.
   The page only sees messages sent after Book is clicked, so keep the tab open.
4. The user taps **Yes**, then the number, on their phone, within about 3 minutes. The bot waits up to 180 s for the home page.
5. The number is also always in the Actions log ("Tap NN on your phone"), which works as a fallback.

If the `NTFY_TOPIC` secret is missing, the log says `NTFY_TOPIC secret is not set` and the site shows nothing.
Each run gets a new number, so approving an old run's number does nothing.

### Cookie reuse (skips Google and 2FA)
1. Locally run `python export_cookies.py`, log in, and press Enter at each prompt. It writes `cookies.b64.txt` (git-ignored).
2. Paste its contents into the repo secret `MIS_COOKIES`.
3. `shuttle_ci.py` loads those cookies (CDP `Network.setCookie`) and goes straight to the booking page.
   If the session is rejected, it logs "Cookie session rejected or expired" and falls back to the Google login + 2FA flow.
4. When runs start falling back, re-run the export script and update the secret.

Untested against MoveInSync: if it ties sessions to an IP, this fails and the fallback applies. Only cookies are
exported; if the booking apps keep their token in localStorage, this will need extending.

## Behaviour and limits
- The runner's timezone is set to `Asia/Kolkata` (`TZ` in the workflow) so "tomorrow" is the IST date.
- The workflow has `timeout-minutes: 30`. The hard GitHub limit is 360. Public repos have unlimited free minutes,
  and private repos get 2,000 per month.
- If no slot is found, the original `while True` loop in `bookshuttle` retries forever (about 20 s per attempt)
  until the timeout. Logs show `checking the following: [...]` and `Error occurred: ...` each pass.
  The empty text after "Error occurred:" is normal for Selenium timeouts.
- Public repo on the free Pages plan means the logs are public. Never print secrets or page contents.

## Known issues in the booking logic (not fixed, kept identical to the original)
- `seatnumber` is unbound (crash) if `seats_count` is 0.
- The retry loop is infinite and never reloads the page, despite the message saying it does.
- The local script rejects a window of 0 (`if time_window_plus:`). The CI copy allows 0.

## Debugging checklist
- **422 "No ref found for: main"**: the branch name in the site's Settings is wrong (probably `master`).
- **404 on dispatch**: the workflow file isn't on that branch, or the token lacks access to the repo.
- **Timeout at the "Next" button or the bus-booking link**: download the `debug` artifact from the failed run
  (run page → Artifacts) and read `failure.txt`. It shows the URL and the text of the page the browser was stuck on.
  So far this has been Google's 2FA screen.
- **No number on the site**: check that the log doesn't say `NTFY_TOPIC secret is not set`, that the topic in the site's Settings matches
  the secret exactly, and that the page was open before the number was posted.

## Status
Working: dispatch from the site, run tracking, Google email and password entry, 2FA number detection.
Not yet confirmed end to end: a full booking, because the 2FA tap has not yet succeeded within the wait window.
