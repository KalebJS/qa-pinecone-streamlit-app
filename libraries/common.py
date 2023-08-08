import datetime
import os
import shutil
import time
from contextlib import suppress
from functools import wraps

from libraries.sso_core import BadRequestException


def get_downloaded_file_path(path_to_temp: str, extension: str, error_message: str = "") -> str:
    downloaded_files = []
    timer = datetime.datetime.now() + datetime.timedelta(0, 60 * 1)

    while timer > datetime.datetime.now():
        time.sleep(1)
        downloaded_files = [f for f in os.listdir(path_to_temp) if os.path.isfile(os.path.join(path_to_temp, f))]
        if downloaded_files and downloaded_files[0].endswith(extension):
            time.sleep(1)
            break
    if len(downloaded_files) == 0:
        if error_message:
            raise IOError(error_message)
        return ""
    return os.path.join(path_to_temp, downloaded_files[0])


def print_version():
    try:
        file = open("VERSION")
        try:
            print(f"Version {file.read().strip()}")
        except Exception as ex:
            print(f"Error reading VERSION file. {str(ex)}")
        finally:
            file.close()
    except Exception as e:
        print(f"VERSION file not found. {str(e)}")


def create_or_clean_dir(folder_path: str):
    shutil.rmtree(folder_path, ignore_errors=True)
    with suppress(FileExistsError):
        os.mkdir(folder_path)


def retry_on_bad_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        error = None
        for _ in range(3):
            try:
                return func(*args, **kwargs)
            except BadRequestException as e:
                error = e
                print(f"Received bad response ({error.status_code}): [{error.message}]. Retrying in 30 seconds...")
                time.sleep(30)
        raise error

    return wrapper
