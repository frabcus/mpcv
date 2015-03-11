// Integration tests in Casper, which runs a headless browser.
// No need to cover everything in this - just main workflows,
// and anything javascript intensive (such as file upload).

// URL we start from, read as parameter --address=
var address = casper.cli.get("address");
var screenshot = casper.cli.get("screenshot");
var fs = require('fs');

// Record screenshots
var screenshot_number = 0;
if (screenshot) {
    casper.on("load.finished", function() {
        screenshot += 1;
        var name = "screenshots/" + screenshot_number +  ".png";
        this.capture(name);
        // console.log("screenshot: ", name, "url:", casper.getCurrentUrl());
    });
}

// Tests in detail
/*
casper.test.begin('Postcode lookup and constituency cookie', 13, function suite(test) {
    casper.start(address, function(result) {
        test.assertEquals(result.status, 200);
        test.assertTextExists('Before you vote, look at their CVs!');
        test.assertTextExists('Debug email enabled');

        this.fill('form[action="/set_postcode"]', { postcode: "zz99zz" }, true);
    });

    casper.waitForUrl(/candidates$/, function() {
        test.assertTextExists('Democracy Club Test Constituency');
        test.assertTextExists('View CVs of these candidates');
        test.assertTextExists('Sicnarf Gnivri');
        test.assertExists('a[href="/show_cv/7777777"]');
        test.assertTextExists('Ask these candidates to add their CV');
        test.assertTextExists('Notlits Esuom');
        test.assertExists('a[href="/upload_cv/7777778"]');
    });

    // make sure constituency remembered, and front page redirects back to constituency page
    casper.thenOpen(address, function() {
        test.assertTextExists('Democracy Club Test Constituency');
        test.assertTextExists('View CVs of these candidates');

        this.clickLabel("Change constituency");
    });

    // "Change constituency" clears the memory of constituency
    casper.then(function() {
        test.assertTextExists('Before you vote, look at their CVs!');
    });

    casper.run(function() {
        test.done();
    });
});
*/

casper.test.begin('Uploading a CV', 13, function suite(test) {

    casper.start(address + "upload_cv/7777777", function(result) {
        test.assertTextExists('We need to confirm your email first');
        test.assertTextExists('Hi, Sicnarf Gnivri');

        this.fill('form[action="/upload_cv/7777777"]', { }, true);
    });

    casper.then(function() {
        test.assertTextExists('Check your email!');

        var url = fs.readFileSync('last_confirm_url.txt').toString();
        console.log("last_confirm_url: " + url);

        this.open(url);
    });

    casper.waitForUrl(/upload_cv\/7777777\/c\/.*$/, function() {
        test.assertTextExists('Drop your CV in here');

        console.log("before url is: " + casper.getCurrentUrl());
        //this.page.onFilePicker = function() {
        //    console.log('in onFilePicker');
        //    return "fixtures/Example MP candidate CV.doc";
        //};
        console.log("slUtils.getMozFile: ");
        var foo = slUtils.getMozFile("fixtures/Example MP candidate CV.doc"));
        console.log(foo);
        this.page.uploadFile('input#fileupload', "fixtures/Example MP candidate CV.doc");
        // this.fill('form', { 'file': 'fixtures/Example MP candidate CV.doc' }, true)
        //this.click('#fileupload');
        console.log("after url is: " + casper.getCurrentUrl());
    });

    casper.waitForUrl(/candidates$/, function() {
        test.assertTextExists('Your CV has been successfully uploaded');
    });


    casper.run(function() {
        test.done();
    });

});



