@echo off
echo Installing required modules, this may take a while...
REM Install required modules. 
REM This script targets Python 3, which must be installed and in the system PATH variable.
python3 -m pip install -r requirements.txt
REM If you're getting errors about your computer requiring Python from the Microsoft Store, 
REM change "python3" to "python" in the command above.
REM Setup is done. Send a message to the user. 
echo Dependencies successfully installed. You can now run the main script with "python3 main.py".