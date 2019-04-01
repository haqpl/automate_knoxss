import json
import pickle
import time
import sys
import getopt
import signal
import os
import queue

from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import AddonFormatError, FirefoxProfile
from http.cookies import SimpleCookie

bad_extensions = ['.svg', '.jpg', '.zip', '.rar', '.gif', '.jpeg', '.png', '.xml']

def usage():
    print("Automation of KNOXSS extension v. 0.1")
    print("Copyright Maciej Piechota @haqpl 2019")
    print("Usage: automate_knoxss.py -u URL -c COOKIES -f PATH_TO_FIREFOX_BIN -a PATH_TO_ADDON_DIR")
    sys.exit()

def signal_handler(sig, frame):
    global driver
    print('[+] Cleaning up!')
    driver.quit()
    sys.exit(0)

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

class CheckableQueue(queue.Queue):
    def __contains__(self, item):
        with self.mutex:
            return item in self.queue
    def __len__(self):
        return self.qsize()

def page_has_loaded():
    print("[+] Checking if {} page has loaded.".format(driver.current_url))
    page_state = driver.execute_script('return document.readyState;')
    return page_state == 'complete'

def parse_cookies(cookies):
    cookie = SimpleCookie()
    cookie.load(cookies)
    cook = []
    for key, morsel in cookie.items():
        cook.append({'name': str(key), 'value': str(morsel.value), 'domain': 'knoxss.me'})
    return cook

def find_hrefs(hrefs):
    global driver
    global visited_urls
    links = driver.find_elements_by_xpath("//a[@href]")
    for elem in links:
        elem_url = elem.get_attribute("href")
        current_url = urlparse(driver.current_url)
        if (current_url.scheme+"://"+current_url.netloc in elem_url) and (elem_url not in hrefs) and (elem_url[-4:] not in bad_extensions) and (elem_url not in dict(visited_urls)):
            print("[+] Found new URL: {}".format(elem.get_attribute("href")))
            hrefs.put(elem.get_attribute("href"))
    return hrefs


def main():
    global driver
    global visited_urls
    time_to_wait = 90       #timeout for KNOXSS event
    visited = 0         
    knoxss_status = None
    cookies = False
    url = False
    firefox_binary = False  #location of Firefox developer edition
    addon = False           #location of unzipped KNOXSS add-on
    active = False
    elapsed_time = 0
    visited_urls = []

    if not len(sys.argv[1:]):
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:c:f:a:", ["help", "url", "cookies", "firefox", "addon"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
            print('Example usage: python automate_knoxss.py -u "http://target" -c cookies.pkl -f /usr/bin/firefox -a knoxss')
        elif o in ("-u", "--url"):
            url = str(a)
        elif o in ("-c", "--cookies"):
            cookies = str(a)
        elif o in ("-f", "--firefox"):
            firefox_binary = str(a)
        elif o in ("-a", "--addon"):
            addon = str(a)
        else:
            assert False, "Bad options"
    
    if not url or not cookies or not firefox_binary or not addon: 
        usage()
        sys.exit()

    signal.signal(signal.SIGINT, signal_handler)
    print("[+] Starting Web driver...")
    
    try:
        profile = FirefoxProfileWithWebExtensionSupport()
        profile.add_extension(addon)

        driver = webdriver.Firefox(firefox_profile=profile,
                                firefox_binary=firefox_binary)
    except Exception as err:
        sys.stderr.write('[-] ERROR running Webdriver: %s' % str(err))
        if driver:
            signal_handler(None, None)
        sys.exit()

    print("[+] Loading Cookies")

    try:
        driver.get('https://knoxss.me')
        for cookie in parse_cookies(cookies):
            driver.add_cookie(cookie)
    except Exception as err:
        sys.stderr.write('[-] ERROR loading Cookies, check Internet connection or Cookies format: %s' % str(err))
        if driver:
            signal_handler(None, None)
        sys.exit()

    time.sleep(30)
    print("[+] Navigating to {}".format(url))
    driver.get(url)
    driver.execute_script("window.knoxss_status = []; document.addEventListener(\"knoxss_status\", function(e){window.knoxss_status.push(e.detail); e.stopPropagation();}, true);")
    
    web_hrefs = CheckableQueue()
    web_hrefs = find_hrefs(web_hrefs)

    try:
        while True:
            knoxss_status = driver.execute_script("return window.knoxss_status.pop()")
            if knoxss_status is not None:
                elapsed_time = 0
                if "Nothing found" in str(knoxss_status) :
                    print('[+] Nothing found: {}'.format(knoxss_status))
                elif "XSS" in str(knoxss_status):
                    print('[+] FOUND XSS: {}'.format(knoxss_status))
                elif "ACTIVATED" in str(knoxss_status):
                    print('[+] KNOXSS activated: {}'.format(knoxss_status))
                    knoxss_status = None
                    active = True
                    continue
                elif "deactivated" in str(knoxss_status):
                    print('[+] KNOXSS deactivated: {}'.format(knoxss_status))
                    knoxss_status = None
                    active = False
                    continue
                else:
                    raise RuntimeError('Uknown error: %s Aborting!' % str(knoxss_status))
            else:
                if active:
                    print("[+] Waiting for KNOXSS event, timeout: {}/{}".format(str(elapsed_time), str(time_to_wait)))
                else:
                    print("[+] Enable KNOXSS add-on, timeout: {}/{}".format(str(elapsed_time), str(time_to_wait)))
                elapsed_time += 0.5
                if elapsed_time > 0:
                    spent_time = elapsed_time
                time.sleep(0.5)
                if elapsed_time > time_to_wait:
                    raise RuntimeError('There is no event from KNOXSS. Check Cookies status or adjust timeout. Aborting!')
            if active and knoxss_status is not None:
                if len(web_hrefs) == 0:
                    break
                link = web_hrefs.get()
                print("[+] Navigating: {}".format(link))
                driver.get(link)
                visited_urls.append((link, knoxss_status))
                visited += 1
                if page_has_loaded():
                    driver.execute_script("window.knoxss_status = []; document.addEventListener(\"knoxss_status\", function(e){window.knoxss_status.push(e.detail);}, false);")
                    web_hrefs = find_hrefs(web_hrefs)
                progress = len(web_hrefs)*spent_time
                print("[+] Remaining: {} minutes, visited/all_urls: {}/{}".format(progress / 60, visited, len(web_hrefs)+len(visited_urls)))
    except RuntimeError as err:
        sys.stderr.write('[-] ERROR spidering: %s' % str(err)) 
        signal_handler(None, None)
    except Exception as err:
        sys.stderr.write('[-] Uknown ERROR. Proceeding : %s' % str(err))
        pass
    finally:
        signal_handler(None, None)

if __name__ == '__main__':
    main()
