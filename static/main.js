console.log("in main.js!!!")
$(function () {
    console.log("in main.js sub!!!")
    $('#fileupload').fileupload({
        dataType: 'json',
        done: function (e, data) {
            console.log("done file upload ok, redirecting")
            location.href = "{{ successful_link }}"
        },
        fail: function (e, data) {
            $('.alert-danger').remove()
            $('#upload_cv').prepend('<div class="alert alert-danger">There was a problem uploading your CV. Please try again later.</div>')
        },
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#progress .bar').css(
                'width',
                progress + '%'
            );
        }
    });
});
