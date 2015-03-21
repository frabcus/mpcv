$(function () {

  // File upload URL button
  $(".files").change(function() {
    var btn = $(this)
    btn.parent().parent().submit()
    // This is a bit complicated - have to disable the invisible button,
    // change the text of the span above, and set the visible (bootstrap)
    // disabled attribute on the span button lookalike parent.
    btn.prop('disabled', true)
    btn.prev().attr("x-text-before", btn.prev().text())
    btn.prev().text("Uploading CV...")
    btn.parent().attr("disabled", "")
    // (Note that we can't use jquery's button.reset here due to this complexity)
  })

  // Reset buttons, on Firefox this is needed when doing back button.
  // http://duckranger.com/2012/01/double-submit-prevention-disabled-buttons-firefox-and-the-back-button/
  $(window).on("pageshow.files", function() {
    $(".files").each(function() {
      var btn = $(this)
      var text_before = btn.prev().attr("x-text-before")
      btn.prev().text(text_before)
      btn.prop('disabled', false)
      btn.parent().removeAttr("disabled")

      // Clearing the value is needed on all browsers so "change" event still fires
      // if they select the same document again.
      btn.val("")
    })

  })

  // Used on send email page (initially)
  var initiator = ""
  $(".button-disabling-form .btn").click(function() { initiator = this.id });
  $(".button-disabling-form").on('submit', function() {
    $("#" + initiator).button('loading')
  })
  // Needed for Firefox / back button
  $(window).on("pageshow.button-disabling-form", function() {
    $(".button-disabling-form .btn").button('reset').prop('disabled', false)
  });

  // Custom Tweet button
  // http://gpiot.com/blog/elegant-twitter-share-button-and-dialog-with-jquery/
  $('a.tweet').click(function(e){
    e.preventDefault();
    var loc = $(this).attr('href');
    var title = encodeURIComponent($(this).attr('title'));
    var hashtags = encodeURIComponent($(this).attr('data-hashtags'));
    var related = encodeURIComponent($(this).attr('data-related'));
    var via = encodeURIComponent($(this).attr('data-via'));

    window.open('http://twitter.com/share?' + 
      'url=' + loc + '&text=' + title + '&hashtags=' + hashtags + '&related=' + related + '&via=' + via, 
      'twitterwindow', 'height=450, width=550, top='+($(window).height()/2 - 225) +', left='+$(window).width()/2 +', ' + 
                      'toolbar=0, location=0, menubar=0, directories=0, scrollbars=0');
  }); 
});
