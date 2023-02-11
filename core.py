__author__ = 'norsulfazol'
__version__ = '1.3.0'

import os
import sys
import shutil
import urllib3
import tempfile
import ec as EC
from typing import Union
from logging import getLogger
from itertools import product
from collections import namedtuple
from decimal import Decimal, InvalidOperation
from progress import bar  # the progress bar is displayed only in the terminal (not in the python console)
from pyotp import TOTP
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException, StaleElementReferenceException

logger = getLogger(__name__)


def _validate_argument(arg_value, arg_string: str, arg_obj: Union[type, tuple], allowed_values: tuple = tuple()):
    """
    Validates an argument.

    :param arg_value: any type
    :param arg_string: str
    :param arg_obj: type or tuple of types
    :param allowed_values: tuple
    """

    def get_err_msg(string: str, obj: Union[type, tuple]) -> str:
        return f'Argument "{string}" must be of type ' \
               f""""{'" or "'.join(o.__name__ for o in obj) if isinstance(obj, tuple) else obj.__name__}"."""

    if not isinstance(arg_string, str):
        raise ValueError(get_err_msg('arg_string', str))
    if not isinstance(arg_obj, (type, tuple)):
        raise ValueError(get_err_msg('arg_obj', (type, tuple)))
    if isinstance(arg_obj, tuple):
        for i, v in enumerate(arg_obj):
            if not isinstance(v, type):
                raise ValueError(get_err_msg(f'arg_obj[{i}]', type))
    if not isinstance(allowed_values, tuple):
        raise ValueError(get_err_msg('allowed_values', tuple))
    if not isinstance(arg_value, arg_obj):
        raise ValueError(get_err_msg(arg_string, arg_obj))
    if allowed_values and arg_value not in allowed_values:
        raise ValueError(f'Argument "{arg_string}" must have one of the following values: '
                         f'{", ".join(map(str, allowed_values))}.')


def str2num(string: str, obj: type = int) -> Union[int, Decimal, float]:
    """
    Returns an integer, Decimal or float number converted from a string.
    Returns obj() => 0, if the string is empty or the conversion failed.

    :param string: str
    :param obj: type (int (default), Decimal or float)
    :return: int, Decimal or float
    """
    _validate_argument(string, 'string', str)
    _validate_argument(obj, 'obj', type, (int, Decimal, float))
    if string.strip():
        try:
            return obj(string)
        except (ValueError, InvalidOperation):
            logger.error('String "%s" is not suitable for conversion to %s.', string, obj.__name__)
    return obj()


def download_file(url: str, target_dir: str = '', target_name: str = '', message: str = '', chunk_size: int = 2048,
                  method: int = 0, progress_bar: type = bar.IncrementalBar) -> str:
    """
    Downloads a file at the given URL and returns the path to the downloaded file.

    :param url: str
    :param target_dir: str
    :param target_name: str
    :param message: str
    :param chunk_size: int (0 - length = COPY_BUFSIZE = 1024 * 1024 if _WINDOWS else 64 * 1024)
    :param method: int (0 (default) - shutil.copyfileobj, 1 - response.stream)
    :param progress_bar: type (bar.Bar, bar.IncrementalBar (default), bar.ChargingBar, etc.)
    :return: str
    """
    _validate_argument(url, 'url', str)
    _validate_argument(target_dir, 'target_dir', str)
    _validate_argument(target_name, 'target_name', str)
    _validate_argument(message, 'message', str)
    _validate_argument(chunk_size, 'chunk_size', int)
    _validate_argument(method, 'method', int, (0, 1))
    _validate_argument(progress_bar, 'progress_bar', type)
    log_msg = f'{message if message else "Downloading file"} by URL '
    if not url:
        logger.error('%sfailed. URL is empty.', log_msg)
        return ''
    with urllib3.PoolManager().request('GET', url, preload_content=False) as response:
        if response.status != 200:
            logger.error('%s"%s" failed. Response status - %s.', log_msg, url, response.status)
            return ''
        target_size = int(response.getheader('content-length'))
        with open(os.path.join(target_dir if os.path.isdir(target_dir) else tempfile.gettempdir(),
                               target_name if target_name else url.split('/')[-1]), 'wb') as target:
            if not message:
                var1 = 50  # string max length
                var2 = var1 // 2 - 2  # string part length
                print(f'{log_msg}"{url.replace(url[var2:-var2], "....") if len(url) > var1 else url}"')
                message = 'to PATH "{}"'.format(
                    target.name.replace(target.name[var2:-var2], "....") if len(target.name) > var1 else target.name)
            if method:
                var1 = shutil.get_terminal_size().columns - 15 - len(message) - progress_bar.width - len(
                    getattr(progress_bar, 'bar_prefix', 0)) - len(getattr(progress_bar, 'bar_suffix', 0))
                progress_bar.width += var1 if var1 < 0 else 0
                progress_bar.width = 1 if progress_bar.width < 1 else progress_bar.width
                var1, var2 = divmod(target_size, chunk_size)
                with progress_bar(message, max=var1 + bool(var2), suffix='%(percent)d%% [%(elapsed_td)s]') as pb:
                    for chunk in response.stream(chunk_size):
                        target.write(chunk)
                        pb.next()
            else:
                print(f'{message} ...', end='\r')
                shutil.copyfileobj(response, target, length=chunk_size)
                print(f'{message} - done.')
        if method:
            response.release_conn()
    if not os.path.isfile(target.name):
        logger.error('%s"%s" failed. Target file "%s" not found or is not a file.', log_msg, url, target.name)
        return ''
    if os.path.getsize(target.name) != target_size:
        logger.error('%s"%s" failed. Target file "%s" is not the correct size.', log_msg, url, target.name)
        try:
            os.remove(target.name)
        except OSError:
            logger.warning('Removing the corrupted file "%s" failed.', target.name)
        return ''
    logger.info('%s"%s" successful.', log_msg, url)
    return target.name


def unpack_archive(arch_path: str, target_dir: str = '', arch_format: str = '', is_remove: bool = True) -> bool:
    """
    Unpacks the archive to the specified directory.

    :param arch_path: str
    :param target_dir: str
    :param arch_format: str (one of 'zip', 'tar', 'gztar', 'bztar', or 'xztar')
    :param is_remove: bool
    :return: bool
    """
    _validate_argument(arch_path, 'arch_path', str)
    _validate_argument(target_dir, 'target_dir', str)
    _validate_argument(arch_format, 'arch_format', str)
    _validate_argument(is_remove, 'is_remove', bool)
    log_msg = 'Unpacking the archive '
    if not arch_path:
        logger.error('%sfailed. Archive path is empty.', log_msg)
        return False
    try:
        shutil.unpack_archive(arch_path, target_dir if target_dir else None, arch_format if arch_format else None)
        logger.info('%s"%s" successful.', log_msg, arch_path)
        if is_remove:
            try:
                os.remove(arch_path)
            except OSError:
                logger.warning('Removing the unpacked archive "%s" failed.', arch_path)
        return True
    except shutil.ReadError:
        logger.error('%s"%s" failed. Archive not found.', log_msg, arch_path)
    except ValueError:
        logger.error('%s"%s" failed. Unregistered archive format.', log_msg, arch_path)
    return False


