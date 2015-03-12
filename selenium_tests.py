#!/usr/bin/env python3

import selenium.webdriver
import unittest

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

        self.assertIn('Drop your CV in here', self.browser.page_source)

        # XXX this doesn't work
        print("send_keys")
        self.browser.find_element_by_id('fileupload').send_keys('fixtures/Example MP candidate CV.doc')
        #self.browser.find_element_by_id('fileupload').click()

        #self.assertIn('Your CV has been successfully uploaded', self.browser.page_source)

if __name__ == '__main__':
    unittest.main()


