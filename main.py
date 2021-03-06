import argparse
import datetime
import pickle
import os
import sys
from pathlib import Path
import platform
from collections import defaultdict


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from tqdm import tqdm
from win10toast import ToastNotifier


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
            chrome_options.add_argument("--silent")
            chrome_options.add_argument("--log-level=3")

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

    def get_current_html(self, url, clicks, target, html_or_content='content'):
        # load page
        self.driver.get(url)

        # perform actions
        for click in clicks:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, click))
            )
            element.click()

        # get html
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, target))
        )

        if html_or_content == 'html':
            # more accurate, but problematic due to js content etc.
            html = element.get_attribute('innerHTML')
        else:
            # more reliable:
            html = element.text

        return html

    def __del__(self):
        self.driver.close()


def parse_pings(ping_file):

    pings = []

    with open(ping_file)as inf:
        for line in inf.readlines():
            if line.strip() == '' or line.startswith('#'):
                continue
            url, actions, target, triggers = [x.strip() for x in line.split('|')]
            triggers = triggers.split(';')
            triggers = [x.strip() for x in triggers]

            if actions.startswith('#'):
                actions = CLICK_MACROS[actions]
            elif actions == '':
                actions = []
            else:
                # split actions
                actions = actions.split(';')
            if target.startswith('#'):
                target = TARGET_MACROS[target]
            elif target == '':
                target = '//body'

            ping = (url, actions, target, triggers)
            pings.append(ping)

    return pings


def main():
    # parse args
    parser = argparse.ArgumentParser(description='Crawl a number of sites and compare them to a previous known state.')
    parser.add_argument('--show_driver', action='store_true', default=False, help='Disables headless mode for webdriver.')
    parser.add_argument('--no_notify', action='store_true', default=False, help='Disable toast notifications.')
    parser.add_argument('--html_or_content', choices=['html', 'content'], default='content', help='Whether to compare html or content.')
    args = parser.parse_args()

    # read pings
    pings = parse_pings('./pings.txt')

    previous_htmls = defaultdict(lambda: {
        'time': None,
        'html': ''
    })

    # read previous htmls
    if os.path.isfile('./previous.pickle'):
        with open('./previous.pickle', 'rb') as inf:
            previous_htmls.update(pickle.load(inf))

    # store new htmls separately in order to discard no longer tracked sites
    new_previous_htmls = defaultdict(lambda: {
        'time': None,
        'html': ''
    })

    spider = Spider(headless=(not args.show_driver))

    stuff_changed = False
    changes = []
    for url, clicks, target, triggers in tqdm(pings):
        try:
            current_content = spider.get_current_html(url, clicks, target, args.html_or_content)
        except Exception:
            tqdm.write(f'Retrieving html failed for: {url}')

        # do nothing if not of the given triggers are fired
        if len(triggers) > 0 and not any([x in current_content for x in triggers]):
            continue

        # store "new previous"
        new_previous_htmls[url]['html'] = current_content
        new_previous_htmls[url]['time'] = datetime.datetime.now()

        if previous_htmls[url]['html'] is not None \
            and current_content is not None \
            and current_content != previous_htmls[url]['html']:
            tqdm.write(f'Changed: {url}')

            stuff_changed = True

            # save differences
            changes.append({
                'url': url,
                'previous_time': previous_htmls[url]['time'],
                'previous_html': ' '.join(previous_htmls[url]['html'].split()),
                'current_time': datetime.datetime.now(),
                'current_html': ' '.join(current_content.split())
            })

    # write change report
    with open('./updates.log', 'a+', encoding='utf-8') as out:
        for change in changes:
            out.write(f'{change["current_time"]}, URL {change["url"]}\n')
            out.write(f'\tBefore:\t{change["previous_html"]}\n')
            out.write(f'\tAfter:\t {change["current_html"]}\n')
            out.write('----------------------------------------------\n')

    if not args.no_notify and stuff_changed and platform.system() == 'Windows':
        # create an object to ToastNotifier class
        n = ToastNotifier()
        n.show_toast("ProjectPing", f"{len(changes)} change(s) detected. Check log for details.", duration=5,
                     icon_path="./assets/spider.ico")

    # write current htmls as new previous
    with open('./previous.pickle', 'wb') as out:
        pickle.dump(dict(new_previous_htmls), out)


if __name__ == '__main__':
    # execute only if run as the entry point into the program
    main()
