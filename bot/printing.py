import inspect
from typing import Union
from colorama import Fore, Style
import sys
import traceback


def __printc__(message, color: str = Style.RESET_ALL) -> None:
    if message == None:
        message = ''
    print(f'{color}{message}{Style.RESET_ALL}')


def printe(message: str, e: Union[Exception, None] = None, is_fatal: bool = False) -> None:
    """
    Print error with red coloration and prepended with [ERROR]
    """
    message = f'[ERROR] {inspect.stack()[1].function}(): {message}'
    __printc__(message, Fore.RED)
    if e != None:
        # __printc__(e, Fore.RED)
        __printc__(traceback.format_exc(), Fore.RED)
    if is_fatal:
        sys.exit()


def printw(message: str) -> None:
    """
    Print warning with yellow coloration and prepended with [WARNING]
    """
    message = f'[WARNING] {inspect.stack()[1].function}(): {message}'
    __printc__(message, Fore.YELLOW)


def prints(message: str) -> None:
    """
    Print status with green coloration and prepended with [STATUS]
    """
    message = f'[STATUS] {inspect.stack()[1].function}(): {message}'
    __printc__(message, Fore.GREEN)


def printp(message) -> None:
    """
    Print plain without any fancy coloration
    """
    __printc__(message)


def printl(message) -> None:
    """
    Print log (or print lame) with dimmed coloration
    """
    __printc__(message, Fore.LIGHTBLACK_EX)
