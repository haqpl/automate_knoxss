# Quick start

1. Install firefox-developer

https://download.mozilla.org/?product=firefox-devedition-latest-ssl&os=linux64&lang=pl

2. `pip install selenium --user` # requires Python

3. Download geckodriver, it should be placed in /usr/bin or add it to PATH

https://github.com/mozilla/geckodriver/releases

4. Download XPI with KNOXSS Pro

http://knoxss.me

### Important
6. Login to http://knoxss.me and retrieve session Cookies, pass them to -c argument.

## Parameters:

1. `-u` or `--url` - defines the target for the scan
2. `-c` or `--cookies` - defines the session Cookies for logged in user to KNOXSS service
3. `-f` or `--firefox` - defines the location of Firefox Developer edition binary
4. `-a` or `--addon` - defines the location of KNOXSS extension directory, unzipped and modified
5. `-t` or `--timeout` - defines the timout for event

### Example usage:

`python3 automate_knoxss.py -u "https://target" -c "wordpress_logged_in_...=...; wordpress_sec_...=...; sucuri_cloudproxy_uuid_...=...; wordpress_test_cookie=WP+Cookie+check;" -f /home/firefox/firefox -a knoxss -t 90`
