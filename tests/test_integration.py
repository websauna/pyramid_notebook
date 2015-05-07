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



def test_add_context_variables(web_server, browser):
    """See that we get custom templates through IPython Notebook"""

    b = browser
    b.visit("http://username:password@localhost:{}/shell2".format(web_server["port"]))

    time.sleep(3)
    assert b.is_text_present("a - varible a")

    # Type in a sample equation suing predefined variable

    b.find_by_css(".input").click()
    import ipdb ; ipdb.set_trace()
    b.find_by_css("#notebook").send_keys(Keys.ENTER)

    # ActionChains(b).send_keys(Keys.ENTER).perform()
    import ipdb ; ipdb.set_trace()git
    b.find_by_css("textarea").type('print("Output of a is ", a + 1')

    for c in 'print("Output of a is ", a + 1':
        e =  b.find_by_css(".code_cell")
        ActionChains(e).send_keys(c).perform()
        time.sleep(0.05)

    ActionChains(b).key_down(Keys.ALT).send_keys(Keys.ENTER).key_up(Keys.ALT).perform()
    time.sleep(3)

    # Back to the home
    b.find_by_css_class("#pyramid_notebook_shutdown").click()
    time.sleep(3)
    assert b.is_text_present("pyramid_notebook test application")



