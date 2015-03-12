#!/usr/bin/env python3

import unittest
import os

import selenium.webdriver

address = "http://mpcv.bat/"

class UploadingCVTestCase(unittest.TestCase):

    def setUp(self):
        self.browser = selenium.webdriver.Firefox()
        #self.addCleanup(self.browser.quit)

    def testUploadCV(self):
        self.browser.get(address + "upload_cv/7777777")

        self.assertIn('We need to confirm your email first', self.browser.page_source)
        self.assertIn('Hi, Sicnarf Gnivri', self.browser.page_source)

        self.browser.find_element_by_id('confirm_email').click()
        self.assertIn('Check your email!', self.browser.page_source)

        url = open('last_confirm_url.txt', 'r').read()
        print("last_confirm_url: ", url);
        self.browser.get(url)
        self.assertIn('Choose a Word document or PDF', self.browser.page_source)

        doc_full_path = os.path.abspath('fixtures/Example MP candidate CV.doc')
        self.browser.find_element_by_css_selector('.files').send_keys(doc_full_path)

        self.assertIn('Your CV has been successfully uploaded', self.browser.page_source)

if __name__ == '__main__':
    unittest.main()


