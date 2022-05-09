# Faucet auto-clicker.

Program for managing one of the oldest bitcoin faucets.

### Currently, he is able to:
* authenticate a user;
* play a free game;
* change some account settings;
* check and activate some bonuses;
* get some information from the account.

As an example, the program includes a basic scenario for the program.

## Installation:
The program requires a **Python 3.6+** interpreter with standard packages. Linux operating systems usually come with one
or two versions of Python already, and it's easy enough to make sure you have the version you need. In MS Windows
operating systems, Python will have to be installed independently.

### Python installation for MS Windows OS:
Download the Python installer for Windows from the
[official Python website](https://www.python.org/downloads/windows/ "Download page Python for MS Windows") and start the
installation by running the exe file (for example, _**python-3.6.8.exe**_ or _**python-3.6.8-amd64.exe**_). During the
installation process, confirm the installation of the **pip** package manager, standard packages, and also pay attention
to the correctness of adding Python paths to environment variables. It is recommended to install Python to the root of
the _**C**_ drive (you should get something like _**C:\Python36**_). A more detailed description of the installation
process for Python for Windows is easy to find on the Internet.

---
>**NOTE:** After installing Python, all subsequent commands will need to be run in the terminal.

>**NOTE:** If both versions 2 and 3 of Python are installed on the operating system, then the `python3` and `pip3`
> commands should be used instead of the `python` and `pip` commands, respectively.
---

### Checking installed Python version:
`python -V` or `python --version`

### Checking installed version of pip package manager:
`pip -V` or `pip --version`

### Upgrade pip package manager:
`pip install --upgrade pip`

### Program installation:
The program itself does not have a special installation method.
It is enough to take it from the repository and save it in a place convenient for you.
>**WARNING:** If the program is located in a folder whose name contains a space(s), then in the future the full path to
> the program will need to be enclosed in quotes.

---
>**NOTE:** After installing the program, all subsequent commands will need to be run in the terminal, being in the
> program folder.
---

### Installation additional Python packages required for the program to work:
It is good practice to install additional Python packages for a program in a separate virtual environment. A description
of the installation, activation and work with **virtualenv** is easy to find on the Internet. Pay attention to this in
the future. For now, let's install the packages in the global environment:  
`pip install -r requirements.txt`

### Viewing the list of installed additional Python packages in the current environment:
`pip freeze`

### Browser driver installation:
Before starting work, you must select which browser the program will work with. It is recommended to update the selected
browser to the latest possible version. Determine the version and bitness of the selected browser. Download the
appropriate browser driver (links to driver distributions for some browsers in the
_**faucet_auto-clicker/drivers/readme.txt**_ file). If you cannot find a driver that is the same version as your
browser, you can try using the next older version of the driver. Extract the driver from the archive (if it is in the
archive) and save it to the _**faucet_auto-clicker/drivers**_ folder.

## Program settings:
The program settings are located in the _**settings.py**_ file. For the most part, the settings are optimal and there is
no need to change them. Before running the program, you only need to set/change the following few settings:

    BROWSER_NAME = '<name of the selected browser (default is 'Firefox')>'
    DRIVER_FILE = '<file name (with extension, if any) of the selected browser driver (default is 'geckodriver')>'
    
    AUTH_ADDRESS = '<account email or BTC (withdrawal) address>'
    AUTH_PASSWORD = '<account password>'
    AUTH_TOTP_SECRET = '<secret key that is used to generate the Time-based One-Time Password,- only if 2FA is enabled on your account>'

>**ATTENTION:** It is safer to store account authentication data not in the _**settings.py**_ file, but in
> environment variables. To do this, the following environment variable names are proposed in the program
> (respectively):
> 
>     FBTC_ADDRESS <= AUTH_ADDRESS
>     FBTC_PASSWORD <= AUTH_PASSWORD
>     FBTC_TOTP_SECRET <= AUTH_TOTP_SECRET
> Descriptions of setting environment variables for various operating systems are available on the Internet. After
> saving account authentication data in environment variables, there is no need to save them in the corresponding
> variables of the _**settings.py**_ file.

### Custom settings file:
Instead of adjusting the main program settings file, you can create your own personal file in the program folder (for
example, with the name _**my_settings.py**_), into which it is enough to copy only the necessary settings from the
_**settings.py**_ file and set/change them.

#### Example (_faucet_auto-clicker/my_settings.py_):

    from settings import *

    BROWSER_NAME = 'Chrome'
    DRIVER_FILE = 'chromedriver.exe'
    ...
    FAUCET_LOG_TO_FILE = False
    ...
    DISABLE_LOTTERY = False
    ...

## Program launch:
Following are the possible options for running the program from the terminal. Command line directives enclosed in square
brackets (`[<directive>]`) are optional.

### Launching the program from any folder:
`[[<full path to python interpreter>/]python[.exe]] <full path to the program folder>/faucet_auto-clicker/main.py
[<custom settings file name>]`

If the first line of the file _**main.py**_ is a shebang-string with the path to the Python interpreter,
then the directive _**python**_ on the command line can be omitted. If the custom settings file name is not specified or
is erroneous, then the _**settings.py**_ file will be used.

### Launching the program from the program folder:
`python[.exe] -m main [<custom settings file name>]`
