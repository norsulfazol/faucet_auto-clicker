#!/usr/bin/env python3 -B
import os
import sys
import core
from time import sleep
from itertools import count
from logging import basicConfig, getLogger

# Import custom settings
try:
    settings = __import__(sys.argv[1])
except (IndexError, ModuleNotFoundError, ImportError) as err:
    settings = __import__('settings')
    if err.__class__.__name__ != 'IndexError':
        print({'ModuleNotFoundError': f'Module "{sys.argv[1]}" not found.',
               'ImportError': f'Failed to import module "{sys.argv[1]}".'}[err.__class__.__name__])
print(f'Current settings module "{settings.__name__}".')

# Logging initialization
if getattr(settings, 'LOGS_DIR', '') and not os.path.exists(settings.LOGS_DIR):
    os.mkdir(settings.LOGS_DIR)
faucet_log_level = getattr(settings, "FAUCET_LOG_LEVEL", 20)
basicConfig(**({'filename': os.path.join(getattr(settings, 'LOGS_DIR', ''),
                                         f'{getattr(settings, "LOGS_PREFIX", "")}'
                                         f'{getattr(settings, "FAUCET_LOG_FILE", "faucet.log")}'
                                         f'{getattr(settings, "LOGS_SUFFIX", "")}'),
                'filemode': getattr(settings, 'FAUCET_LOG_FILE_MODE', 'w')}
               if getattr(settings, 'FAUCET_LOG_TO_FILE', True) else {'stream': sys.stdout}),
            format=f'%(asctime)s{("", " [%(process)6d]")[faucet_log_level == 10]} %(levelname)-8s'
                   f'{("", " (%(module)s, %(funcName)s)")[faucet_log_level == 10]}: %(message)s',
            datefmt='%d.%m.%y %H:%M:%S', level=30)
logger = getLogger(__name__)
logger.setLevel(faucet_log_level)
core.logger.setLevel(faucet_log_level)
del faucet_log_level


