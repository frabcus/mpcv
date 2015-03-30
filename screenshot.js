var system = require('system');
var page = require('webpage').create();

// Usage: phantomjs screenshot.js <CV URL> <filename>

var cvUrl = system.args[1];
var filename = system.args[2];

/**
 * Wait until the test condition is true or a timeout occurs. Useful for waiting
 * on a server response or for a ui change (fadeIn, etc.) to occur.
 *
 * @param testFx javascript condition that evaluates to a boolean,
 * it can be passed in as a string (e.g.: "1 == 1" or "$('#bar').is(':visible')" or
 * as a callback function.
 * @param onReady what to do when testFx condition is fulfilled,
 * it can be passed in as a string (e.g.: "1 == 1" or "$('#bar').is(':visible')" or
 * as a callback function.
 * @param timeOutMillis the max amount of time to wait. If not specified, 3 sec is used.
 */
function waitFor(testFx, onReady, timeOutMillis) {
    var maxtimeOutMillis = timeOutMillis ? timeOutMillis : 3000, //< Default Max Timout is 3s
        start = new Date().getTime(),
        condition = false,
        interval = setInterval(function() {
            if ( (new Date().getTime() - start < maxtimeOutMillis) && !condition ) {
                // If not time-out yet and condition not yet fulfilled
                condition = (typeof(testFx) === "string" ? eval(testFx) : testFx()); //< defensive code
            } else {
                if(!condition) {
                    // If condition still not fulfilled (timeout but condition is 'false')
                    console.log("'waitFor()' timeout");
                    phantom.exit(1);
                } else {
                    // Condition fulfilled (timeout and/or condition is 'true')
                    typeof(onReady) === "string" ? eval(onReady) : onReady(); //< Do what it's supposed to do once the condition is fulfilled
                    clearInterval(interval); //< Stop this interval
                }
            }
        }, 250); //< repeat check every 250ms
};

var url = "http://docs.google.com/viewer?embedded=true&url=" + encodeURIComponent(cvUrl);

console.log("Generating screenshot for: " + url);
page.open(url, function (status) {
    if (status !== "success") {
        console.log("Unable to access network");
        phantom.exit();
    } else {
        var clip = 12
        page.viewportSize = {width: 400 + 2*clip, height: 566 + 2*clip};
        page.includeJs("https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js", function() {
            waitFor(function () {
                return page.evaluate(function() {
                    return $(['role=\"document\"']).length > 0;
                });
            }, function() {
                // wait another 10 seconds (until page num and toolbar disappear)
                setTimeout(function () {
                    if (page.content.indexOf("No preview available") > -1) {
                        phantom.exit(3);
                    }

                    page.clipRect = {
                      top: clip,
                      left: clip,
                      width: 400,
                      height: 566
                    };
                    page.render(filename);
                    phantom.exit();
                }, 10000);
            });
        });
    }
});
