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
        elem_url = elem.get_attribute("href") 
        if (driver.current_url.split("//")[-1].split("/")[0].split('?')[0] in elem_url) & (elem_url not in hrefs) & (elem_url[-4:] not in ['.svg', '.jpg', '.zip', '.rar', '.gif', '.jpeg', '.png']):
            print("Found URL: {}".format(elem.get_attribute("href")))
            hrefs.append(elem.get_attribute("href"))
    return hrefs

profile = FirefoxProfileWithWebExtensionSupport()
profile.set_preference("devtools.console.stdout.content", True)
profile.add_extension('knoxss')


firefox_binary = '/home/mp/firefox/firefox'  
driver = webdriver.Firefox(firefox_profile=profile, firefox_binary=firefox_binary)
driver.maximize_window()

driver.get('https://knoxss.me')


cookies = pickle.load(open("cookies2.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)

driver.get('https://brutelogic.com.br/knoxss.html')

print("Waiting... Enable Knoxss extension")
time.sleep(30)
print("Done...")

hrefs = []
hrefs = find_urls(hrefs)
clicked = 0
text = ""

for link in hrefs:
    elapsed_time = 0
    try:
        print("Clicking: {}".format(link))
        driver.get(link)
        clicked+=1
        hrefs = find_urls(hrefs)
        driver.execute_script("document.body.addEventListener(\"knoxss_status\", function(e){window.knoxss_status = e.detail}, false);")
        while True:
            text = driver.execute_script("return window.knoxss_status")
            if text is not None:
                if str(text) not in "Nothing found":
                    print('Got Knoxss event: {}'.format(text))
                elif str(text) not in "XSS":
                    print('FOUND XSS: {}'.format(text))
                else:
                    print('Unknown error: {}'.format(text))
                break
            else:
                print("Waiting for Knoxss event: {}".format(str(text)))
                elapsed_time += 0.5
                time.sleep(0.5)
        progress = len(hrefs)*elapsed_time
        print("Remaining: {} minutes, clicked/all_urls: {}/{}".format(progress/60, clicked, len(hrefs)))
    except:
        pass

r = input()
driver.quit()


