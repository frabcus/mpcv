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

});
