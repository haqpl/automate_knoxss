import json
import os
import sys
import pickle
import time

from random import randint
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import AddonFormatError, FirefoxProfile

class FirefoxProfileWithWebExtensionSupport(webdriver.FirefoxProfile):
    def _addon_details(self, addon_path):
        try:
            return super()._addon_details(addon_path)
        except AddonFormatError:
            try:
                with open(os.path.join(addon_path, 'manifest.json'), 'r') as f:
                    manifest = json.load(f)
                    return {
                        'id': manifest['applications']['gecko']['id'],
                        'version': manifest['version'],
                        'name': manifest['name'],
                        'unpack': False,
                    }
            except (IOError, KeyError) as e:
                raise AddonFormatError(str(e), sys.exc_info()[2])


def page_has_loaded():
    print("Checking if {} page is loaded.".format(driver.current_url))
    page_state = driver.execute_script('return document.readyState;')
    return page_state == 'complete'

def find_urls(hrefs):
    links = driver.find_elements_by_xpath("//a[@href]")

    for elem in links:
        #print(elem.get_attribute("href"))
        if (driver.current_url.split("//")[-1].split("/")[0].split('?')[0] in elem.get_attribute("href")) & (elem.get_attribute("href") not in hrefs):
            print("Found URL: {}".format(elem.get_attribute("href")))
            hrefs.append(elem.get_attribute("href"))
    print("Done2...")
    return hrefs

profile = FirefoxProfileWithWebExtensionSupport()
profile.add_extension('knoxss_ok')


firefox_binary = '/home/mp/firefox/firefox'  
driver = webdriver.Firefox(firefox_profile=profile, firefox_binary=firefox_binary)
driver.maximize_window()

driver.get('https://knoxss.me')


cookies = pickle.load(open("cookies.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)

driver.get('https://www.grammarly.com/')

print("Waiting...")
time.sleep(30)
print("Done...")

hrefs = []
hrefs = find_urls(hrefs)

for link in hrefs:
    try:
        print("Clicking: {}".format(link))
        driver.get(link)
        hrefs = find_urls(hrefs)
        time.sleep(randint(10, 20))
    except:
        pass

r = input()
driver.quit()