class BrowserExecFileOrLink:
    __version_info = namedtuple('version_info', 'major minor release build')

    def __new__(cls, name: str, **kwds):
        """
        Creates and returns an instance of the current class only if a filename is passed.

        :param name: str
        ...
        """
        instance = super().__new__(cls)
        _validate_argument(name, 'name', str)
        return instance if name else None

    def __init__(self, name: str, **kwds):
        """
        Initializes an instance of the current class.

        ...
        :param kwds:
            directory: str
            reg_key: str
        """
        self.__name = f'{name}{(".exe", "")[name.endswith(".exe")]}' if sys.platform.startswith(
            'win32') else name.rstrip('ex')[:-1] if name.endswith('.exe') else name
        # since Python 3.9 (sys.version_info.minor > 8): name.removesuffix('.exe')
        self.directory = kwds.get('directory', '')
        self.reg_key = kwds.get('reg_key', '')
        _validate_argument(self.reg_key, 'reg_key', str)
        self._ver_idx = -1

    def __str__(self):
        return f'{self.__class__.__name__.replace("ExecFileOrLink", "")} executable file (link): ' \
               f'{self.path} (v.{self.version})'

    @property
    def name(self) -> str:
        """
        Returns the name. Read-only property.
        """
        return self.__name

    @property
    def directory(self) -> str:
        """
        Returns the directory where the file is located, or an empty string if the file is not found in any directory,
        including directories in the PATH environment variable.
        """
        for p in [self.__directory] + os.getenv('PATH', '').split((':', ';')[sys.platform.startswith('win32')]):
            if p and os.path.isfile(os.path.join(p, self.name)):
                return p
        return ''

    @directory.setter
    def directory(self, value: str):
        """
        Sets the file location directory only if it is valid, otherwise sets the empty string.
        """
        _validate_argument(value, 'value', str)
        value = os.path.abspath(os.path.normcase(value))
        self.__directory = value if os.path.isdir(value) and os.path.isfile(os.path.join(value, self.name)) else ''

    @property
    def path(self) -> str:
        """
        Returns the path to the file (directory + filename) if a file exists at this path, otherwise only the filename.
        Read-only property.
        """
        return os.path.join(self.directory, self.name)

    @property
    def version(self) -> str:
        """
        Returns the version as a string. Read-only property.
        """
        p = self.path
        if ' ' in p:
            p = ('"', '')[p.startswith('"')] + p + ('"', '')[p.endswith('"')]
        for condition, cmd_line in ((p, f'{p} --version'),
                                    (sys.platform.startswith('win32') and self.reg_key,
                                     f'reg query "{self.reg_key}" /v version')):
            if condition:
                with os.popen(cmd_line) as f:
                    try:
                        return f.read().strip().split()[self._ver_idx].replace(' ', '').lstrip('v.')
                    except IndexError:
                        pass
        return ''

    @property
    def version_info(self) -> namedtuple:
        """
        Returns the version as a named tuple of integer values. Read-only property.
        """
        length = len(self.__version_info._fields)
        ver = [int(v) if v.isdigit() else 0 for v in self.version.split('.')[:length]]
        return self.__version_info(*(ver + [0] * (length - len(ver))))

    def is_exists(self) -> bool:
        """
        Checks for the existence of a file at the specified path.
        """
        return os.path.isfile(self.path)


class DriverExecFileOrLink(BrowserExecFileOrLink):
    __VALID_PERMS = tuple(f'{owner}{group}{other}' for owner, group, other in product('04567', repeat=3))
    _upd_log_msg = 'Updating the driver '

    def __init__(self, name: str, **kwds):
        """
        Initializes an instance of the current class.
        """
        super().__init__(name, **kwds)
        self.directory = kwds.get('directory', '')
        self._ver_idx = 1

    @property
    def directory(self) -> str:
        """
        Returns the directory where the file should be located, or an empty string if such a directory is not set or
        does not exist and the file is not found in any of the directories in the PATH environment variable.
        """
        if not self.__directory:
            for p in os.getenv('PATH', '').split((':', ';')[sys.platform.startswith('win32')]):
                if p and os.path.isfile(os.path.join(p, self.name)):
                    return p
        return self.__directory if os.path.isdir(self.__directory) else ''

    @directory.setter
    def directory(self, value: str):
        """
        Creates (if it doesn't exist) and sets the file's location directory.
        """
        _validate_argument(value, 'value', str)
        value = os.path.abspath(os.path.normcase(value))
        if value and not os.path.exists(value):
            os.mkdir(value)
        self.__directory = value if os.path.isdir(value) else ''

    def perms(self, value: str = '') -> str:
        """
        Attempts to set and/or returns file permissions.

        :param value: str
        :return: str
        """
        if not self.is_exists():
            return ''
        if value:
            _validate_argument(value, 'value', str, self.__VALID_PERMS)
            try:
                os.chmod(self.path, int(f'0o{value}', 8))
            except PermissionError:
                logger.error('Setting file permissions failed. The current user has insufficient rights.')
        return oct(os.stat(self.path).st_mode)[-3:]

    def update(self, url: str) -> bool:
        """
        Updates the driver, if needed.
        Returns True if the driver was successfully updated or does not need to be updated, otherwise returns False.

        :param url: str
        :return: bool
        """
        _validate_argument(url, 'url', str)
        if not url:
            logger.error('%sfailed. URL is empty.', self._upd_log_msg)
            return False
        return True


class FirefoxDriverExecFileOrLink(DriverExecFileOrLink):
    def update(self, url: str, **kwds) -> bool:
        if not super().update(url):
            return False
        response = urllib3.PoolManager().request('GET', f'{url.rstrip("/")}/latest')
        if response.status != 200:
            logger.error('%sfailed. Response status - %s.', self._upd_log_msg, response.status)
            return False
        ver = response.geturl().rstrip('/').split('/')[-1].lstrip('v.')
        if ver <= self.version:
            logger.info('%snot needed.', self._upd_log_msg)
            return True
        if not unpack_archive(
                download_file('{}/{}-v{}-{}{}.{}'.format(response.geturl().replace('/tag/', '/download/'), self.name,
                                                         ver, ('', 'linux')[sys.platform.startswith('linux')] or
                                                              ('', 'win')[sys.platform.startswith('win32')] or
                                                              ('', 'macos')[sys.platform.startswith('darwin')],
                                                         (('32', '64')[sys.maxsize == 2 ** 63 - 1], '')[
                                                             sys.platform.startswith('darwin')],
                                                         ('tar.gz', 'zip')[sys.platform.startswith('win32')]),
                              target_dir=self.directory, message='Downloading driver', method=1),
                target_dir=self.directory):
            logger.error('%sfailed.', self._upd_log_msg)
            return False
        if self.perms('755') < '755':
            logger.error('%sfailed.', self._upd_log_msg)
            return False
        logger.info('%ssuccessful.', self._upd_log_msg)
        return True


