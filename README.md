# PriceScraper
A smart tool to watch in real time (more or less) the current price
of **any** Amazon product. For now, you've to enter the Amazon product URL and the ceiling price. 
I plan to add a GUI to make our lives easier (see *TODOs* zone), which should be there shortly. 
## Setup
PriceScraper comes with an integrated GUI. For already compiled executables, see my [Releases page](https://github.com/LionelPB/PriceScraper/releases). 
To run it: Ensure you've Python 3 installed (and added to PATH). 
### Clone the repository: 
```bash
git clone https://github.com/LionelPB/PriceScraper
cd PriceScraper
```
### Install dependencies
Run this command in the *PriceScraper* folder. 
```bash
.\setup.cmd
```
This will ensure all dependencies are installed. 
### Run PriceScraper
To run the terminal version of PriceScraper: 
```bash
python3 main.py
```
If you want to run the GUI version: 
```bash
python3 gui.py
```
From the GUI, you'll be able to search Amazon products without having to copy and paste URLs in a terminal. 
## Compatibility
While I tried to ensure the scripts work with (almost) every web site, there can still be some that this tool
won't be able to extract prices from. If you suspect the webe site to have CAPTCHAs, disable the **HEADLESS** flag
to see the browser window. From then on, just complete the CAPTCHA to continue. 
## AgentMail: Obtain API key
+ To create an AgentMail account, go to [Agent Mail](https://www.agentmail.to/) and create your account. 
+ You'll then have to specify your inbox email address (not your real email address, your bot's email address). 
+ Once done, go to **[API keys](https://console.agentmail.to/dashboard/api-keys)** and click **Create API key**. 
+ In the dialog that will open, choose a name for your bot. **IMPORTANT**: In *Scope*, choose *No scope*, and make sure *Restrict permissions* is not checked. 
    - Once you create your API key, copy it and set the **AGENTMAIL_APIKEY** variable in *main.py* to the API key. *NOTE*: Once you close the dialog, you will not be able to see the API key again. 
## TODOs

- [x] Add GUI for simple use:
    - [ ] Runs `main.py` with environment variables defined by `gui.py` (the GUI)
    - [ ] Enables the user to set the `INTERVAL` variable for customized refresh rate.
- [ ] In `main.py`, try to use the `INTERVAL` environment variable instead of hardcoding  
    - [ ] This is relatively simple.
