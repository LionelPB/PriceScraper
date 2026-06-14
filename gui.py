"""
Here's the GUI version of "main.py". 
It lets you search directly on Amazon to avoid having to get the right product URL. 
"""
import glob
from statistics import variance
from tkinter import *
from tkinter import ttk # Updated widgets. 
from flask.cli import F
from playwright.sync_api import sync_playwright  # Manipulate the browser to search on Amazon for the user. 
from bs4 import BeautifulSoup
import threading
import re # To detect JavaScript URLs
from urllib.parse import urljoin # To correctly join URLs. 

import io # To store previews in RAM
import requests # To get previews 
import PIL.Image, PIL.ImageTk # To show previews (default format in Amazon is JPEG). 
import tkinter.font as tk_font # Adjust title trimming when window resizes. 

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
    set_status("Preparing to search...")
    url = SEARCH_URL + text
    found = [] # What we got back. 

    try: 
        with sync_playwright() as p: 
            browser = p.chromium.launch(headless=HEADLESS, channel="chrome")
            loader_text("Opening tab...")
            set_status("This may take a few seconds...")
            tab = browser.new_page()
            loader_text("Searching...")
            set_status("This may take a few seconds...")
            tab.goto(url, wait_until="domcontentloaded", timeout=40000)
            try: 
                tab.wait_for_selector("div[data-component-type='s-search-result']", timeout=5000)
            except: 
                pass
            html = tab.content()
            browser.close() # We don't need it anymore. 
        # Get out of here to close the browser. 
        loader_text("Extracting data...")
        set_status("We're almost done...")
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
            # Try to extract ASIN for JavaScript URLs. 
            anchor = item.select_one('[data-cy="title-recipe"] a[href]')
            href = anchor['href'] if anchor and anchor.has_attr('href') else None
            asin = item.get('data-asin')
            if not asin and href:
                m = re.search(r'/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})', href)
                if m:
                    asin = m.group(1) or m.group(2)
            if asin:
                link = urljoin(BASE_URL, f'/dp/{asin}')
            elif href and not href.strip().lower().startswith('javascript:'):
                link = urljoin(BASE_URL, href)
            else:
                link = None
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
    set_status("There was an error while fetching result: \n%s" % (error))
colors = ["#000000", "#444444", "#333333", "#222222", "#ffffff", "#222222", "#333333", "#444444"]
bright = colors[0:4]
idx = -1
hover_color = "#00542d"
def hover(frame): 
    try: 
        frame.configure(bg=hover_color)
    except: 
        pass
    for elem in frame.winfo_children(): 
        try: 
            elem.configure(bg=hover_color, cursor="hand2")
        except: 
            pass
        try: 
            elem.configure(fg="#ffffff")
        except: 
            pass
        hover(elem)
    root.after(0, root.update) # If we were ever called from a thread. 
def leave(frame, orig=None): 
    if orig == None: 
        color, text_color = frame.original_color
    else: 
        color, text_color = orig
    try: 
        frame.configure(bg=color)
    except: 
        pass
    for elem in frame.winfo_children(): 
        try: 
            elem.configure(bg=color, cursor="")
        except: 
            pass
        try: 
            elem.configure(fg=text_color)
        except: 
            pass
        leave(elem, (color, text_color)) # The children might not have ".original_color". 
    root.after(0, root.update) # If we were ever called from a thread. 
def open_page(frame): 
    result = frame.result
    for elem in container.winfo_children(): 
        elem.destroy()
    set_status("Please wait...")
    contain = Frame(container)
    contain.pack(expand=True, fill=BOTH)
    Label(contain, text="Track this product", font=("Segoe UI", 16), anchor="w").pack(fill=X)
    buttons = Frame(contain)
    buttons.pack(fill=X)
    ttk.Button(buttons, text="< Back to search results", command=lambda: show_results(last_results)).pack(side="left")
    track = ttk.Button(buttons, text="Add this product to the tracklist")
    track.configure(command=lambda r=result: track_untrack(r, track))
    track.pack(side="left")
    ttk.Button(buttons, text="Show my Tracklist", command=open_tracklist).pack(side="left")
    if result in tracklist: 
        track.configure(text="Remove from Tracklist")
    else:
        track.configure(text="Add this product to the Tracklist")
    set_status("What do you want to do with this product? ")
def track_untrack(result, btn): 
    if result in tracklist: 
        tracklist.remove(result)
        btn.configure(text="Add this product to the Tracklist")
    else:
        tracklist.append(result)
        btn.configure(text="Added! Remove from Tracklist")
    update_tracklist()
