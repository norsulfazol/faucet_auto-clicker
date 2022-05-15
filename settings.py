import os

# from time import strftime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Browser & driver
BROWSER_NAME = 'Firefox'  # Chrome, Firefox, Ie, Edge, Opera, Safari, etc.
DRIVERS_DIR = os.path.join(BASE_DIR, 'drivers')
DRIVER_FILE = 'geckodriver'  # chromedriver, geckodriver, etc.

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

ON_UNAVAILABLE_ATTEMPTS = 5  # 0 - infinitely (not recommended)
ON_UNAVAILABLE_ATTEMPTS_TIMEOUT = 60 * 5  # in seconds
ON_UNAVAILABLE_ATTEMPTS_TIMEOUT_INCREASE = 2

CLOSE_COOKIE_WARNING_BANNER = True
CLOSE_NOTIFICATION_MODAL = True
CLOSE_AFTER_FREE_PLAY_MODAL = True  # after a free play, a modal window usually pops up

SOUND_FREE_PLAY = False
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
BONUSES = {'btc': 1000, 'wof': 5}
BONUSES_TIMEOUT_ELEM_WAIT = TIMEOUT_ELEM_WAIT / 2
