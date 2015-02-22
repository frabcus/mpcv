#!/usr/bin/env python3

import os
import unittest

import main

class MainTestCase(unittest.TestCase):

    def setUp(self):
        main.app.config['TESTING'] = True
        self.app = main.app.test_client()

    def tearDown(self):
        pass


    def test_home(self):
        r = self.app.get('/')
        assert 'To apply, please send your CV' in r.data.decode('utf-8')

if __name__ == '__main__':
    unittest.main()
