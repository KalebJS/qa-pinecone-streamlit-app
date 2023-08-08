import os
from functools import wraps

from config import SCREENSHOTS_FOLDER
from libraries.common import log_message


def screenshot_and_reload_on_failure(func):
    """
    Decorator to take a screenshot of the current page on failure.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            log_message(f"Experienced error during execution of {func.__name__}: '{str(e)}'", "ERROR")

            error_index = 1
            while True:
                screenshot_path = os.path.join(SCREENSHOTS_FOLDER, f"{func.__name__}_error_{error_index}.png")
                if not os.path.exists(screenshot_path):
                    break
                error_index += 1

            log_message(f"Screenshot being output at {screenshot_path}", "INFO")
            self.driver.screenshot(filename=screenshot_path)

            self.driver.reload_page()
            raise e

    return wrapper
