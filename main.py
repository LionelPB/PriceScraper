"""
Price scraping utility for Amazon products.
"""
# Use BeautifulSoup for HTML parsing and Requests for HTTP requests. 
import time # For delays to avoid overloading servers and hanging the connection. 
import requests # To fetch Amazon's product page. 
from bs4 import BeautifulSoup # To extract price data from the request response. 
import os # To get environment variables for Amazon URL and price ceiling. 
import sys # In case no URL is provided. 

logs = []
AMAZON_URL = ""
MAX_PRICE = 0.0
INTERVAL = 4 # Check every minute. 
PRICE_ID = "priceblock_ourprice" # For non-Amazon web sites, extends compatibility by allowing to get prices from different elements. 

def log(msg: str = "") -> None: 
    """Adds a log. Logs aren't saved. """
    logs.append(msg) # But do not print them unless the environment variable DEBUG is set to "true".
    if os.environ.get("DEBUG", "false").lower() == "true":
        print(msg)
    else: 
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



    # Wait for next update.
    time.sleep(INTERVAL)