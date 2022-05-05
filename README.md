# Faucet auto-clicker.

Program for managing one of the oldest bitcoin faucets.

### At the moment, she can:
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