tracklist = [] # List of products user wants to track. 
last_results = []
def show_results(found, protected=None, callback=None): 
    global color
    global last_results
    global idx
    if protected == None: # Normal search. 
        last_results = found
    set_status("Search results: ")
    for elem in container.winfo_children(): 
        if elem != protected: 
            elem.destroy()
    for result in found: 
        idx = idx + 1
        try: 
            color = colors[idx]
        except: 
            idx = -1
            color = colors[idx]
        text_color = "#ffffff" if color in bright else "#000000"
        frame = Frame(container, bg=color)
        frame.bind("<Enter>", lambda evt, frm=frame: hover(frm))
        frame.bind("<Leave>", lambda evt, frm=frame: leave(frm))
        frame.bind("<Button-1>", lambda evt, frm=frame: open_page(frm))
        frame.result = result
        frame.original_color = (color, text_color)
        icon = Frame(frame, bg=color)
        text = Frame(frame, bg=color)
        icon.pack(side="left")
        text.pack(side="left", fill=X, expand=True)
        full_title = result["title"]
        title = trim(full_title, 60)
        title_label = Label(text, text=title, font=("Calibri", 16), bg=color, fg=text_color, anchor="w")
        title_label.pack(fill=X)
        title_label.full_title = full_title
        if not str(result["price"]).lower().startswith("not"):
            price_label = Label(text, text="$" + str(result["price"]), bg=color, fg=text_color, anchor="w", font=("Segoe UI", 11)) # ("Segoe UI", 9) is the default Windows font size. 
            price_label.pack(fill=X)
        else:
            price_label = Label(text, text="Price: " + str(result["price"]), bg=color, fg="#ff0000", anchor="w", font=("Segoe UI", 11)) # ("Segoe UI", 9) is the default Windows font size. 
            price_label.pack(fill=X)
        icon_label = Label(icon, bg=color, fg=text_color)
        icon_label.pack()
        preview_thread = threading.Thread(target=preview_render, args=(result["image"], icon_label), daemon=True)
        preview_thread.start()
        frame.pack(fill=X, pady=1)
        icon.bind("<Button-1>", lambda evt, frm=frame: open_page(frm))
        text.bind("<Button-1>", lambda evt, frm=frame: open_page(frm))
        title_label.bind("<Button-1>", lambda evt, frm=frame: open_page(frm))
        icon_label.bind("<Button-1>", lambda evt, frm=frame: open_page(frm))
        price_label.bind("<Button-1>", lambda evt, frm=frame: open_page(frm))
        if callback != None: 
            callback_frame = Frame(text)
            callback_frame.pack(fill=X)
            callback(callback_frame, result)
    root.after(440, update_trim)
def update_trim(evt=None): 
    """Adjusts trimming based on widget size. """
    f = tk_font.Font(family="Calibri", size=16)
    for frame in container.winfo_children():
        children = frame.winfo_children()
        if len(children) < 2:
            continue
        text_frame = children[1]
        labels = text_frame.winfo_children()
        if not labels:
            continue
        title_label = labels[0]
        full_title = getattr(title_label, "full_title", title_label.cget("text"))
        free_pixels = text_frame.winfo_width()
        if free_pixels <= 10: 
            continue
        avg_char_px = max(6, f.measure("n"))
        max_chars = max(8, int(free_pixels / avg_char_px))
        title_label.configure(text=trim(full_title, max_chars))
def trim(string: str = "String to trim", chars: int = 13): 
    """Trims a string. It avoids to overflow the label in which the text is. 
       If the string to trim's length is less that chars - 3, the string is returned as is. 
    """
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
            img.thumbnail((100, 100), PIL.Image.Resampling.LANCZOS)
            tk_img = PIL.ImageTk.PhotoImage(master=root, image=img)
            root.after(0, lambda: set_image(tk_img, target, preview))
        else: 
            raise Exception("The preview file was not found: %s. " % (req.status_code))
    except (BaseException, Exception, KeyboardInterrupt) as error: 
        print("Could not fetch preview. %s" % (error))
def set_image(image, target, url=None): 
    img_cache.append([image, url]) # The image and where we found it. 
    try: 
        target.configure(image=image)
    except: 
        pass # Last results may still be downloading, and user has clicked on a product, so everything got destroyed. 
    root.update()
def update_tracklist(): 
    elems = len(tracklist)
    add = "s"
    if elems == 1: 
        add = ""
    tracklist_counter.set("%s element%s in the Tracklist" % (elems, add))
