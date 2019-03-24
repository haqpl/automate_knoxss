# Quick start

1. Install firefox-developer

https://download.mozilla.org/?product=firefox-devedition-latest-ssl&os=linux64&lang=pl

2. pip install selenium

3. Download geckodriver

https://github.com/mozilla/geckodriver/releases

4. Download XPI with Knoxss

http://knoxss.me

5. Edit hardcoded paths in script.

### Important
6. You have to have cookies.pkl file with session cookies from knoxss.me:

```
import pickle
import selenium.webdriver 

driver = selenium.webdriver.Firefox()
driver.get("http://knoxss.me")
pickle.dump( driver.get_cookies() , open("cookies.pkl","wb"))
