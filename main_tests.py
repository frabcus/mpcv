#!/usr/bin/env python3

# Reasonably comprehensive Python unit tests

import os
import unittest
import coverage
import re

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
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))
        self.assertIn('<form action="/set_postcode" method="GET">', r.get_data(True))
        self.assertIn('Debug email enabled', r.get_data(True))

    def test_postcode(self):
        r = self.app.get('/set_postcode?postcode=ZZ99ZZ', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Democracy Club Test Constituency', r.get_data(True))
        self.assertIn('Sicnarf Gnivri', r.get_data(True))
        self.assertIn('href="/show_cv/7777777"', r.get_data(True))
        self.assertIn('Notlits Esuom', r.get_data(True))
        self.assertIn('href="/upload_cv/7777778"', r.get_data(True))

        # make sure constituency remembered, and front page redirects back to constituency page
        r = self.app.get('/', follow_redirects=True)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))
        self.assertIn('Your constituency', r.get_data(True))

        # "I live somewhere else" clears the memory of constituency
        self.assertIn('<a href="/candidates">Your constituency</a>', r.get_data(True))
        r = self.app.get('/candidates', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Democracy Club Test Constituency', r.get_data(True))

    def test_candidates_redirect(self):
        # When no cookie set, /candidates takes you to front page to choose postcode
        r = self.app.get('/candidates', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))

    def test_bad_postcode(self):
        r = self.app.get('/set_postcode?postcode=moo', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))
        self.assertIn("Postcode &#39;MOO&#39; is not valid.", r.get_data(True))

    def test_no_postcode(self):
        r = self.app.get('/set_postcode?postcode=', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))
        self.assertIn("Postcode is not valid.", r.get_data(True))

    def test_upload_cv_index(self):
        r = self.app.get('/upload_cv/7777777')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Hello, Sicnarf Gnivri', r.get_data(True))
        self.assertIn('<form action="/upload_cv/7777777" method="POST">', r.get_data(True))
        self.assertIn('<button id="confirm_email" type="submit" class="btn btn-success btn-lg">Share my CV</button>', r.get_data(True))
        self.assertIn('frabcus@fastmail.fm', r.get_data(True))

    def test_upload_cv_error(self):
        r = self.app.get('/upload_cv/382828281818', follow_redirects=True)
        self.assertEqual(r.status_code, 500)
        self.assertIn('Oh dear', r.get_data(True))
        self.assertIn('Candidate 382828281818 not found', r.get_data(True))

    def test_upload_cv_send_email(self):
        with main.mail.record_messages() as outbox:
            # Ask for email confirmation
            r = self.app.post('/upload_cv/7777777')
            self.assertEqual(r.status_code, 200)
            self.assertIn('Check your email!', r.get_data(True))

            # Extract URL to confirm from email
            self.assertEqual(len(outbox), 1)
            self.assertEqual(outbox[0].subject, "Upload your CV to apply to be an MP")
            self.assertEqual(outbox[0].recipients, [('Sicnarf Gnivri', 'test@localhost')])
            self.assertEqual(outbox[0].sender, "Democracy Club CV <cv@democracyclub.org.uk>")
            m = re.search("^http://localhost(/.*)$", outbox[0].body, re.M)
            self.assertTrue(m)
            confirmation_url = m.group(1)

        # View the page where the upload form is
        r = self.app.get(confirmation_url)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Choose your CV to share', r.get_data(True))
        self.assertIn('action="' + confirmation_url + '"', r.get_data(True))

        # Upload

        f = open('fixtures/Example MP candidate CV.doc', 'rb')
        try:
            rup = self.app.post(confirmation_url, data=dict(
               files=(f, 'Example MP candidate CV.doc'),
             ), follow_redirects=True)
        finally:
            f.close()
        self.assertEqual(rup.status_code, 200)
        self.assertIn('Democracy Club Test Constituency', rup.get_data(True))
        self.assertIn('Your CV has been successfully uploaded', rup.get_data(True))

    def test_badly_signed_confirmation_link(self):
        r = self.app.get('/upload_cv/7777777/c/xxxxxyyyyyy', follow_redirects=True)
        self.assertEqual(r.status_code, 500)
        self.assertIn("That web link isn&#39;t right", r.get_data(True))

    def test_show_cv(self):
        r = self.app.get('/show_cv/7777777')
        self.assertIn('Sicnarf Gnivri', r.get_data(True))
        self.assertIn("<iframe", r.get_data(True))

if __name__ == '__main__':
    try:
        unittest.main(warnings='ignore')
    finally:
        cov.stop()
        cov.html_report(directory='covhtml')


