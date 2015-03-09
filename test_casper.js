// URL we start from, read as parameter --address=
var address = casper.cli.get("address");

// Record screenshots
var screenshot = 0;
casper.on("load.finished", function() {
    screenshot += 1;
    this.capture("screenshots/" + screenshot +  ".png");
});

// Tests

casper.test.begin('Postcode lookup', 10, function suite(test) {
    casper.start(address, function(result) {
        test.assertEquals(result.status, 200);
        test.assertTextExists('Before you vote, look at their CVs!');
        test.assertTextExists('Debug email enabled');

        this.fill('form[action="/set_postcode"]', { postcode: "zz99zz" }, true);
    });

    casper.then(function() {
        test.assertTextExists('Democracy Club Test Constituency');
        test.assertTextExists('View CVs of these candidates');
        test.assertTextExists('Sicnarf Gnivri');
        test.assertExists('a[href="/show_cv/7777777"]');
        test.assertTextExists('Ask these candidates to add their CV');
        test.assertTextExists('Notlits Esuom');
        test.assertExists('a[href="/upload_cv/7777778"]');
    });

    // make sure constituency remembered, and front page redirects back to constituency page
    casper.then(function() {
        //r = self.app.get('/', follow_redirects=True)
        //self.assertEqual(r.status_code, 200)
        //self.assertIn('Candidates for job of MP', r.get_data(True))
        //self.assertIn('Democracy Club Test Constituency', r.get_data(True))
    });

    casper.run(function() {
        test.done();
    });
});
