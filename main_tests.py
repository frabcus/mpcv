#!/usr/bin/env python3

import os
import unittest

os.environ['MPCV_SESSION_SECRET'] = 'doesnotmatterastesting'

import main

class MainTestCase(unittest.TestCase):

    def setUp(self):
        main.app.config['TESTING'] = True
        self.app = main.app.test_client()

    def tearDown(self):
        pass


    def test_home(self):
        r = self.app.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('To apply, please send your CV', r.get_data(True))
        self.assertIn('<form action="/set_postcode" method="GET">', r.get_data(True))

    def test_postcode(self):
        r = self.app.get('/set_postcode?postcode=ZZ99ZZ', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Candidates for job of MP', r.get_data(True))
        self.assertIn('Democracy Club Test Constituency', r.get_data(True))
        self.assertIn('Sicnarf Gnivri', r.get_data(True))

        # make sure constituency remembered, and front page redirects back to constituency page
        r = self.app.get('/', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Candidates for job of MP', r.get_data(True))
        self.assertIn('Democracy Club Test Constituency', r.get_data(True))

        # "I live somewhere else" clears the memory of constituency
        self.assertIn('<a href="/clear_postcode">I live somewhere else</a>', r.get_data(True))
        r = self.app.get('/clear_postcode', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('To apply, please send your CV', r.get_data(True))

if __name__ == '__main__':
    unittest.main()
