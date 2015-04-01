$(function () {

  // Cope with top navigation wrapping
  // http://stackoverflow.com/a/20197508
  $(document.body).css('padding-top', $('#topnavbar').height() - 10);
  $(window).resize(function(){
      $(document.body).css('padding-top', $('#topnavbar').height() - 10);
  });

  // File upload URL button
  $(".files").change(function() {
    var btn = $(this);
    btn.parent().parent().submit();
    // This is a bit complicated - have to disable the invisible button,
    // change the text of the span above, and set the visible (bootstrap)
    // disabled attribute on the span button lookalike parent.
    // (Note that we can't use jquery's button.reset here due to this complexity)
    btn.prop('disabled', true);
    btn.prev().attr("x-text-before", btn.prev().text());
    btn.prev().text("Uploading CV...");
    btn.parent().attr("disabled", "");
  });

  // Reset buttons, on Firefox this is needed when doing back button.
  // http://duckranger.com/2012/01/double-submit-prevention-disabled-buttons-firefox-and-the-back-button/
  $(window).on("pageshow.files", function() {
    $(".files").each(function() {
      var btn = $(this);
      var text_before = btn.prev().attr("x-text-before");
      btn.prev().text(text_before);
      btn.prop('disabled', false);
      btn.parent().removeAttr("disabled");

      // Clearing the value is needed on all browsers so "change" event still fires
      // if they select the same document again.
      btn.val("");
    });

  });

  // Used on send email page (initially)
  var initiator = "";
  $(".button-disabling-form .btn").click(function() { initiator = this.id; });
  $(".button-disabling-form").on('submit', function() {
    $("#" + initiator).button('loading');
  });
  // Needed for Firefox / back button
  $(window).on("pageshow.button-disabling-form", function() {
    $(".button-disabling-form .btn").button('reset').prop('disabled', false);
  });

  // Twitter analytics
  // Event hooks on custom Twitter buttons see: see http://stackoverflow.com/a/16288629/284340
  if (typeof twttr !== 'undefined') {
    twttr.ready(function() {
      twttr.events.bind(
        'tweet',
        function (ev) {
          var person_id = $(ev.target).attr("x-person-id");
          ga('send', 'event', 'ask', 'tweet', person_id);
          console.log("sent GA event: ask tweet ", person_id);
        }
      );
    });
  }

});

// Event tracking
var track_ask_email_event = function(person_ids) {
  for (var i=0; i<person_ids.length; i++) {
    ga('send', 'event', 'ask', 'email', person_ids[i]);
    console.log("sent GA event: ask email ", person_ids[i]);
  }
};


