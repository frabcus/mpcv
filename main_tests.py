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
        self.assertIn('<form action="/candidates" method="GET"', r.get_data(True))
        self.assertIn('Debug email enabled', r.get_data(True))

    def test_postcode(self):
        r = self.app.get('/candidates?postcode=ZZ99ZZ', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Democracy Club Test Constituency', r.get_data(True))
        self.assertIn('Sicnarf Gnivri', r.get_data(True))
        self.assertIn('href="/show_cv/7777777"', r.get_data(True))
        self.assertIn('Notlits Esuom', r.get_data(True))
        self.assertIn('href="/upload_cv/7777778"', r.get_data(True))

        # make sure constituency remembered
        r = self.app.get('/', follow_redirects=True)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))
        self.assertIn('My constituency', r.get_data(True))

        # "I live somewhere else" clears the memory of constituency
        self.assertIn('<a href="/candidates/8888888">My constituency</a>', r.get_data(True))
        r = self.app.get('/candidates', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Democracy Club Test Constituency', r.get_data(True))

    def test_clear_all(self):
        r = self.app.get('/candidates?postcode=ZZ99ZZ', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Democracy Club Test Constituency', r.get_data(True))

        r = self.app.get('/clear_all', follow_redirects=True)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))

        r = self.app.get('/candidates', follow_redirects=True)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))

    def test_candidates_redirect(self):
        # When no cookie set, /candidates takes you to front page to choose postcode
        r = self.app.get('/candidates', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))

    def test_bad_postcode(self):
        r = self.app.get('/candidates?postcode=moo', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))
        self.assertIn("Postcode &#39;MOO&#39; is not valid.", r.get_data(True))

    def test_no_postcode(self):
        r = self.app.get('/candidates?postcode=', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Before you vote, look at their CVs!', r.get_data(True))
        self.assertIn("Postcode is not valid.", r.get_data(True))

    def test_upload_cv_index(self):
        r = self.app.get('/upload_cv/7777778')
        self.assertEqual(r.status_code, 200)
        self.assertIn('I am Notlits Esuom', r.get_data(True))
        self.assertIn('<form action="/upload_cv/7777778" method="POST">', r.get_data(True))
        self.assertIn('<button id="confirm_email" type="submit" class="btn btn-default btn-lg">I am', r.get_data(True))

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
            self.assertEqual(outbox[0].subject, "Share your CV with voters using this link")
            self.assertEqual(outbox[0].recipients, [('Sicnarf Gnivri', 'test@localhost')])
            self.assertEqual(outbox[0].sender, "Democracy Club CV <cv@democracyclub.org.uk>")
            m = re.search("^http://localhost(/.*)$", outbox[0].body, re.M)
            self.assertTrue(m)
            confirmation_url = m.group(1)

        # View the page where the upload form is
        r = self.app.get(confirmation_url)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Choose a new CV', r.get_data(True))
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
        self.assertIn('Your CV has been successfully uploaded', rup.get_data(True))
        self.assertNotIn('alert-danger', rup.get_data(True))

    def test_badly_signed_confirmation_link(self):
        r = self.app.get('/upload_cv/7777777/c/xxxxxyyyyyy', follow_redirects=True)
        self.assertEqual(r.status_code, 500)
        self.assertIn("That web link isn&#39;t right", r.get_data(True))

    def test_show_cv(self):
        r = self.app.get('/show_cv/7777777')
        self.assertIn('Sicnarf Gnivri', r.get_data(True))
        self.assertIn("<iframe", r.get_data(True))

    def test_browse_recent(self):
        r = self.app.get('/browse/recent/medium')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Browse', r.get_data(True))

    def test_browse_party(self):
        r = self.app.get('/browse/party/small')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Browse', r.get_data(True))

    def test_browse_constituency(self):
        r = self.app.get('/browse/constituency/medium')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Browse', r.get_data(True))

    def test_sitemap_xml(self):
        r = self.app.get('/sitemap.xml')
        self.assertEqual(r.content_type, "application/xml")
        self.assertIn('</urlset>', r.get_data(True))

    def test_cvs_json(self):
        r = self.app.get('/cvs.json')
        self.assertEqual(r.content_type, "application/json")
        self.assertIn('thumb', r.get_data(True))

    def test_about(self):
        r = self.app.get('/about')
        self.assertIn('cv@democracyclub.org.uk', r.get_data(True))

    def test_email_candidates(self):
        # Set postcode
        r = self.app.get('/candidates?postcode=ZZ99ZZ', follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        # Email two candidates
        r = self.app.get('/email_candidates/8888888')
        self.assertIn('Email Democracy Club Test Constituency', r.get_data(True))
        self.assertIn('Writing an effective mail', r.get_data(True))
        self.assertIn('frabcus+notlits@fastmail.fm, frabcus+ojom@fastmail.fm', r.get_data(True))
        self.assertIn('action="/email_candidates/8888888"', r.get_data(True))

        with main.mail.record_messages() as outbox:
            self.app.post('/email_candidates/8888888', data={
                'from_email': 'frabcus+voter@fastmail.fm',
                'message': 'Please please please send in your CV! Link below ;)',
                'subject': 'You need to submit a CV to apply for your new job!'
            }, follow_redirects=True)

            self.assertEqual(len(outbox), 2)

            # Check the mails are correct
            self.assertEqual(outbox[0].subject, "You need to submit a CV to apply for your new job!")
            self.assertEqual(outbox[0].recipients, [('Notlits Esuom', 'test@localhost')])
            self.assertEqual(outbox[0].sender, "Democracy Club CV <cv@democracyclub.org.uk>")
            self.assertIn('Please please please send in your CV! Link below ;)', outbox[0].body)

            self.assertEqual(outbox[1].subject, "You need to submit a CV to apply for your new job!")
            self.assertEqual(outbox[1].recipients, [('Ojom Yeknom', 'test@localhost')])
            self.assertEqual(outbox[1].sender, "Democracy Club CV <cv@democracyclub.org.uk>")
            self.assertIn('Please please please send in your CV! Link below ;)', outbox[1].body)

            # Get the upload URLs
            m = re.search("^http://localhost(/.*)$", outbox[0].body, re.M)
            upload_url_0 = m.group(1)
            m = re.search("^http://localhost(/.*)$", outbox[1].body, re.M)
            upload_url_1 = m.group(1)

        # Test out the upload URLs
        r = self.app.get(upload_url_0)
        self.assertIn('Notlits Esuom', r.get_data(True))
        self.assertIn('Choose your CV to share', r.get_data(True))

        r = self.app.get(upload_url_1)
        self.assertIn('Ojom Yeknom', r.get_data(True))
        self.assertIn('Choose your CV to share', r.get_data(True))

    def test_tweet_candidates(self):
        # Set postcode
        r = self.app.get('/candidates?postcode=ZZ99ZZ', follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        # Option to tweet one candidates
        r = self.app.get('/tweet_candidates/8888888')
        self.assertIn('Tweet Democracy Club Test Constituency candidates', r.get_data(True))
        self.assertIn('Tweet @frabcus+notlits', r.get_data(True))
        self.assertNotIn('Tweet @frabcus+sicnarf', r.get_data(True))

    def test_updates_join(self):
        r = self.app.get('/candidates?postcode=ZZ99ZZ', follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        r = self.app.post('/updates_join', data={
            'email': 'frabcus+voter@fastmail.fm',
        }, follow_redirects=True)

        self.assertIn('Thanks for subscribing to updates!', r.get_data(True))


if __name__ == '__main__':
    try:
        unittest.main(warnings='ignore')
    finally:
        cov.stop()
        cov.html_report(directory='covhtml')