def scenario() -> int:
    """
    Scenario.

    :return: int - exit status
    """

    def is_refreshed() -> bool:
        timeout = getattr(settings, 'ON_UNAVAILABLE_ATTEMPTS_TIMEOUT', 60 * 5)
        for att in count(1):
            if on_unavailable_attempts != 1:
                logger.info('Refresh attempt: %s/%s', att,
                            (on_unavailable_attempts, 'infinity')[on_unavailable_attempts == 0])
            if faucet.refresh() and faucet.is_available():
                return True
            if att == on_unavailable_attempts:
                return False
            logger.info('Timeout for next refresh attempt (sec): %s => %sh %sm %ss', timeout,
                        *divmod(timeout // 60, 60), timeout % 60)
            sleep(timeout)
            timeout *= on_unavailable_attempts_timeout_increase

    browser = getattr(settings, 'BROWSER', 'firefox').strip()
    browser_file = getattr(settings, f'{browser.upper()}_BROWSER_FILE', browser).strip()
    browser_file = core.BrowserExecFileOrLink(browser_file if browser_file else browser,
                                              directory=getattr(settings, f'{browser.upper()}_BROWSER_DIR', '').strip(),
                                              reg_key=getattr(settings,
                                                              f'{browser.upper()}_BROWSER_REG_KEY', '').strip())
    if not browser_file:
        return 1
    print(browser_file)
    driver_file_type = getattr(core, f'{browser.capitalize()}DriverExecFileOrLink', None)
    if not driver_file_type:
        return 1
    driver_file = getattr(settings, f'{browser.upper()}_DRIVER_FILE', browser).strip()
    driver_file = driver_file_type(driver_file if driver_file else browser,
                                   directory=getattr(settings, f'{browser.upper()}_DRIVER_DIR', '').strip())
    del driver_file_type
    if not driver_file:
        return 1
    print(driver_file)
    if not driver_file.update(getattr(settings, f'{browser.upper()}_DRIVER_URL', '').strip(),
                              browser_version_info=browser_file.version_info):
        return 1
    #
    quick_start = getattr(settings, 'QUICK_START', True)
    faucet = core.FreeBitcoinFaucet(browser_name=browser,
                                    driver_exec_path=driver_file.path,
                                    driver_log_path=os.path.join(getattr(settings, 'LOGS_DIR', ''),
                                                                 f'{getattr(settings, "LOGS_PREFIX", "")}'
                                                                 f'{getattr(settings, "DRIVER_LOG_FILE", "driver.log")}'
                                                                 f'{getattr(settings, "LOGS_SUFFIX", "")}'),
                                    driver_options=getattr(settings, f'{browser.upper()}_BROWSER_OPTIONS', {}),
                                    timeout_page_load=getattr(settings, 'TIMEOUT_PAGE_LOAD', 30),
                                    timeout_elem_wait=getattr(settings, 'TIMEOUT_ELEM_WAIT', 10),
                                    check_for_captcha=getattr(settings, 'CHECK_FOR_CAPTCHA', True),
                                    **({'open': True, 'sign_in': True,
                                        'sign_in_address': getattr(settings, 'AUTH_ADDRESS', ''),
                                        'sign_in_password': getattr(settings, 'AUTH_PASSWORD', ''),
                                        'sign_in_totp_secret': getattr(settings, 'AUTH_TOTP_SECRET', '')}
                                       if quick_start else {}))
    if not faucet:
        return 1
    on_unavailable_attempts = getattr(settings, 'ON_UNAVAILABLE_ATTEMPTS', 1)
    on_unavailable_attempts_timeout_increase = getattr(settings, 'ON_UNAVAILABLE_ATTEMPTS_TIMEOUT_INCREASE', 1)
    if quick_start:
        if not faucet.is_available() or not faucet.is_authenticated():
            faucet.quit()
            return 1
        if getattr(settings, 'CLOSE_COOKIE_WARNING_BANNER', True):
            faucet.close_cookie_warning_banner()
    else:
        logger.info('Faucet: %s', faucet)
        logger.info('Browser: %s (v.%s)', faucet.browser_name, faucet.browser_version)
        logger.info('Page load timeout (sec): %s', faucet.timeout_page_load)
        logger.info('Element(s) wait timeout (sec): %s', faucet.timeout_elem_wait)
        logger.info('Captcha check status: %s', faucet.check_for_captcha)
        #
        on_unavailable_attempts_timeout = getattr(settings, 'ON_UNAVAILABLE_ATTEMPTS_TIMEOUT', 60 * 5)
        for attempt in count(1):
            if on_unavailable_attempts != 1:
                logger.info('Open site attempt: %s/%s', attempt,
                            (on_unavailable_attempts, 'infinity')[on_unavailable_attempts == 0])
            if faucet.open() and faucet.is_available():
                break
            if attempt == on_unavailable_attempts:
                faucet.quit()
                return 1
            logger.info('Timeout for next open site attempt (sec): %s => %sh %sm %ss', on_unavailable_attempts_timeout,
                        *divmod(on_unavailable_attempts_timeout // 60, 60), on_unavailable_attempts_timeout % 60)
            sleep(on_unavailable_attempts_timeout)
            on_unavailable_attempts_timeout *= on_unavailable_attempts_timeout_increase
        logger.info('Current URL: %s', faucet.current_url)
        logger.info('Site page title: %s', faucet.title)
        #
        if getattr(settings, 'CLOSE_COOKIE_WARNING_BANNER', True):
            faucet.close_cookie_warning_banner()
        if getattr(settings, 'CLOSE_NOTIFICATION_MODAL', True):
            faucet.close_notification_modal()
        if not faucet.sign_in(getattr(settings, 'AUTH_ADDRESS', ''),
                              getattr(settings, 'AUTH_PASSWORD', ''),
                              getattr(settings, 'AUTH_TOTP_SECRET', '')):
            faucet.quit()
            return 1
    if getattr(settings, 'CLOSE_NOTIFICATION_MODAL', True):
        faucet.close_notification_modal()
    #
    logger.debug('User ID: %s', faucet.user_id)
    logger.debug('Email address: %s', faucet.email_address)
    if faucet.recovery_phone_number != '+0':
        logger.debug('Recovery phone number: %s', faucet.recovery_phone_number)
    if faucet.btc_address:
        logger.debug('BTC (withdrawal) address: %s', faucet.btc_address)
    #
    faucet.state_free_play_sound = getattr(settings, 'FREE_PLAY_SOUND', False)
    faucet.state_disable_lottery = getattr(settings, 'DISABLE_LOTTERY', False)
    faucet.state_disable_interest = getattr(settings, 'DISABLE_INTEREST', False)
    logger.info('Starting balance: BTC: %.8f | Reward points: %s | Lottery tickets: %s',
                faucet.balance_btc, faucet.balance_rp, faucet.balance_lt)
    #
    free_play_num = getattr(settings, 'FREE_PLAY_NUM', 0)
    free_play_attempts = getattr(settings, 'FREE_PLAY_ATTEMPTS', 1)
    for num in count(1):
        if free_play_num != 1:
            logger.info('Free play: %s/%s', num, (free_play_num, 'infinity')[free_play_num == 0])
        is_played = False
        for attempt in count(1):
            if free_play_attempts != 1:
                logger.info('Free play attempt: %s/%s', attempt,
                            (free_play_attempts, 'infinity')[free_play_attempts == 0])
            if attempt > 1 and not is_refreshed():
                break
            delay = faucet.free_play_countdown
            if delay:
                logger.info('Free play countdown (sec): %s => %sm %ss', delay, *divmod(delay, 60))
                sleep(delay + getattr(settings, 'FREE_PLAY_AFTER_COUNTDOWN_DELAY', 0))
                if (getattr(settings, 'FREE_PLAY_AFTER_COUNTDOWN_REFRESH',
                            False) or not faucet.is_available()) and not is_refreshed():
                    break
            if faucet.is_ready_free_play():
                if faucet.load_bonus_table():
                    logger.debug('Available bonuses free BTC (%%/RP): %s',
                                 ', '.join([f'{k}/{v}' for k, v in sorted(faucet.bonuses_btc.items())]))
                    logger.debug('Available bonuses lottery tickets (tickets/RP): %s',
                                 ', '.join([f'{k}/{v}' for k, v in sorted(faucet.bonuses_lt.items())]))
                    logger.debug('Available bonuses wheel of fortune (spins/RP): %s',
                                 ', '.join([f'{k}/{v}' for k, v in sorted(faucet.bonuses_wof.items())]))
                    bonuses = getattr(settings, 'BONUSES', {})
                    if any(bonuses.values()):
                        faucet.timeout_elem_wait = getattr(settings, 'BONUSES_TIMEOUT_ELEM_WAIT', 5)
                        current_bonuses_states = faucet.activate_bonuses(bonuses)
                        faucet.timeout_elem_wait = getattr(settings, 'TIMEOUT_ELEM_WAIT', 10)
                        if current_bonuses_states:
                            logger.debug('Current states of bonuses: %s',
                                         ', '.join([f'"{k}"-> {v}' for k, v in current_bonuses_states.items()]))
                is_played = faucet.play_free_play()
            if is_played or attempt == free_play_attempts:
                break
        if not is_played:
            break
        win_lt = faucet.winning_lt
        win_wof = faucet.winning_wof if getattr(settings, 'CHECK_FOR_WINNING_WOF', True) else 0
        logger.info('Winning: BTC: %.8f | Reward points: %s%s%s', faucet.winning_btc, faucet.winning_rp,
                    f' | Lottery tickets: {win_lt}' if win_lt else '',
                    f' | Wheel of fortune spins: {win_wof}' if win_wof else '')
        logger.info('Balance: BTC: %.8f | Reward points: %s | Lottery tickets: %s',
                    faucet.balance_btc, faucet.balance_rp, faucet.balance_lt)
        if getattr(settings, 'CLOSE_AFTER_FREE_PLAY_MODAL', True):
            faucet.close_after_free_play_modal()
        faucet.play_free_play_sound()
        if num == free_play_num:
            break
    is_authenticated = not faucet.sign_out()
    faucet.quit()
    return int(is_authenticated)


def main():
    exit_status = scenario()
    print('\nExit status:', ('ERROR', 'OK')[exit_status == 0])
    input('\nPress <Enter> key to complete the program ...')
    sys.exit(exit_status)


if __name__ == '__main__':
    main()
