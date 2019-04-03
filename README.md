# Quick start

1. Install firefox-developer

https://download.mozilla.org/?product=firefox-devedition-latest-ssl&os=linux64&lang=pl

2. `pip install selenium --user` # requires Python

3. Download geckodriver

https://github.com/mozilla/geckodriver/releases

4. Download XPI with KNOXSS Pro

http://knoxss.me

### Important
6. Login to http://knoxss.me and retrieve session Cookies, pass them to -c argument.

### Example usage:

`python3 automate_knoxss.py -u "https://target" -c "wordpress_logged_in_...=...; wordpress_sec_...=...; sucuri_cloudproxy_uuid_...=...; wordpress_test_cookie=WP+Cookie+check;" -f /home/mp/firefox/firefox -a knoxss -t 90`