def show_widgets(): 
    """Adds widgets to the empty window. """
    global search
    global scroll_canvas
    global goSearch
    global container
    global search_text
    global canvas_frame
    global text_status
    global tracklist_frame
    global tracklist_label
    global tracklist_counter
    global text_statusLabel
    search = ttk.Entry(top, width=100)
    search.grid(row=0, column=0, sticky="ew")
    search_text = StringVar(root, value="Search")
    goSearch = ttk.Button(top, textvariable=search_text, command=search_products)
    goSearch.grid(row=0, column=1, sticky="e")
    tracklist_frame = Frame(top)
    tracklist_counter = StringVar(root, value="Please wait...")
    tracklist_label = Label(tracklist_frame, cursor="hand2", bg="#ffffff", textvariable=tracklist_counter, font=("Segoe UI", 11), anchor="e")
    tracklist_label.pack(expand=True, fill=BOTH)
    tracklist_label.bind("<Enter>", lambda evt: (tracklist_label.configure(bg="#000000", fg="#ffffff"), tracklist_counter.set("               See my Tracklist")))
    tracklist_label.bind("<Leave>", lambda evt: (tracklist_label.configure(bg="#ffffff", fg="#000000"), update_tracklist()))
    tracklist_label.bind("<Button-1>", lambda evt: open_tracklist())
    tracklist_frame.grid(row=0, column=2, sticky="e")
    top.grid_columnconfigure(0, weight=1)
    scroll_canvas = Canvas(center, highlightthickness=0)
    scroll_canvas.pack(expand=True, fill=BOTH)
    canvas_frame = Frame(scroll_canvas)
    scroll_canvas.create_window(0, 0, window=canvas_frame, anchor="nw", tags="inner_window")
    scroll_canvas.bind(
        "<Configure>", 
        lambda evt: scroll_canvas.itemconfigure("inner_window", width=evt.width)
    )
    canvas_frame.bind(
        "<Configure>",
        lambda evt: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
    )
    canvas_frame.bind("<Configure>", update_trim, add="+")
    # Scrollbars to scroll through the frame. 
    v_scrollbar = ttk.Scrollbar(center, orient="vertical", command=scroll_canvas.yview)
    scroll_canvas.configure(yscrollcommand=v_scrollbar.set)
    v_scrollbar.pack(side=RIGHT, fill=Y)
    scroll_canvas.pack(side=LEFT, expand=True, fill=BOTH)
    text_status = StringVar(root, value="Search for any product with the search bar above. ")
    text_statusLabel = Label(canvas_frame, textvariable=text_status, font=("Calibri", 18))
    text_statusLabel.pack(expand=True, fill=BOTH)
    container = Frame(canvas_frame)
    container.pack(expand=True, fill=BOTH)
    update_tracklist()
def set_status(status): 
    text_status.set(status)
def clear(): 
    """Clears the scrollable frame. Must be called from the main thread. """
    for elem in canvas_frame.winfo_children(): 
        elem.destroy()
    root.update()
def open_tracklist(): 
    """Shows the current tracking items. """
    for elem in container.winfo_children(): 
        elem.destroy()
    cont = Frame(container)
    Label(cont, text="The Tracklist tracks the prices of the added products and notifies you when their price gets below a ceiling. ").pack()
    buttons = Frame(cont)
    buttons.pack(fill=X)
    ttk.Button(buttons, text="< Show results from my last search", command=lambda: show_results(last_results)).pack(side="left")
    ttk.Button(buttons, text="Logged prices >").pack(side="left")
    te = ttk.Button(buttons, text="Track everything")
    te.pack(side="left")
    if tracklist == current: # Everything being tracked. 
        te.configure(text="Stop tracking everything")
    else: 
        te.configure(text="Start tracking everything")
    te.configure(command=lambda: track_all(te))
    cont.pack(fill=X)
    if tracklist == []: # Empty!
        set_status("Your Tracklist is empty! \n Find for a product, click on it, \n add it to the Tracklist and come back here. ")
    else: 
        show_results(tracklist, cont, choose_times)
        set_status("Contents of my Tracklist")
def track_all(button): 
    pass
def choose_times(frame, result): 
    Label(frame, text="Choose verification interval for this product: ", anchor="w").pack(fill=X)
    frm = Frame(frame)
    frm.pack(fill=X)
    result["interval"] = IntVar(root, value=800)
    Label(frm, text="Interval in seconds to wait between price checks: ").grid(row=0, column=0)
    ttk.Spinbox(frm, from_=20, to=1000000, increment=5, textvariable=result["interval"]).grid(row=0, column=1) # Safe value: 20 seconds. Otherwise, it would be too much work for the computer to launch a browser every 20 seconds. 
    b = ttk.Button(frame, text="Start tracking for this item")
    b.configure(command=lambda: start_track(b, result))
    b.pack(anchor="w")
    if result in current: 
        b.configure(text="Stop tracking")
    else: 
        b.configure(text="Start tracking")

def start_track(btn, result): 
    if result in current: 
        current.remove(result)
        btn.configure(text="This item is no longer tracked. Track it again")
    else: 
        current.append(result)
        btn.configure(text="Currently tracked. Stop tracking")
settings = {

}
current = []
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