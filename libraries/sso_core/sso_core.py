import contextlib
from datetime import timedelta

import pyotp
from RPA.Browser.Selenium import Selenium


class SSOCore:
    def __init__(self, browser: Selenium, okta_credentials: dict):
        """
        This function initializes the class with the browser, the credentials, and the TOTP key

        Args:
          browser (Selenium): Selenium - the browser that you're using to access Okta.
          okta_credentials (dict): a dictionary containing the following keys:
        """
        self.login = okta_credentials["login"]
        self.password = okta_credentials["password"]
        self.driver = browser
        self.url = okta_credentials["url"]
        self.totp_generator = pyotp.TOTP(okta_credentials["TOTP Key"])

    def login_through_okta(self):
        """
        It waits until the page is loaded, then it inputs the login and password, then it waits until the page is loaded
        again
        """
        self.driver.wait_until_location_contains("thoughtfulautomation.okta.com/login")

        input_login = "id:okta-signin-username"
        self.driver.wait_until_element_is_visible(input_login)
        self.driver.input_text(input_login, self.login)
        self.driver.click_element("id:okta-signin-submit")
        try:
            self.driver.wait_until_element_is_visible("password")
            self.driver.input_text("password", self.password)
            self.driver.click_element('//input[@value="Verify"]')
            self.driver.wait_until_location_does_not_contain("thoughtfulautomation.okta.com")
        except AssertionError:
            input_otp = '//div[contains(.,"Enter Code")]/div/span/input'
            self.driver.wait_until_element_is_visible(input_otp)
            self.driver.input_text(input_otp, self.totp_generator.now())
            submit_verify = '//input[@value="Verify"]'
            with contextlib.suppress(AssertionError):
                self.driver.wait_until_element_is_enabled(submit_verify)
                self.driver.click_element(submit_verify)

    def login_to_okta_app(self, app_name: str, app_landing_location: str) -> None:
        """
        This function opens a browser, logs into Okta, clicks on the app link, and waits until the app landing page is
        loaded

        Args:
          app_name (str): The name of the app you want to login to.
          app_landing_location (str): The URL that the app should land on after logging in.
        """
        self.driver.open_chrome_browser(self.url, preferences={"--disable-notifications": True})
        self.driver.maximize_browser_window()

        self.login_through_okta()

        app_link = f'//div[@data-se="app-card-container"]/a[contains(@href, "{app_name}")]'
        self.driver.wait_until_element_is_visible(app_link, timeout=timedelta(seconds=30))
        app_location = self.driver.get_element_attribute(app_link, "href")
        self.driver.go_to(app_location)

        self.driver.wait_until_location_contains(app_landing_location, timeout=timedelta(seconds=30))
