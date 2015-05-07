"""Make sure scheisse holds on the wall."""
import logging
import os
import time
import random

from pyramid_notebook.notebookmanager import NotebookManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

NOTEBOOK_FOLDER = os.path.join("/tmp", "pyramid_notebook_tests")
os.makedirs(NOTEBOOK_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.DEBUG)

USER = "test{}".format(random.randint(0, 1000))


def test_notebook_template(web_server, browser):
    """See that we get custom templates through IPython Notebook"""

    b = browser
    browser.visit("http://localhost:{}/".format(web_server["port"]))
    assert b.is_text_present("pyramid_notebook test application")

    browser.visit("http://username:password@localhost:{}/shell1".format(web_server["port"]))
    time.sleep(3)
    assert b.find_by_css("#pyramid_notebook_logo")

    # Back to the home
    b.find_by_css("#pyramid_notebook_shutdown").click()
    time.sleep(3)
    assert b.is_text_present("pyramid_notebook test application")


def hacker_typing(browser, spinter_selection, code):
    """We need to break Splinter abstraction and fall back to raw Selenium here.

    Note: There is a bug of entering parenthesis due to IPython capturing keyboard input.
    """
    elem = spinter_selection[0]._element
    driver = browser.driver

    # Activate IPython input mode
    ActionChains(driver).click(elem).send_keys(Keys.ENTER).perform()

    # Tyoe int he code
    a = ActionChains(driver)
    a.send_keys(code)
    a.key_down(Keys.ALT).send_keys(Keys.ENTER).key_up(Keys.ALT)
    a.perform()


def test_add_context_variables(web_server, browser):
    """We can perform meaningful calculations on variables set in startup.py"""

    b = browser
    b.visit("http://username:password@localhost:{}/shell2".format(web_server["port"]))

    time.sleep(1)
    assert b.is_text_present("a - varible a")

    # Type in a sample equation suing predefined variable
    hacker_typing(b, b.find_by_css(".code_cell"), 'print("Output of a + b is", a + b)')

    assert b.is_text_present("Output of a + b is foobar")

    # Back to the home
    b.find_by_css("#pyramid_notebook_shutdown").click()

    # There should be alert "Do you really wish to leave notebook?"
    alert = b.driver.switch_to_alert()
    alert.accept()

    time.sleep(1)
    assert b.is_text_present("pyramid_notebook test application")



