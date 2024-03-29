import os

# from time import strftime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Browser & shared driver directory
BROWSER = 'firefox'  # firefox, chrome, edge, ie, opera, safari, etc.
DRIVERS_DIR = os.path.join(BASE_DIR, 'drivers')

# Mozilla Firefox
FIREFOX_BROWSER_FILE = 'firefox'  # empty or omitted value - BROWSER variable is used
FIREFOX_BROWSER_DIR = ''  # empty or omitted value - search for the browser file through the PATH env variable
FIREFOX_BROWSER_REG_KEY = ''  # for Windows platform only
# The user-agent string on the client side (that is, sent by your browser) can be obtained in the browser using
# JavaScript (navigator.userAgent property) or using a special web service (for example, https://2ip.ru/browser-info/ ).
FIREFOX_BROWSER_OPTIONS = {
    'capabilities': {},  # (dictionary) only for Firefox, Chrome, IE
    'preferences': {'general.useragent.override': 'Mozilla/5.0 (Linux; Android 8.1.0; Redmi 6A; rv:109.0) '
                                                  'Gecko/20100101 Firefox/109.0 Mobile Safari/537.36',
                    'browser.privatebrowsing.autostart': True},  # (dictionary) only for Firefox
    'experimentals': {},  # (dictionary) only for Chrome
    'arguments': ()}  # (list, tuple, set) only for Firefox, Chrome, IE

FIREFOX_DRIVER_FILE = 'geckodriver'  # empty or omitted value - BROWSER variable is used
FIREFOX_DRIVER_DIR = DRIVERS_DIR  # empty or omitted value - search for the driver file through the PATH env variable
FIREFOX_DRIVER_URL = 'https://github.com/mozilla/geckodriver/releases'

# Google Chrome (Chromium)
CHROME_BROWSER_FILE = 'google-chrome'  # here, examples: 'google-chrome-stable', 'google-chrome', 'chrome', ...
CHROME_BROWSER_DIR = ''  # here, examples: '/usr/bin', 'c:/Program Files/Google/Chrome/Application', ...
CHROME_BROWSER_REG_KEY = 'HKCU\\SOFTWARE\\Google\\Chrome\\BLBeacon'
CHROME_BROWSER_OPTIONS = {'experimentals': {'excludeSwitches': ['enable-logging', 'enable-automation'],
                                            'useAutomationExtension': False},
                          'arguments': ('--user-agent=Mozilla/5.0 (Linux; Android 8.1.0; Redmi 6A) '
                                        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36',
                                        '--no-default-browser-check',
                                        '--no-first-run',
                                        '--incognito',
                                        # '--headless',
                                        # '--no-sandbox',
                                        # '--disable-gpu',
                                        # '--disable-blink-features=AutomationControlled',
                                        'mobileEmulation')}

CHROME_DRIVER_FILE = 'chromedriver'
CHROME_DRIVER_DIR = DRIVERS_DIR
CHROME_DRIVER_URL = 'https://chromedriver.storage.googleapis.com'

# MS Edge
EDGE_BROWSER_FILE = 'edge'
EDGE_BROWSER_DIR = ''
EDGE_BROWSER_REG_KEY = ''

EDGE_DRIVER_FILE = 'msedgedriver'
EDGE_DRIVER_DIR = DRIVERS_DIR
EDGE_DRIVER_URL = 'https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/'

# Authentication
# On Linux add enviropment variables for current user only:
#   echo "export FBTC_ADDRESS=<address>" >> ~/.bashrc
#   echo "export FBTC_PASSWORD=<password>" >> ~/.bashrc
#   echo "export FBTC_TOTP_SECRET=<totp_secret>" >> ~/.bashrc
#   source ~/.bashrc
#   env | grep FBTC
# Or specify values as the second parameter of the os.getenv() method.
AUTH_ADDRESS = os.getenv('FBTC_ADDRESS', '')  # email or BTC (withdrawal) address
AUTH_PASSWORD = os.getenv('FBTC_PASSWORD', '')
AUTH_TOTP_SECRET = os.getenv('FBTC_TOTP_SECRET', '')  # if not using 2FA, the value should be empty

# Logging
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
LOGS_PREFIX = ''  # for example: f'{strftime("%y%m%d")}_'
LOGS_SUFFIX = ''  # for example: f'_{os.getpid()}'
FAUCET_LOG_LEVEL = 20  # 0|NOTSET - disable faucet logging, 10|DEBUG, 20|INFO, 30|WARNING, 40|ERROR, 50|CRITICAL
FAUCET_LOG_TO_FILE = True  # set to False to log to standard output
FAUCET_LOG_FILE_MODE = 'w'  # 'w' - overwrites an existing file, 'a' - adds to the end of the existing file
FAUCET_LOG_FILE = 'faucet.log'
DRIVER_LOG_FILE = 'driver.log'

# Scenario
TIMEOUT_PAGE_LOAD = 30
TIMEOUT_ELEM_WAIT = 10

QUICK_START = False

ON_UNAVAILABLE_ATTEMPTS = 5  # 0 - infinitely (not recommended)
ON_UNAVAILABLE_ATTEMPTS_TIMEOUT = 60 * 5  # in seconds
ON_UNAVAILABLE_ATTEMPTS_TIMEOUT_INCREASE = 2

CLOSE_COOKIE_WARNING_BANNER = True
CLOSE_NOTIFICATION_MODAL = True
CLOSE_AFTER_FREE_PLAY_MODAL = True  # after a free play, a modal window usually pops up

FREE_PLAY_SOUND = False
DISABLE_LOTTERY = True
DISABLE_INTEREST = False

CHECK_FOR_CAPTCHA = True  # set to False if captcha verification is disabled - this will remove unnecessary delays
CHECK_FOR_WINNING_WOF = False  # set to False if the WOF win check is not needed - this will remove unnecessary delays

FREE_PLAY_NUM = 0  # 0 - infinitely
FREE_PLAY_ATTEMPTS = 3  # 0 - infinitely (not recommended)
FREE_PLAY_AFTER_COUNTDOWN_DELAY = 5  # in seconds
FREE_PLAY_AFTER_COUNTDOWN_REFRESH = False  # after the countdown ends, the page should automatically refresh

# Bonuses in the dictionary must be arranged in the order of their activation.
# Each subsequent bonus will try to activate only if all previous bonuses are activated.
# If the bonus is not in the dictionary, then it will never be activated.
# If the dictionary is empty, then none of the bonuses will ever activate.
# BONUSES = {'btc': 50 | 100 | 500 | 1000, 'lt': 1 | 10 | 25 | 50 | 100, 'wof': 1 | 2 | 3 | 4 | 5}
BONUSES = {'btc': 500, 'wof': 5}
BONUSES_TIMEOUT_ELEM_WAIT = TIMEOUT_ELEM_WAIT / 2
