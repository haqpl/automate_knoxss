import json
import pickle
import time
import sys
import getopt
import signal
import os

from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import AddonFormatError, FirefoxProfile

bad_extensions = ['.svg', '.jpg', '.zip', '.rar', '.gif', '.jpeg', '.png', '.xml']

def usage():
    print("Automation of KNOXSS extension v. 0.1")
    print("Copyright Maciej Piechota @haqpl 2019")
    print("Usage: automate_knoxss.py -u URL -c COOKIES -f PATH_TO_FIREFOX_BIN -a PATH_TO_ADDON_DIR")
    sys.exit()

def signal_handler(sig, frame):
    global driver
    print('[+] Ctrl+C, cleaning up!')
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


def page_has_loaded(driver):
    print("[+] Checking if {} page has loaded.".format(driver.current_url))
    page_state = driver.execute_script('return document.readyState;')
    return page_state == 'complete'


def find_urls(driver, hrefs):
    links = driver.find_elements_by_xpath("//a[@href]")
    for elem in links:
        elem_url = elem.get_attribute("href")
        current_url = urlparse(driver.current_url)
        if (current_url.netloc in elem_url) and (elem_url not in hrefs) and (elem_url[-4:] not in bad_extensions):
            print("[+] Found new URL: {}".format(elem.get_attribute("href")))
            hrefs.append(elem.get_attribute("href"))
    return hrefs


def main():
    global driver
    time_to_wait = 90   #timeout for knoxss event
    clicked = 0         
    text = ""
    cookies = False
    url = False
    firefox_binary = '/home/mp/firefox/firefox'
    addon = False
    active = False

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

    print("[+] Starting Webdriver...")
    
    try:
        profile = FirefoxProfileWithWebExtensionSupport()
        profile.add_extension(addon)

        driver = webdriver.Firefox(firefox_profile=profile,
                                firefox_binary=firefox_binary)
        signal.signal(signal.SIGINT, signal_handler)
    except Exception as err:
        sys.stderr.write('[-] ERROR running Webdriver: %s' % str(err))
        sys.exit()

    driver.get('https://knoxss.me')
    
    try:
        cookies = pickle.load(open(cookies, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
    except Exception as err:
        sys.stderr.write('[-] ERROR loading cookies: %s' % str(err))
        sys.exit()

    print("[+] Navigating to {}".format(url))
    driver.get(url)
    #driver.execute_script("document.addEventListener(\"knoxss_status\", function(e){window.knoxss_status = e.detail}, false);")
    
    hrefs = []
    hrefs = find_urls(driver, hrefs)
    hrefs.insert(0, url)

    try:
        for link in hrefs:
            elapsed_time = 0
            hrefs = find_urls(driver, hrefs)
            driver.execute_script("document.addEventListener(\"knoxss_status\", function(e){window.knoxss_status = e.detail}, false);")
            while True:
                text = driver.execute_script("return window.knoxss_status")
                if text is not None:
                    if "Nothing found" in str(text) :
                        print('[+] Nothing found: {}'.format(text))
                        break
                    elif "XSS" in str(text):
                        print('[+] FOUND XSS: {}'.format(text))
                        break
                    elif "ACTIVATED" in str(text):
                        if active:
                            break
                        print('[+] KNOXSS on/off: {}'.format(text))
                        active = True
                    else:
                        raise RuntimeError('Uknown error: %s Aborting!' % str(text))
                else:
                    print("[+] Waiting for KNOXSS event, timeout: {}/{}".format(str(elapsed_time), str(time_to_wait)))
                    elapsed_time += 0.5
                    time.sleep(0.5)
                    if elapsed_time > time_to_wait:
                        raise RuntimeError('There is no event from KNOXSS. Check Cookies status. Aborting!')
            print("[+] Navigating: {}".format(link))
            driver.get(link)
            clicked += 1
            progress = len(hrefs)*elapsed_time
            print("[+] Remaining: {} minutes, clicked/all_urls: {}/{}".format(progress / 60, clicked, len(hrefs)))
    except RuntimeError as err:
        sys.stderr.write('[-] ERROR spidering: %s' % str(err)) 
        driver.quit()
        sys.exit()
    except Exception as err:
        sys.stderr.write('[-] Uknown ERROR. Proceeding : %s' % str(err))
        pass
    finally:
        print("[+] Cleaning up")
        driver.quit()

if __name__ == '__main__':
    main()
