#!/usr/bin/env python -B
import sys
import core
from time import sleep
from itertools import count
from logging import basicConfig, getLogger

# Import custom settings
try:
    settings = __import__(sys.argv[1])
    print(f'Current settings module "{sys.argv[1]}".')
except IndexError:
    settings = __import__('settings')
    print('Current settings module "settings".')
except (ModuleNotFoundError, ImportError) as err:
    settings = __import__('settings')
    print({'ModuleNotFoundError': f'Module "{sys.argv[1]}" not found.\n',
           'ImportError': f'Failed to import module "{sys.argv[1]}".\n'}[err.__class__.__name__],
          'Current settings module "settings".', sep='')

# Logging initialization
faucet_log_level = getattr(settings, "FAUCET_LOG_LEVEL", 20)
basicConfig(**({'filename': getattr(settings, 'LOGS_DIR', '') / f'{getattr(settings, "LOGS_PREFIX", "")}'
                                                                f'{getattr(settings, "FAUCET_LOG_FILE", "faucet.log")}'
                                                                f'{getattr(settings, "LOGS_SUFFIX", "")}',
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

    :return: int - error code
    """
    faucet = core.FreeBitcoinFaucet(
        browser_name=getattr(settings, 'BROWSER_NAME', 'Firefox'),
        driver_exec_path=getattr(settings, 'DRIVERS_DIR', '') / getattr(settings, 'DRIVER_FILE', 'geckodriver'),
        driver_log_path=getattr(settings, 'LOGS_DIR', '') / f'{getattr(settings, "LOGS_PREFIX", "")}'
                                                            f'{getattr(settings, "DRIVER_LOG_FILE", "driver.log")}'
                                                            f'{getattr(settings, "LOGS_SUFFIX", "")}',
        timeout_page_load=getattr(settings, 'TIMEOUT_PAGE_LOAD', 30),
        timeout_elem_wait=getattr(settings, 'TIMEOUT_ELEM_WAIT', 10),
        check_for_captcha=getattr(settings, 'CHECK_FOR_CAPTCHA', True))
    if not faucet:
        return 1
    logger.info('Browser: %s', faucet.browser_name)
    logger.info('Current URL: %s', faucet.current_url)
    logger.info('Faucet: %s', faucet)
    logger.info('Faucet title: %s', faucet.title)
    logger.info('Page load timeout (sec): %s', faucet.timeout_page_load)
    logger.info('Element(s) wait timeout (sec): %s', faucet.timeout_elem_wait)
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

    logger.debug('User ID: %s', faucet.user_id)
    logger.debug('Email address: %s', faucet.email_address)
    if faucet.recovery_phone_number != '+0':
        logger.debug('Recovery phone number: %s', faucet.recovery_phone_number)
    if faucet.btc_address:
        logger.debug('BTC (withdrawal) address: %s', faucet.btc_address)

    faucet.state_sound_free_play = getattr(settings, 'SOUND_FREE_PLAY', False)
    faucet.state_disable_lottery = getattr(settings, 'DISABLE_LOTTERY', False)
    faucet.state_disable_interest = getattr(settings, 'DISABLE_INTEREST', False)
    logger.info('Starting balance: BTC: %.8f | Reward points: %s | Lottery tickets: %s',
                faucet.balance_btc, faucet.balance_rp, faucet.balance_lt)

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
            if attempt > 1:
                faucet.refresh()
            delay = faucet.countdown_free_play
            if delay:
                logger.info('Free play countdown (sec): %s => %sm %ss', delay, *divmod(delay, 60))
                sleep(delay + getattr(settings, 'FREE_PLAY_AFTER_COUNTDOWN_DELAY', 0))
                if getattr(settings, 'FREE_PLAY_AFTER_COUNTDOWN_REFRESH', False):
                    faucet.refresh()
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
        if num == free_play_num:
            break
    is_auth = not faucet.sign_out()
    faucet.quit()
    return int(is_auth)


if __name__ == '__main__':
    sys.exit(scenario())
