"""
Here's the GUI version of "main.py". 
It lets you search directly on Amazon to avoid having to get the right product URL. 
"""
from tkinter import *
from tkinter import ttk # Updated widgets. 
from playwright.sync_api import sync_playwright  # Manipulate the browser to search on Amazon for the user. 
from bs4 import BeautifulSoup
import threading

import io # To store previews in RAM
import requests # To get previews 
import PIL.Image, PIL.ImageTk # To show previews (default format in Amazon is JPEG). 

BASE_URL = "https://www.amazon.es/"
SEARCH_URL = BASE_URL + "s?k=" # This is the Amazon search URL. 
HEADLESS = False # Set this to "False" to see the browser, if it is in "True", then the browser window won't be visible. 

def search_products(): 
    """Finds products on Amazon by using Playwright. """
    global searchThread
    text = search.get().lower().strip()
    if len(text) == 0: # Nothing to do
        return
    goSearch.configure(state=DISABLED, text="Please wait...")
    search.configure(state=DISABLED)
    root.update()
    clean = text.replace(" ", "+") # Browser should complete this. 
    searchThread = threading.Thread(target=search_amazon, args=(clean, ), daemon=True) # The last arguments avoids us having to manage the thread. 
    searchThread.start()
def loader_text(newText: str): 
    search_text.set(newText)
def search_amazon(text, *args, **kwargs): 
    """Headlessy opens a browser, and searches Amazon"""
    loader_text("Starting browser...")
    url = SEARCH_URL + text
    found = [] # What we got back. 

    try: 
        with sync_playwright() as p: 
            browser = p.chromium.launch(headless=HEADLESS, channel="chrome")
            loader_text("Opening tab...")
            tab = browser.new_page()
            loader_text("Searching...")
            tab.goto(url, wait_until="load", timeout=40000)
            html = tab.content()
            browser.close() # We don't need it anymore. 
        # Get out of here to close the browser. 
        loader_text("Extracting data...")
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select('div[data-component-type="s-search-result"], div.s-result-item')
        for item in items: 
            title = item.select_one('[data-cy="title-recipe"] h2 span') # Extract title
            if title == None: 
                continue
            title = title.get_text(strip=True)
            price = item.select_one('[data-cy="price-recipe"] .a-price .a-offscreen')
            price = price.get_text(strip=True) if price else "Not available"
            img = item.select_one('img.s-image')
            img = img['src'] if img and img.has_attr('src') else None
            link = item.select_one('[data-cy="title-recipe"] a')
            link = BASE_URL + link['href'] if link and link.has_attr('href') else None
            found.append({
                "title": title, 
                "price": price, 
                "image": img, 
                "link": link,
            })
    except (Exception, BaseException, KeyboardInterrupt) as error: 
        root.after(0, lambda: show_error(error))
    else: 
        root.after(0, lambda: show_results(found))
    finally: 
        loader_text("Search")
        root.after(0, unblock_ui)
def unblock_ui(): 
    search.configure(state=NORMAL)
    goSearch.configure(state=NORMAL)
def show_error(error): 
    pass
def show_results(found): 
    pass
def trim(string: str = "String to trim", chars: int = 13): 
    """Trims a string. It avoids to overflow the label in which the text is. """
    if len(string) <= chars - 3: 
        return string # It fits, so no need to trim! 
    return string[0:chars-3] + "..." # -3 because len("...") is 3. 
img_cache = []
def preview_render(preview: str, target: Label): 
    """Downloads a JPEG preview onto RAM and shows it in the label. """
    for possible_img in img_cache: 
        if possible_img[-1] == preview: # We already have it! 
            root.after(0, lambda: set_image(possible_img[0], target, preview))
            return
    # Because we're here, the image isn't cached. 
    try : 
        req = requests.get(preview, timeout=10) # No more than 10 seconds per preview. 
        if req.status_code == 200: 
            img = req.content
            img = io.BytesIO(img)
            img = PIL.Image.open(img)
            img = img.resize((100, 100), PIL.Image.Resampling.LANCZOS)
            tk_img = PIL.ImageTk.PhotoImage(master=root, image=img)
            root.after(0, lambda: set_image(tk_img, target, preview))
        else: 
            raise Exception("The preview file was not found: %s. " % (req.status_code))
    except (BaseException, Exception, KeyboardInterrupt) as error: 
        print("Could not fetch preview. %s" % (error))
def set_image(image, target, url=None): 
    img_cache.append([image, url]) # The image and where we found it. 
    target.configure(image=image)
    root.update()
def show_widgets(): 
    """Adds widgets to the empty window. """
    global search
    global scroll_canvas
    global goSearch
    global search_text
    global scroll_canvas
    search = ttk.Entry(top, width=100)
    search.grid(row=0, column=0)
    search_text = StringVar(root, value="Search")
    goSearch = ttk.Button(top, textvariable=search_text, command=search_products)
    goSearch.grid(row=0, column=1)
    scroll_canvas = Canvas(center, highlightthickness=0)
    scroll_canvas.pack(expand=True, fill=BOTH)
    canvas_frame = Frame(scroll_canvas)
    scroll_canvas.create_window(0, 0, window=canvas_frame, anchor="nw", tags="inner_window")
    scroll_canvas.bind(
        "<Configure>", 
        lambda event: scroll_canvas.itemconfigure("inner_window", width=event.width)
    )
    canvas_frame.bind(
        "<Configure>",
        lambda event: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
    )
    # Scrollbars to scroll through the frame. 
    v_scrollbar = ttk.Scrollbar(center, orient="vertical", command=scroll_canvas.yview)
    scroll_canvas.configure(yscrollcommand=v_scrollbar.set)
    v_scrollbar.pack(side=RIGHT, fill=Y)
    scroll_canvas.pack(side=LEFT, expand=True, fill=BOTH)
def clear(): 
    """Clears the scrollable frame. Must be called from the main thread. """
    for elem in canvas_frame.winfo_children(): 
        elem.destroy()
    root.update()
root = Tk()
root.title("PriceScraper GUI")
root.minsize(600, 400)
top = Frame(root)
top.pack(fill=X)
center = Frame(root)
center.pack(expand=True, fill=BOTH)
bottom = Frame(root)
bottom.pack(fill=X)
show_widgets()
root.mainloop()