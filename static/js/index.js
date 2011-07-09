var GENERIC_ERROR = "Oops!  There was an error uploading your file.  Please upload only jpg, png, and gif files.  Maximum file size is 8 MB.";

function reset_index() {
   $("#upfile").val(""); 

   $("#inputform").show();
   $("#spinner").hide();
}

function before_submit(formData, jqForm, options) {
    $("#inputform").hide();
    $("#spinner").show();
    $(".errorbox").hide();

    return true;
}

function upload_success (data, stat) {
    if (stat !== 'success') {
        display_error(GENERIC_ERROR, reset_index);
        return false;
    } 
    resp = eval('(' + strip_pre(data) + ')');

    if (resp.error) {
        display_error(GENERIC_ERROR, reset_index);
        return false;

    } else {
        location.href = unescape(resp.select_uri);
    }
};

$(function() {
    init_logo();

    // Use this ajax to submit the upload form 
    $("#upform").ajaxForm({ 
        dataType: 'none',
        success: upload_success,
        beforeSubmit: before_submit
    });
});

