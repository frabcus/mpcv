#!/usr/bin/env python3

# Integration tests in Selenium. No need to cover everything in this - just
# main workflows, and anything javascript intensive (such as file upload).

import unittest
import os
import sys

import selenium.webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class UploadingCVTestCase(unittest.TestCase):

    def setUp(self):
        self.browser = selenium.webdriver.Firefox()
        self.addCleanup(self.browser.quit)
        self.browser.implicitly_wait(3)
        self.wait = WebDriverWait(self.browser, 10)

    def testPostcodeLookup(self):
        self.browser.get(address)
        self.assertIn('Before you vote, look at their CVs!', self.browser.page_source)
        self.assertIn('Debug email enabled', self.browser.page_source)

        self.browser.find_element_by_id('postcode').send_keys('zz99zz')
        self.browser.find_element_by_id('postcode').submit()

        self.assertIn('Democracy Club Test Constituency', self.browser.page_source)
        self.assertIn('Sicnarf Gnivri', self.browser.page_source)
        self.assertIn('Notlits Esuom', self.browser.page_source)
        self.assertIn('Ojom Yeknom', self.browser.page_source)

        # make sure constituency remembered, and front page redirects back to constituency page
        self.browser.get(address)
        self.assertIn('Before you vote, look at their CVs!', self.browser.page_source)
        self.assertIn('My constituency', self.browser.page_source)

        # "Change constituency" clears the memory of constituency
        self.browser.find_element_by_link_text("My constituency").click()
        self.assertIn('Democracy Club Test Constituency', self.browser.page_source)

    def testUploadCV(self):
        self.browser.get(address + "upload_cv/7777777")
        self.assertIn('I am Sicnarf Gnivri', self.browser.page_source)

        self.browser.find_element_by_id('confirm_email').click()
        self.assertIn('Check your email!', self.browser.page_source)

        with open('last_confirm_url.txt', 'r') as o:
            url = o.read()
        self.browser.get(url)
        self.assertIn('Choose a new CV to replace', self.browser.page_source)

        doc_full_path = os.path.abspath('fixtures/Example MP candidate CV.doc')
        self.browser.find_element_by_css_selector('.files').send_keys(doc_full_path)
        self.wait.until(EC.title_contains("About"))

        self.assertIn('Your CV has been successfully uploaded', self.browser.page_source)
        self.assertNotIn("alert-danger", self.browser.page_source)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Give URL of mpcv instance to test as first parameter.")
        sys.exit(1)
    address = sys.argv.pop()
    unittest.main(warnings='ignore')


