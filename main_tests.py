#!/usr/bin/env python3

import os
import unittest
import coverage

cov = coverage.coverage(branch = True, omit=["^/*", "main_tests.py"], include=["[a-z_]*.py"])
cov.start()

os.environ['MPCV_SECRET_KEY'] = 'doesnotmatterastesting'
os.environ['MPCV_DEBUG_EMAIL'] = 'test@localhost'
os.environ['MPCV_TESTING'] = 'True'

import main

class MainTestCase(unittest.TestCase):

    def setUp(self):
        self.app = main.app.test_client()

    def tearDown(self):
        pass


    def test_home(self):
        r = self.app.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('To apply, please send your CV', r.get_data(True))
        self.assertIn('<form action="/set_postcode" method="GET">', r.get_data(True))
        self.assertIn('Debug email enabled', r.get_data(True))

    def test_postcode(self):
        r = self.app.get('/set_postcode?postcode=ZZ99ZZ', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Candidates for job of MP', r.get_data(True))
        self.assertIn('Democracy Club Test Constituency', r.get_data(True))
        self.assertIn('Sicnarf Gnivri', r.get_data(True))
        self.assertIn('<a href="/upload_cv/7777777">This is me, add my CV</a>', r.get_data(True))

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

    def test_bad_postcode(self):
        r = self.app.get('/set_postcode?postcode=moo', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('To apply, please send your CV', r.get_data(True))
        self.assertIn("Postcode &#39;MOO&#39; is not valid.", r.get_data(True))

    def test_upload_cv_index(self):
        r = self.app.get('/upload_cv/7777777')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Hi, Sicnarf Gnivri!', r.get_data(True))
        self.assertIn('<form action="/upload_cv/7777777" method="POST">', r.get_data(True))
        self.assertIn('<button type="submit" class="btn btn-default">Confirm email</button>', r.get_data(True))
        self.assertIn('frabcus@fastmail.fm', r.get_data(True))

    def test_upload_cv_send_email(self):
        with main.mail.record_messages() as outbox:
            r = self.app.post('/upload_cv/7777777')
            self.assertEqual(r.status_code, 200)
            self.assertIn('Check your email!', r.get_data(True))
            self.assertEqual(len(outbox), 1)
            self.assertEqual( outbox[0].subject, "Upload your CV for becoming an MP")
            self.assertEqual( outbox[0].recipients, [('Sicnarf Gnivri', 'test@localhost')])
            self.assertEqual( outbox[0].sender, "Democracy Club CVs <cv@democracyclub.org.uk>")


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        cov.stop()
        cov.html_report(directory='covhtml')