class ChromeDriverExecFileOrLink(DriverExecFileOrLink):
    def update(self, url: str, **kwds) -> bool:
        """
        :param url: str
        :param kwds:
            browser_version_info: namedtuple
        ...
        """
        if not super().update(url):
            return False
        ver = ''
        if kwds.get('browser_version_info'):
            _validate_argument(kwds['browser_version_info'], 'browser_version_info', tuple)
            ver = '.'.join(map(str, kwds['browser_version_info'][:-1]))
        response = urllib3.PoolManager().request('GET', f'{url.rstrip("/")}/LATEST_RELEASE{("", "_")[bool(ver)]}{ver}')
        if response.status != 200:
            logger.error('%sfailed. Response status - %s.', self._upd_log_msg, response.status)
            return False
        ver = response.data.decode('utf-8').lstrip('v.')
        if ver == self.version:
            logger.info('%snot needed.', self._upd_log_msg)
            return True
        if not unpack_archive(
                download_file('{}/{}/{}_{}.zip'.format(url.rstrip('/'), ver, self.name,
                                                       ('', 'linux64')[sys.platform.startswith('linux')] or
                                                       ('', 'win32')[sys.platform.startswith('win32')] or
                                                       ('', 'mac64')[sys.platform.startswith('darwin')]),
                              target_dir=self.directory, message='Downloading driver', method=1),
                target_dir=self.directory):
            logger.error('%sfailed.', self._upd_log_msg)
            return False
        try:
            os.remove(os.path.join(self.directory, f'LICENSE.{self.name}'))
        finally:
            pass
        if self.perms('755') < '755':
            logger.error('%sfailed.', self._upd_log_msg)
            return False
        logger.info('%ssuccessful.', self._upd_log_msg)
        return True


