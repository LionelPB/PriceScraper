"""
Price scraping utility for Amazon products.
"""
# Use BeautifulSoup for HTML parsing and Requests for HTTP requests. 
import time # For delays to avoid overloading servers and hanging the connection. 
import requests # To fetch Amazon's product page. 
from bs4 import BeautifulSoup # To extract price data from the request response. 
import os # To get environment variables for Amazon URL and price ceiling. 
import sys # In case no URL is provided. 
from playwright.sync_api import sync_playwright # To fetch the web page in case requests + bs4 were blocked. 

logs = []
AMAZON_URL = ""
HEADLESS = False # If there's a ReCAPTCHA, set this to False so you see the browser and solve it. If there are no ReCAPTCHAs, 
# you can set it to True to avoid opening a browser window. 
MAX_PRICE = 0.0
INTERVAL = 60 # Check every minute. 
PRICE_CLASS = "a-price-whole" # For non-Amazon web sites, extends compatibility by allowing to get prices from different elements. 

def log(msg: str = "") -> None: 
    """Adds a log. Logs aren't saved to any file. """
    logs.append(msg) # But do not print them unless the environment variable DEBUG is set to "true".
    if os.environ.get("DEBUG", "false").lower() == "true":
        print(msg)

try: 
    AMAZON_URL = os.environ["AMAZON_URL"]
    log("Amazon URL found in environment variable. ")
except: 
    log("Amazon URL not provided in environment variable. Retrieving from user input...")
    AMAZON_URL = input("Enter the Amazon product URL: ")
    if len(AMAZON_URL.strip()) == 0: 
        print("No URL provided. Exiting.")
        sys.exit(1)
    log("Amazon URL successfully retrieved. ")
# Now we've got the product URL to track. 
# Next: Get the price ceiling from environment variable (if possible), else from user input.
try: 
    MAX_PRICE = os.environ["MAX_PRICE"]
    MAX_PRICE = float(MAX_PRICE)
    log("Price ceiling predefined in environment variable. ")
except: 
    log("Obtaining price ceiling from user...")
    MAX_PRICE = input("Enter the maximum price you want to pay (ceiling price): ")
    if len(MAX_PRICE.strip()) == 0: 
        print("No price ceiling provided. Define it in the environment variable MAX_PRICE if you do not want to provide it now. ")
        sys.exit(1)
    else: 
        try: 
            MAX_PRICE = float(MAX_PRICE)
        except:
            print("You must give a valid number (e. g. 19.99 or only 19) for the price ceiling. ")
            sys.exit(1)
    log("Price ceiling defined by user. ")
# Now, we have both the product URL and the price ceiling. 
# Launch Playwright but only use it in case the requests + bs4 method fails.
with sync_playwright() as p:
    log("Launching Google Chrome browser...")
    browser = p.chromium.launch(headless=HEADLESS, channel="chrome")
    page = browser.new_page()
    while True:
        try: 
            log("Fetching for new price...")
            req = requests.get(AMAZON_URL, 
                            # Add fake user agents to avoid Amazon blocking the request.
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}) # This is an user agent for Chrome on Windows. 
            if req.status_code != 200: 
                raise Exception("Web page fetch failed: %d. " % (req.status_code))
            # Do not need an "else" block, if there's a non 200 status code, the exception will be raised, and this code will never be able to run. 
            content = req.content # Here's the HTML of the web page. 
        except (Exception, BaseException, KeyboardInterrupt) as error: 
            log("Unable to fetch new price: %s" % (error))
            print("Could not fetch the product page. Make sure you gave a valid URL and that you've an internet connection. \n Details: %s" % (error))
            sys.exit(1)
        # Parse the HTML response and extract the current price. 
        log("Successfully fetched the web page, extracting price...")

        try: 
            soup = BeautifulSoup(content, "html.parser")
            price_element = soup.find(class_=PRICE_CLASS) # "class_" to avoid conflicts with the "class" keyword. 
            if price_element != None: 
                price = price_element.get_text() # Get the current price. 
                price = price.strip() # Only price is kept, in case there were any spaces or newlines (unlikely, but if not from Amazon, we don't know for sure).
                log("Extracted price: %s. " % (price))
            else: 
                raise Exception("Price element with class \"%s\" not found in the web page. If the page you're fetching is not from Amazon, update PRICE_CLASS accordingly. " % (PRICE_CLASS))
        except (Exception, BaseException, KeyboardInterrupt) as error: 
            log("Unable to extract price: %s" % (error))
            print("Could not extract the price from the web page. Make sure the URL is correct. \n Details: %s" % (error))
            # sys.exit(1)
            # Try with Playwright now. 
            log("Using Playwright to fetch the web page...")
            if browser.is_connected() == False:
                log("Browser not running, maybe closed because of an error. Relaunching...")
                browser = p.chromium.launch(headless=HEADLESS, channel="chrome")
                page = browser.new_page()
                log("Successfully restarted browser. ")
            page.goto(AMAZON_URL, wait_until="load")
            # Wait for 10 seconds for the price to be here, else there's a timeout and we exit. 
            page.wait_for_selector(f".{PRICE_CLASS}", timeout=10000)
            content = page.content() # You may not know this returns the HTML updated (by JavaScript) of the web page, 
                                     #  not the raw original HTML. 
            # OK, let's try to extract the price out of the HTML. 
            try: 
                soup = BeautifulSoup(content, "html.parser")
                price_element = soup.find(class_=PRICE_CLASS) # "class_" to avoid conflicts with the "class" keyword. 
                if price_element != None: 
                    price = price_element.get_text() # Get the current price. 
                    price = price.strip() # Only price is kept, in case there were any spaces or newlines (unlikely, but if not from Amazon, we don't know for sure).
                    log("Extracted price with Playwright. " % (price))
                else: 
                    raise Exception("Price element with class \"%s\" not found in the web page. If the page you're fetching is not from Amazon, update PRICE_CLASS accordingly. " % (PRICE_CLASS))
            except (Exception, BaseException, KeyboardInterrupt) as error:
                log("Unable to extract price with Playwright: %s" % (error))
                print("Could not extract the price from the web page even with Playwright. Make sure the URL is correct and that the price element class is correct. \n Details: %s" % (error))
                sys.exit(1)
            finally: 
                # Close the browser even if everything succeeds, so it frees up RAM and CPU. 
                browser.close()
        # Because we're still here, everything went well, and we've the price as as string. 
        print("Final price: %s" % (price))
        # Wait for next update.
        time.sleep(INTERVAL)