import pickle
import os
import sys
from pathlib import Path
from collections import defaultdict

from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException


CLICK_MACROS = {
}

TARGET_MACROS = {
}


class Spider:
    def __init__(self, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--headless")

        try:
            driver = webdriver.Chrome(options=chrome_options)
        except WebDriverException:
            print("chromedriver' executable needs to be in PATH. "
                  "Please see https://sites.google.com/a/chromium.org/chromedriver/home")
            decision = input('add bundled chromedriver to path? y/[n]')
            if decision not in ['y', 'n'] or decision == 'n':
                sys.exit(1)
            else:
                dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
                sys.path.insert(0, dir_path / 'chromedriver.exe')
                print('Warning: supplied chromedriver is intended for Windows and Chrome version 83.')

        self.driver = driver

    def get_current_html(self, url, clicks, target):
        # load page
        self.driver.get(url)

        # perform actions
        for click in clicks:
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, click))
                )
            except Exception:
                return None
            element.click()

        # get html
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, target))
        )

        # more accurate, but problematic due to js content etc.
        # html = element.get_attribute('innerHTML')

        # more reliable:
        html = element.text

        return html

    def __del__(self):
        self.driver.close()


def parse_pings(ping_file):

    pings = []

    with open(ping_file)as inf:
        for line in inf.readlines():
            if line.strip() == '':
                continue
            url, actions, target = [x.strip() for x in line.split('|')]
            if actions.startswith('#'):
                actions = CLICK_MACROS[actions]
            elif actions == '':
                actions = []
            else:
                # split actions
                actions = actions.split(';')
            if target.startswith('#'):
                target = TARGET_MACROS[target]

            ping = (url, actions, target)
            pings.append(ping)

    return pings


def main():
    # read pings
    pings = parse_pings('./pings.txt')

    previous_htmls = defaultdict(lambda: '')

    # read previous htmls
    if os.path.isfile('./previous.pickle'):
        with open('./previous.pickle', 'rb') as inf:
            previous_htmls.update(pickle.load(inf))

    spider = Spider(headless=True)

    for url, clicks, target in tqdm(pings):

        current = spider.get_current_html(url, clicks, target)
        if current is None:
            print(f'Retrieving html failed for: {url}')
        elif current != previous_htmls[url]:
            print(f'Updated: {url}')
            previous_htmls[url] = current

    # write current htmls as new previous
    with open('./previous.pickle', 'wb') as out:
        pickle.dump(dict(previous_htmls), out)


if __name__ == '__main__':
    # execute only if run as the entry point into the program
    main()
