import os
import platform
import logging
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException


class SeleniumLoader:
    def __init__(
        self,
        driver_path: Optional[str] = None,
        user_options: Optional[webdriver.ChromeOptions] = None,
    ):
        self._get_driver_path()
        if driver_path is None:
            self.driver_path = os.path.join(os.getcwd(), self.driver_filename)
        else:
            self.driver_path = driver_path

        self._init_driver(user_options)
        self._version_checker()

    def _get_driver_path(self):
        current_os = platform.system()

        driver_filename = "chromedriver"
        if current_os == "Linux":
            zip_filename = "chromedriver_linux64.zip"
        elif current_os == "Darwin":
            machine = platform.machine()
            if machine == "x86_64":
                zip_filename = "chromedriver_mac64.zip"
            elif machine == "arm64":
                zip_filename = "chromedriver_mac64_m1.zip"
        elif current_os == "Windows":
            zip_filename = "chromedriver_win32.zip"
            driver_filename = "chromedriver.exe"

        self.zip_filename = zip_filename
        self.driver_filename = driver_filename

    def _init_driver(self, options: Optional[webdriver.ChromeOptions] = None):

        if options is None:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("window-size=1920,1280")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/78.0.3904.108 Safari/537.36"
            )
            options.add_argument("lang=ko_KR")
            options.add_argument("log-level=3")
            options.add_experimental_option(
                "excludeSwitches", ["enable-logging"]
            )

        webdriverpath = os.path.join(self.driver_path)

        self.user_options = options
        try:
            self.driver = webdriver.Chrome(webdriverpath, options=options)
        except WebDriverException:
            logging.warning(
                "No chromedriver executable found. "
                "Download latest version of the driver."
            )
            self._download_chromedriver()
            self.driver = webdriver.Chrome(webdriverpath, options=options)

    def _version_checker(self):
        chrome_version = self.driver.capabilities["browserVersion"][0:4]
        driver_version = self.driver.capabilities["chrome"][
            "chromedriverVersion"
        ].split(" ")[0][0:4]
        if chrome_version != driver_version:
            logging.warning(
                "Chromedriver is outdated. "
                "Download latest version of the driver:"
                "Chrome version: %(chrome_version)s, "
                "Driver version: %(driver_version)s",
                {
                    "chrome_version": chrome_version,
                    "driver_version": driver_version,
                },
            )

            self._download_chromedriver()
            self._init_driver(self.user_options)

    def _download_chromedriver(self):
        import stat
        import zipfile
        import shutil

        import requests

        logging.info("Download chromedriver")
        chromedriver_version_api = (
            "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
        )
        response = requests.get(chromedriver_version_api)
        latest_version = response.text

        chromedriver_url = (
            "https://chromedriver.storage.googleapis.com/"
            f"{latest_version}/{self.zip_filename}"
        )
        with requests.get(chromedriver_url, stream=True) as res:
            with open(self.zip_filename, 'wb+') as file:
                shutil.copyfileobj(res.raw, file)

        with zipfile.ZipFile(self.zip_filename, "r") as file:
            file.extractall(os.getcwd())

        os.chmod(
            self.driver_filename, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        os.remove(self.zip_filename)