class FreeBitcoinFaucet:
    # For reference:
    #
    # innerHTML - property that allows you to get the HTML or XML content of an element as a string and modify it.
    # In other words, the innerHTML property sets or gets the HTML or XML markup of the child elements (that is, the
    # elements between the start and end tags).
    #
    # textContent - property that allows you to set or get the text content of an element and its children.
    # This method consumes much less resources than innerHTML because the text is parsed as text, not HTML.
    # In addition, it protects against XSS attacks.

    URL = 'https://freebitco.in'
    __VALID_LOG_LEVELS = tuple(range(0, 60, 10))
    __VALID_BONUS_KEYS = ('btc', 'lt', 'wof')

    def __new__(cls, **kwds):
        """
        Tries to create an instance of the webdriver class.
        On success, creates and returns an instance of the current class. Otherwise returns None.

        :param kwds:
            browser_name: str (firefox, chrome, edge, ie, opera, safari, etc.)
            driver_exec_path: str (None - search for the driver in the directories specified in the PATH environment
                                   variable)
            driver_log_path: str (None - logging will be done in the current directory)
            ...
        """
        instance = super().__new__(cls)
        browser_name = kwds.get('browser_name', 'firefox')
        _validate_argument(browser_name, 'browser_name', str)
        driver_type = getattr(webdriver, browser_name.capitalize(), webdriver.Firefox)
        driver_kwds = {}
        if kwds.get('driver_exec_path'):
            _validate_argument(kwds['driver_exec_path'], 'driver_exec_path', str)
            driver_kwds['executable_path'] = kwds['driver_exec_path']
        if kwds.get('driver_log_path'):
            _validate_argument(kwds['driver_log_path'], 'driver_log_path', str)
            driver_kwds['service_log_path'] = kwds['driver_log_path']
        driver_kwds['options'] = getattr(webdriver, f'{browser_name.capitalize()}Options', None)
        driver_kwds['options'] = driver_kwds['options']() if driver_kwds['options'] else None
        if driver_kwds['options'] and kwds.get('driver_options'):
            _validate_argument(kwds['driver_options'], 'driver_options', dict)
            for option, method in (('capabilities', 'set_capability'),
                                   ('preferences', 'set_preference'),
                                   ('experimentals', 'add_experimental_option')):
                if kwds['driver_options'].get(option) and hasattr(driver_kwds['options'], method):
                    _validate_argument(kwds['driver_options'][option], f'driver_options_{option}', dict)
                    for name, value in kwds['driver_options'][option].items():
                        getattr(driver_kwds['options'], method)(name, value)
            if kwds['driver_options'].get('arguments') and hasattr(driver_kwds['options'], 'add_argument'):
                _validate_argument(kwds['driver_options']['arguments'], 'driver_options_arguments', (list, tuple, set))
                for option in kwds['driver_options']['arguments']:
                    driver_kwds['options'].add_argument(option)
        log_msg = 'Create faucet object '
        try:
            instance._driver = driver_type(**driver_kwds)
            logger.info('%ssuccessful.', log_msg)
            return instance
        except WebDriverException as err:
            logger.error(err.msg)
            logger.critical('%sfailed.', log_msg)
            return None

    def __init__(self, **kwds):
        """
        Initializes an instance of the current class.

        :param kwds:
            ...
            timeout_page_load: int or float - time to wait (in seconds) for a full page load before an exception
                                              TimeoutException is raised
            timeout_elem_wait: int or float - time to wait (in seconds) for an element(s) to appear in the DOM and/or
                                              (in)visibility before an exception TimeoutException is raised
            check_for_captcha: bool - captcha check status
            open: bool - open or not site
            open_url: str
            sign_in: bool - sign-in or not (sign-in is only possible if the site is open)
            sign_in_address: str
            sign_in_password: str
            sign_in_totp_secret: str
        """
        # WebDriver will wait until the page has fully loaded (that is, the “onload” event has fired) before returning
        # control to your script. Be aware that if your page uses a lot of AJAX on load then WebDriver may not know when
        # it has completely loaded.
        if kwds.get('timeout_page_load'):
            self._driver.set_page_load_timeout(kwds['timeout_page_load'])
        self.__timeout_page_load = kwds.get('timeout_page_load',
                                            self._driver.capabilities['timeouts'].get('pageLoad', 60))
        _validate_argument(self.__timeout_page_load, 'timeout_page_load', (int, float))
        self.__timeout_elem_wait = kwds.get('timeout_elem_wait', 10)
        _validate_argument(self.__timeout_elem_wait, 'timeout_elem_wait', (int, float))
        self.__check_for_captcha = bool(kwds.get('check_for_captcha', True))
        self.__password = ''
        self.__totp_secret = ''
        if kwds.get('open'):
            if self.open(kwds.get('open_url', '')):
                if kwds.get('sign_in'):
                    self.sign_in(kwds.get('sign_in_address', ''),
                                 kwds.get('sign_in_password', ''),
                                 kwds.get('sign_in_totp_secret', ''))

    def __str__(self):
        return self.__class__.__name__.replace('inFaucet', '.in')

    def _get_elements(self, **kwds) -> list:
        """
        Returns existing and/or visible DOM elements.
        Returns [True], if the condition is met but no element could be retrieved.

        :param kwds:
            wait_until: bool
            parent: driver or element
            timeout: int or float - timeout (in seconds) before the element appears in DOM and/or the element is visible
            ec: EC - expected condition
            locator: By (ID (default), CLASS_NAME, CSS_SELECTOR, LINK_TEXT, PARTIAL_LINK_TEXT, NAME, TAG_NAME, XPATH)
            locator_value: str
            attr_or_prop: str - attribute or property or css property
            value: str - title/text or attribute/property/css property value
            log_level: int (0, 10, 20, 30, 40 (default), 50)
        :return: list
        """
        timeout = kwds.get('timeout', self.__timeout_elem_wait)
        _validate_argument(timeout, 'timeout', (int, float))
        wait = WebDriverWait(kwds.get('parent', self._driver), timeout, ignored_exceptions=None)
        wait = getattr(wait, f'until{("_not", "")[bool(kwds.get("wait_until", True))]}', wait.until)
        ec = kwds.get('ec', EC.presence_of_all_elements_located)
        ec_args = []
        if kwds.get('locator_value'):
            _validate_argument(kwds['locator_value'], 'locator_value', str)
            ec_args.append((kwds.get('locator', By.ID), kwds['locator_value']))
        if kwds.get('attr_or_prop'):
            _validate_argument(kwds['attr_or_prop'], 'attr_or_prop', str)
            ec_args.append(kwds['attr_or_prop'])
        if kwds.get('value'):
            _validate_argument(kwds['value'], 'value', str)
            ec_args.append(kwds['value'])
        log_level = kwds.get('log_level', 40)
        _validate_argument(log_level, 'log_level', int, self.__VALID_LOG_LEVELS)
        try:
            elements = wait(ec(*ec_args))
            return elements if isinstance(elements, list) else [elements] if elements else []
        except TimeoutException:
            logger.log(log_level, 'None of the "%s" elements were found by %s and/or are not (in)visible in the DOM for'
                                  ' %ss.', *ec_args[0][::-1], timeout)
        except StaleElementReferenceException:
            logger.log(log_level, 'Reference to the DOM element containing %s "%s" was lost because the parent element '
                                  'was updated.', *ec_args[0])
        return []

    def _get_winning(self, locator_value: str, obj: type = int) -> Union[int, Decimal]:
        """
        Returns the amount of the win, if it exists in DOM.

        :param locator_value: str
        :param obj: type (int (default) or Decimal)
        :return: int or Decimal
        """
        _validate_argument(obj, 'obj', type, (int, Decimal))
        elements = self._get_elements(ec=EC.presence_of_element_located, locator_value=locator_value)
        return str2num(elements[0].get_property('textContent').strip(), obj) if elements else obj()

    def _get_bonus_keys(self, locator_value: str) -> list:
        """
        Returns a list of bonus keys, if they exist in DOM.

        :param locator_value: str
        :return: list
        """
        _validate_argument(locator_value, 'locator_value', str)
        return [str2num(e.get_property('textContent').replace('%', '').split()[0]) for e in
                self._get_elements(locator=By.XPATH, locator_value=f'//*[@id="{locator_value}"]/descendant::'
                                                                   'div[contains(@class,"reward_product_name")]')]

    def _get_bonus_costs(self, locator_value: str) -> list:
        """
        Returns a list of bonus costs, if they exist in DOM.

        :param locator_value: str
        :return: list
        """
        _validate_argument(locator_value, 'locator_value', str)
        return [str2num(e.get_property('textContent').replace(',', '').split()[0]) for e in
                self._get_elements(locator=By.XPATH, locator_value=f'//*[@id="{locator_value}"]/descendant::'
                                                                   'div[contains(@class,"reward_dollar_value_style")]')]

    def _get_bonus_buttons(self, locator_value: str) -> list:
        """
        Returns a list of bonus buttons, if they exist in DOM.

        :param locator_value: str
        :return: list
        """
        _validate_argument(locator_value, 'locator_value', str)
        return self._get_elements(locator=By.XPATH,
                                  locator_value=f'//*[@id="{locator_value}"]/descendant::'
                                                'button[contains(@class,"reward_link_redeem_button_style")]')

    def _get_bonuses_dict(self, locator_value: str) -> dict:
        """
        Returns a dictionary of bonuses, if they exists in DOM.

        :param locator_value: str
        :return: dict
        """
        return dict(zip(self._get_bonus_keys(locator_value), self._get_bonus_costs(locator_value)))

    def _close_modal(self, locator_value: str, close_btn_locator_value: str,
                     locator: By = By.ID, close_btn_locator: By = By.CSS_SELECTOR,
                     if_success_log_level: int = 10, if_success_log_msg: str = '') -> bool:
        """
        Closes the modal window, if it exists in DOM and is visible.

        :param locator: By - modal window locator
        :param locator_value: str - modal window locator value
        :param close_btn_locator: By - button or link locator to close the modal window
        :param close_btn_locator_value: str - button or link locator value to close the modal window
        :param if_success_log_level: int (0, 10 (default), 20, 30, 40, 50)
        :param if_success_log_msg: str
        :return: bool
        """
        _validate_argument(if_success_log_level, 'if_success_log_level', int, self.__VALID_LOG_LEVELS)
        _validate_argument(if_success_log_msg, 'if_success_log_msg', str)
        elements = self._get_elements(ec=EC.displayed_of_element, locator=locator, locator_value=locator_value,
                                      log_level=30)
        if not elements:
            return False
        elements = self._get_elements(parent=elements[0], ec=EC.presence_of_element_located, locator=close_btn_locator,
                                      locator_value=close_btn_locator_value, log_level=30)
        if not elements:
            return False
        self._driver.execute_script('arguments[0].click();', elements[0])
        elements = bool(self._get_elements(ec=EC.not_displayed_of_element, locator=locator, locator_value=locator_value,
                                           log_level=0))
        if not elements:
            elements = bool(self._get_elements(wait_until=False, ec=EC.displayed_of_element, locator=locator,
                                               locator_value=locator_value, log_level=30))
        if elements:  # elements = bool([element]) or bool([True]) or bool([])
            logger.log(if_success_log_level, '%s closed.',
                       (f'Modal window with {locator} "{locator_value}"', if_success_log_msg)[bool(if_success_log_msg)])
        return elements

    def _current_sign_form_id(self, locator_value: str = '',
                              if_success_log_level: int = 10, if_success_log_msg: str = '') -> str:
        """
        Sets the current sign form by id and/or returns the id of the current sign form, if it exists in DOM.

        :param locator_value: str
        :param if_success_log_level: int (0, 10 (default), 20, 30, 40, 50)
        :param if_success_log_msg: str
        :return: str
        """
        _validate_argument(locator_value, 'locator_value', str)
        _validate_argument(if_success_log_level, 'if_success_log_level', int, self.__VALID_LOG_LEVELS)
        _validate_argument(if_success_log_msg, 'if_success_log_msg', str)
        if locator_value:
            elements = self._get_elements(locator=By.CLASS_NAME,
                                          locator_value=locator_value.replace('form', 'menu_button'))
            if elements:
                self._driver.execute_script('arguments[0].click();', elements[0])
        elements = [self._get_elements(ec=EC.presence_of_element_located, locator_value=f'{e}_form')
                    for e in ('signup', 'login')]
        elements = [e[0].get_property('id') for e in elements if e and e[0].value_of_css_property('display') != 'none']
        if elements and elements[0] == locator_value:
            logger.log(if_success_log_level, '%s', (f'Current sign form id: "{locator_value}".',
                                                    if_success_log_msg)[bool(if_success_log_msg)])
        return elements[0] if elements else ''

    def _current_page_tab_id(self, locator_value: str = '',
                             if_success_log_level: int = 10, if_success_log_msg: str = '') -> str:
        """
        Sets the current page tab by id and/or returns the id of the current page tab, if it exists in DOM.

        :param locator_value: str
        :param if_success_log_level: int (0, 10 (default), 20, 30, 40, 50)
        :param if_success_log_msg: str
        :return: str
        """
        _validate_argument(locator_value, 'locator_value', str)
        _validate_argument(if_success_log_level, 'if_success_log_level', int, self.__VALID_LOG_LEVELS)
        _validate_argument(if_success_log_msg, 'if_success_log_msg', str)
        if locator_value:
            elements = self._get_elements(locator=By.CSS_SELECTOR,
                                          locator_value=f'a.{locator_value.replace("tab", "link")}')
            if elements:
                self._driver.execute_script('arguments[0].click();', elements[0])
        elements = [e.get_property('id') for e in self._get_elements(locator=By.CLASS_NAME, locator_value='page_tabs')
                    if e.value_of_css_property('display') != 'none']
        if elements and elements[0] == locator_value:
            logger.log(if_success_log_level, '%s', (f'Current page tab id: "{locator_value}".',
                                                    if_success_log_msg)[bool(if_success_log_msg)])
        return elements[0] if elements else ''

    def _value_input_field(self, locator_value: str, value: str = '',
                           if_success_log_level: int = 10, if_success_log_msg: str = '') -> Union[str, None]:
        """
        Fills the input field with the passed value and/or returns the value of the input field,
        if it exists in DOM and is visible.
        Returns None, if the value of the input field could not be determined.

        :param locator_value: str
        :param value: str
        :param if_success_log_level: int (0, 10 (default), 20, 30, 40, 50)
        :param if_success_log_msg: str
        :return: str or None
        """
        _validate_argument(value, 'value', str)
        _validate_argument(if_success_log_level, 'if_success_log_level', int, self.__VALID_LOG_LEVELS)
        _validate_argument(if_success_log_msg, 'if_success_log_msg', str)
        elements = self._get_elements(ec=EC.displayed_of_element, locator_value=locator_value)
        if elements:
            current = elements[0].get_attribute('value')
            if value:
                if current != value:
                    elements[0].clear()
                    elements[0].send_keys(value)
                    current = elements[0].get_property('value')
                if current == value:
                    logger.log(if_success_log_level, '%s filled.',
                               (f'Input field with id "{locator_value}"', if_success_log_msg)[bool(if_success_log_msg)])
            return current

    def _state_checkbox(self, locator_value: str, value: Union[bool, None] = None,
                        if_success_log_level: int = 10, if_success_log_msg: str = '') -> Union[bool, None]:
        """
        (Un)Checks the checkbox and/or returns the state of the checkbox, if it exists in DOM.
        Returns None, if the state of the checkbox could not be determined.

        :param locator_value: str
        :param value: bool or None
        :param if_success_log_level: int (0, 10 (default), 20, 30, 40, 50)
        :param if_success_log_msg: str
        :return: bool or None
        """
        _validate_argument(locator_value, 'locator_value', str)
        _validate_argument(if_success_log_level, 'if_success_log_level', int, self.__VALID_LOG_LEVELS)
        _validate_argument(if_success_log_msg, 'if_success_log_msg', str)
        elements = self._get_elements(ec=EC.presence_of_element_located, locator=By.XPATH,
                                      locator_value=f'//*[@id="{locator_value}"]/following-sibling::'
                                                    'span[contains(@class,"checkbox")]')
        if elements:
            state_element = elements[0]
            current = 'checked' in state_element.get_attribute('class')  # .split()
            if value is not None:
                if current != bool(value):
                    elements = self._get_elements(ec=EC.presence_of_element_located, locator_value=locator_value)
                    if elements:
                        self._driver.execute_script('arguments[0].click();', elements[0])
                        current = 'checked' in state_element.get_attribute('class')  # .split()
                if current == bool(value):
                    logger.log(if_success_log_level, '%s %schecked.',
                               (f'Checkbox with id "{locator_value}"', if_success_log_msg)[bool(if_success_log_msg)],
                               ('un', '')[current])
            return current

    def _active_bonus(self, locator_value: str, value: int = 0,
                      if_success_log_level: int = 10, if_success_log_msg: str = '') -> Union[int, None]:
        """
        Activates bonus by key and/or returns the key of the active bonus, if it exists in the DOM.
        Returns None, if an active bonus is detected but its key is not identified.
        Returns 0, if none of the bonuses is active.

        :param locator_value: str
        :param value: int
        :param if_success_log_level: int (0, 10 (default), 20, 30, 40, 50)
        :param if_success_log_msg: str
        :return: int or None
        """

        def get_active_bonus_key() -> Union[int, None]:
            elements = self._get_elements(ec=EC.presence_of_element_located, locator=By.XPATH,
                                          locator_value='//*[@id="bonus_container_'
                                                        f'{locator_value.replace("_rewards", "")}"]/p/span[1]',
                                          log_level=10)
            if elements:
                bonus_key = str2num(elements[0].get_property('textContent').replace('%', '').split()[0])
                if bonus_key not in bonus_keys:
                    logger.error('Key of the detected active bonus "%s" was not identified.', bonus_key)
                    return None
                return bonus_key
            return 0

        bonus_keys = self._get_bonus_keys(locator_value)
        if not bonus_keys:
            return None
        _validate_argument(value, 'value', int, tuple(bonus_keys + [0]))
        _validate_argument(if_success_log_level, 'if_success_log_level', int, self.__VALID_LOG_LEVELS)
        _validate_argument(if_success_log_msg, 'if_success_log_msg', str)
        current = get_active_bonus_key()
        if current == 0 and value:
            try:
                bonus_cost = self._get_bonus_costs(locator_value)[bonus_keys.index(value)]
                if bonus_cost + (self.free_play_cost if self.__check_for_captcha else 0) <= self.balance_rp:
                    self._driver.execute_script('arguments[0].click();',
                                                self._get_bonus_buttons(locator_value)[bonus_keys.index(value)])
                    current = get_active_bonus_key()
            except IndexError:
                bonus_cost = 0
            if current == value:
                logger.log(if_success_log_level, '%s activated (%s RP spent).',
                           (f'Bonus with key "{current}" from table with id "{locator_value}"',
                            if_success_log_msg)[bool(if_success_log_msg)], bonus_cost)
        return current

    @property
    def browser_name(self) -> str:
        """
        Returns browser name. Read-only property.
        """
        return self._driver.name.capitalize()

    @property
    def browser_version(self) -> str:
        """
        Returns browser version. Read-only property.
        """
        return self._driver.capabilities.get('browserVersion', '')

    @property
    def window_handles(self) -> list:
        """
        Returns the handles of all windows within the current session. Read-only property.
        """
        return self._driver.window_handles

    @property
    def current_window_handle(self) -> str:
        """
        Returns the handle of the current window. Read-only property.
        """
        return self._driver.current_window_handle

    @property
    def current_url(self) -> str:
        """
        Returns the current URL. Read-only property.
        """
        return self._driver.current_url

    @property
    def title(self) -> str:
        """
        Returns the title of the site page. Read-only property.
        """
        return self._driver.title

    @property
    def user_id(self) -> str:
        """
        Returns the user ID. Read-only property.
        """
        elements = self._get_elements(ec=EC.presence_of_element_located, locator=By.XPATH,
                                      locator_value='//*[@id="edit_tab"]/p/span[2]')
        return elements[0].get_property('textContent').strip() if elements else ''

    @property
    def btc_address(self) -> str:
        """
        Returns the BTC (withdrawal) address. Read-only property.
        """
        return self._value_input_field('edit_profile_form_btc_address')

    @property
    def email_address(self) -> str:
        """
        Returns the email address. Read-only property.
        """
        return self._value_input_field('edit_profile_form_email')

    @property
    def recovery_phone_number(self) -> str:
        """
        Returns the recovery phone number. Read-only property.
        """
        return self._value_input_field('rp_phone_number')

    @property
    def password(self) -> str:
        """
        Returns the password. Read-only property.
        """
        return self.__password

    @property
    def totp_secret(self) -> str:
        """
        Returns the secret key that is used to generate the Time-based One-Time Password. Read-only property.
        """
        return self.__totp_secret

    @property
    def timeout_page_load(self) -> Union[int, float]:
        """
        Returns the time to wait (in seconds) for a full page load before an exception TimeoutException is raised.
        """
        return self.__timeout_page_load

    @timeout_page_load.setter
    def timeout_page_load(self, value: Union[int, float]):
        """
        Sets the time to wait (in seconds) for a full page load before an exception TimeoutException is raised.
        """
        _validate_argument(value, 'value', (int, float))
        self._driver.set_page_load_timeout(value)
        self.__timeout_page_load = value
        logger.info('Page load timeout changed (sec): %s', value)

    @property
    def timeout_elem_wait(self) -> Union[int, float]:
        """
        Returns the time to wait (in seconds) for an element(s) to appear in the DOM and/or (in)visibility before an
        exception TimeoutException is raised.
        """
        return self.__timeout_elem_wait

    @timeout_elem_wait.setter
    def timeout_elem_wait(self, value: Union[int, float]):
        """
        Sets the time to wait (in seconds) for an element(s) to appear in the DOM and/or (in)visibility before an
        exception TimeoutException is raised.
        """
        _validate_argument(value, 'value', (int, float))
        self.__timeout_elem_wait = value
        logger.info('Element(s) wait timeout changed (sec): %s', value)

    @property
    def check_for_captcha(self) -> bool:
        """
        Returns captcha check status.
        """
        return self.__check_for_captcha

    @check_for_captcha.setter
    def check_for_captcha(self, value: bool):
        """
        Sets captcha check status.
        """
        self.__check_for_captcha = bool(value)
        logger.info('Captcha check status changed: %s', bool(value))

    @property
    def state_free_play_sound(self) -> Union[bool, None]:
        """
        Returns the state of the free play sound checkbox.
        """
        return self._state_checkbox('free_play_sound')

    @state_free_play_sound.setter
    def state_free_play_sound(self, value: bool):
        """
        (Un)Checks the free play sound checkbox.
        """
        self._state_checkbox('free_play_sound', value, 20, 'Free play sound')

    @property
    def state_disable_lottery(self) -> Union[bool, None]:
        """
        Returns the state of the disable lottery checkbox.
        """
        return self._state_checkbox('disable_lottery_checkbox')

    @state_disable_lottery.setter
    def state_disable_lottery(self, value: bool):
        """
        (Un)Checks the disable lottery checkbox.
        """
        self._state_checkbox('disable_lottery_checkbox', value, 20, 'Disable lottery')

    @property
    def state_disable_interest(self) -> Union[bool, None]:
        """
        Returns the state of the disable interest checkbox.
        """
        return self._state_checkbox('disable_interest_checkbox')

    @state_disable_interest.setter
    def state_disable_interest(self, value: bool):
        """
        (Un)Checks the disable interest checkbox.
        """
        self._state_checkbox('disable_interest_checkbox', value, 20, 'Disable interest')

    @property
    def balance_btc(self) -> Decimal:
        """
        Returns current balance in BTC. Read-only property.
        """
        elements = self._get_elements(locator=By.XPATH, locator_value='//*[starts-with(@id,"balance")]')
        return str2num(elements[0].get_property('textContent').strip(), Decimal) if elements else Decimal()

    @property
    def balance_rp(self) -> int:
        """
        Returns current number of reward points. Read-only property.
        """
        elements = self._get_elements(ec=EC.presence_of_element_located, locator=By.XPATH,
                                      locator_value='//*[@id="rewards_tab"]/descendant::'
                                                    'div[contains(@class,"user_reward_points")]')
        return str2num(elements[0].get_property('textContent').replace(',', '').strip()) if elements else 0

    @property
    def balance_lt(self) -> int:
        """
        Returns current number of lottery tickets. Read-only property.
        """
        elements = self._get_elements(ec=EC.presence_of_element_located, locator_value='user_lottery_tickets')
        return str2num(elements[0].get_property('textContent').replace(',', '').strip()) if elements else 0

    @property
    def winning_btc(self) -> Decimal:
        """
        Returns the amount of the win in BTC. Read-only property.
        """
        return self._get_winning('winnings', Decimal)

    @property
    def winning_rp(self) -> int:
        """
        Returns the number of reward points won. Read-only property.
        """
        return self._get_winning('fp_reward_points_won')

    @property
    def winning_lt(self) -> int:
        """
        Returns the number of lottery tickets won. Read-only property.
        """
        return self._get_winning('fp_lottery_tickets_won')

    @property
    def winning_wof(self) -> int:
        """
        Returns the number of wheel of fortune spins won. Read-only property.
        """
        elements = self._get_elements(ec=EC.presence_of_element_located, locator=By.XPATH,
                                      locator_value='//*[@id="fp_bonus_wins"]/a', log_level=10)
        return str2num(elements[0].get_property('textContent').split()[0]) if elements else 0

    @property
    def bonuses_btc(self) -> dict:
        """
        Returns a dictionary of free BTC bonuses. Read-only property.
        """
        return self._get_bonuses_dict('fp_bonus_rewards')

    @property
    def bonuses_lt(self) -> dict:
        """
        Returns a dictionary of lottery tickets bonuses. Read-only property.
        """
        return self._get_bonuses_dict('free_lott_rewards')

    @property
    def bonuses_wof(self) -> dict:
        """
        Returns a dictionary of wheel of fortune bonuses. Read-only property.
        """
        return self._get_bonuses_dict('free_wof_rewards')

    @property
    def active_bonus_btc(self) -> Union[int, None]:
        """
        Returns the key of the active free BTC bonus.
        """
        return self._active_bonus('fp_bonus_rewards')

    @active_bonus_btc.setter
    def active_bonus_btc(self, value: int):
        """
        Activates free BTC bonus by key.
        """
        self._active_bonus('fp_bonus_rewards', value, 20, f'Free BTC bonus "{value}%"')

    @property
    def active_bonus_lt(self) -> Union[int, None]:
        """
        Returns the key of the active lottery tickets bonus.
        """
        return self._active_bonus('free_lott_rewards')

    @active_bonus_lt.setter
    def active_bonus_lt(self, value: int):
        """
        Activates lottery tickets bonus by key.
        """
        self._active_bonus('free_lott_rewards', value, 20,
                           f'Lottery tickets bonus "{value} ticket{("", "s")[value > 1]}"')

    @property
    def active_bonus_wof(self) -> Union[int, None]:
        """
        Returns the key of the active wheel of fortune bonus.
        """
        return self._active_bonus('free_wof_rewards')

    @active_bonus_wof.setter
    def active_bonus_wof(self, value: int):
        """
        Activates wheel of fortune bonus by key.
        """
        self._active_bonus('free_wof_rewards', value, 20,
                           f'Wheel of fortune bonus "{value} spin{("", "s")[value > 1]}"')

    @property
    def free_play_countdown(self) -> int:
        """
        Returns the time (in seconds) remaining until the next free play. Read-only property.
        """
        elements = self._get_elements(ec=EC.presence_of_element_located, locator_value='time_remaining')
        if not elements:
            return 0
        elements = self._get_elements(parent=elements[0], locator=By.CSS_SELECTOR,
                                      locator_value='span.countdown_amount', log_level=10)
        if elements:
            try:
                elements = [str2num(e.get_property('textContent').strip()) for e in elements]
                return elements[0] * 60 + elements[1]
            except StaleElementReferenceException:
                logger.error('Reference to the countdown timer section element was lost while getting its property '
                             'value.')
            except IndexError:
                logger.error('Countdown timer has less than two sections.')
        return 0

    @property
    def free_play_cost(self) -> int:
        """
        Returns the cost (in RP) of a free play without captcha. Read-only property.
        """
        elements = self._get_elements(ec=EC.presence_of_element_located, locator=By.XPATH,
                                      locator_value='//*[@id="play_without_captcha_desc"]/descendant::span')
        return str2num(elements[0].get_property('textContent').replace(',', '').strip()) if elements else 0

    def is_available(self) -> bool:
        """
        Checks the site's availability.
        """
        return bool(self._get_elements(ec=EC.title_contains_lower, value=str(self)))

    def is_authenticated(self, log_level: int = 10) -> list:
        """
        Checks if the user is authenticated.

        :param log_level: int (0, 10 (default), 20, 30, 40, 50)
        :return: list
        """
        return self._get_elements(locator=By.CSS_SELECTOR, locator_value='a.logout_link', log_level=log_level)

    def is_not_authenticated(self, log_level: int = 10) -> list:
        """
        Checks if the user is not authenticated.

        :param log_level: int (0, 10 (default), 20, 30, 40, 50)
        :return: list
        """
        return self._get_elements(ec=EC.presence_of_element_located, locator_value='login_button', log_level=log_level)

    def is_ready_free_play(self, log_level: int = 10) -> list:
        """
        Checks readiness for free play.

        :param log_level: int (0, 10 (default), 20, 30, 40, 50)
        :return: list
        """
        return self._get_elements(ec=EC.displayed_of_element, locator_value='free_play_form_button',
                                  log_level=log_level)

    def is_ready_free_play_with_captcha(self, log_level: int = 10) -> bool:
        """
        Checks readiness for free play with captcha.

        :param log_level: int (0, 10 (default), 20, 30, 40, 50)
        :return: bool
        """
        elements = self._get_elements(ec=EC.frame_to_be_available_and_switch_to_it, locator=By.XPATH,
                                      locator_value='//*[@id="free_play_recaptcha"]/descendant::iframe',
                                      log_level=log_level)
        if elements:
            elements = self._get_elements(ec=EC.presence_of_element_located, locator_value='checkbox',
                                          log_level=log_level)
            if elements:
                self._driver.execute_script('arguments[0].click();', elements[0])
                elements = self._get_elements(ec=EC.value_to_be_equal_to_attribute_value_of_element,
                                              locator_value='checkbox', attr_or_prop='aria-checked', value='true',
                                              log_level=log_level)
            self._driver.switch_to.default_content()
        return bool(elements)

    def is_ready_free_play_without_captcha(self, log_level: int = 10) -> bool:
        """
        Checks readiness for free play without captcha.

        :param log_level: int (0, 10 (default), 20, 30, 40, 50)
        :return: bool
        """
        elements = self._get_elements(ec=EC.displayed_of_element, locator_value='play_without_captchas_button',
                                      log_level=log_level)
        if elements:
            self._driver.execute_script('arguments[0].click();', elements[0])
        return bool(self._get_elements(ec=EC.displayed_of_element, locator_value='play_with_captcha_button',
                                       log_level=log_level))

    def play_free_play(self) -> bool:
        """
        Plays a free play.
        """
        log_msg = 'Free play '
        free_play_cost = 0
        if self.__check_for_captcha:
            elements = self.is_ready_free_play_with_captcha(30)
            log_msg = f'{log_msg}with{("out", "")[elements]} captcha '
            if not elements:
                free_play_cost = self.free_play_cost
                if free_play_cost > self.balance_rp:
                    logger.error('%sfailed. Reward points are not enough to play free play (free play cost %s RP).',
                                 log_msg, free_play_cost)
                    return False
                if not self.is_ready_free_play_without_captcha(40):
                    logger.error('%sfailed. No readiness.', log_msg)
                    return False
        elements = self.is_ready_free_play(40)
        if not elements:
            logger.error('%sfailed.', log_msg)
            return False
        self._driver.execute_script('arguments[0].click();', elements[0])
        elements = bool(self._get_elements(ec=EC.displayed_of_element, locator_value='free_play_result'))
        logger.log((40, 20)[elements], '%s%s.', log_msg,
                   ('failed', f'successful{(f" ({free_play_cost} RP spent)", "")[free_play_cost == 0]}')[elements])
        return elements

    def play_free_play_sound(self) -> bool:
        """
        Plays a free play sound.
        """
        elements = self._get_elements(ec=EC.presence_of_element_located, locator_value='test_sound', log_level=30)
        if elements:
            self._driver.execute_script('arguments[0].click();', elements[0])
        return bool(elements)

    def load_bonus_table(self) -> bool:
        """
        Temporarily jumps to the rewards tab to load the bonus table.
        """
        prev_page_tab_id = self._current_page_tab_id()
        if self._current_page_tab_id('rewards_tab') == 'rewards_tab':
            self._current_page_tab_id(prev_page_tab_id)
            return True
        return False

    def activate_bonuses(self, bonuses: dict) -> dict:
        """
        Activates bonuses in the order they appear in the dictionary.
        Each subsequent bonus will try to activate only if all previous bonuses are activated.

        :param bonuses: dict
        :return: dict
        """
        _validate_argument(bonuses, 'bonuses', dict)
        result = {}
        for k, v in bonuses.items():
            _validate_argument(k, 'bonus_key', str, self.__VALID_BONUS_KEYS)
            attr_name = f'active_bonus_{k}'
            if all(result.values()):
                setattr(self, attr_name, v)
            result[k] = getattr(self, attr_name)
        return result

    def close_cookie_warning_banner(self) -> bool:
        """
        Closes cookie warning banner.
        """
        return self._close_modal('div.cc_banner-wrapper', 'a.cc_btn', locator=By.CSS_SELECTOR,
                                 if_success_log_level=20, if_success_log_msg='Cookie warning banner')

    def close_notification_modal(self) -> bool:
        """
        Closes modal notification window.
        """
        return self._close_modal('push_notification_modal', 'div.pushpad_deny_button',
                                 if_success_log_level=20, if_success_log_msg='Modal notification window')

    def close_after_free_play_modal(self) -> bool:
        """
        Closes modal window after free play.
        """
        return self._close_modal('myModal22', 'a.close-reveal-modal',
                                 if_success_log_level=20, if_success_log_msg='Modal window after free play')

    def open(self, url: str = '') -> bool:
        """
        Opens the site.

        :param url: str
        :return: bool
        """
        url = url if url else self.URL
        _validate_argument(url, 'url', str)
        log_msg = f'Open site by URL "{url}" '
        try:
            self._driver.get(url)
            logger.info('%ssuccessful.', log_msg)
            return True
        except WebDriverException as err:
            logger.error(err.msg)
            logger.critical('%sfailed.', log_msg)
            return False

    def sign_in(self, address: str, password: str, totp_secret: str = '') -> bool:
        """
        User sign-in.

        :param address: str
        :param password: str
        :param totp_secret: str
        :return: bool
        """
        log_msg = 'Sign-in '
        if self._current_sign_form_id('login_form') != 'login_form':
            logger.critical('%sfailed.', log_msg)
            return False
        if not address:
            logger.error('Email or BTC address is empty.')
            logger.critical('%sfailed.', log_msg)
            return False
        if self._value_input_field('login_form_btc_address', address) != address:
            logger.critical('%sfailed.', log_msg)
            return False
        if not password:
            logger.error('Password is empty.')
            logger.critical('%sfailed.', log_msg)
            return False
        if self._value_input_field('login_form_password', password) != password:
            logger.critical('%sfailed.', log_msg)
            return False
        if totp_secret:
            totp = TOTP(totp_secret).now()
            if self._value_input_field('login_form_2fa', totp) != totp:
                logger.critical('%sfailed.', log_msg)
                return False
        elements = self.is_not_authenticated(40)
        if not elements:
            logger.critical('%sfailed.', log_msg)
            return False
        self._driver.execute_script('arguments[0].click();', elements[0])
        elements = bool(self.is_authenticated())
        if elements:
            self.__password = password
            self.__totp_secret = totp_secret
        logger.log((50, 20)[elements], '%s%s.', log_msg, ('failed', 'successful')[elements])
        return elements

    def sign_out(self) -> bool:
        """
        User sign-out.
        """
        log_msg = 'Sign-out '
        elements = self.is_authenticated(40)
        if not elements:
            logger.error('%sfailed.', log_msg)
            return False
        self._driver.execute_script('arguments[0].click();', elements[0])
        elements = bool(self.is_not_authenticated())
        if elements:
            self.__password = ''
            self.__totp_secret = ''
        logger.log((40, 20)[elements], '%s%s.', log_msg, ('failed', 'successful')[elements])
        return elements

    def refresh(self) -> bool:
        """
        Refreshes the current page.
        """
        log_msg = 'Refresh '
        try:
            self._driver.refresh()
            logger.info('%ssuccessful.', log_msg)
            return True
        except WebDriverException as err:
            logger.error(err.msg)
            logger.critical('%sfailed.', log_msg)
            return False

    def quit(self):
        """
        Quits the driver and close every associated window.
        """
        self._driver.quit()
        logger.info('Browser windows associated with the site are closed.')
