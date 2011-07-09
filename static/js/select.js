var SELECT_ERROR;
SELECT_ERROR = "Oops!  There was an error cropping your image.  Please try again.";

function reset_select() {
    $("#inputform").show();
    $("#spinner").hide();
}

function set_style_preview () {
    // Change the preview to the right of the image
    var name  = $("select#styleselect").val();
    var image = "/static/images/" + name + ".gif";
    $("img#preview").attr("src", image);

    // Then change the circle on the highlighter if needed
    if (name.match(/lighten/)) {
        $("#highcircle").hide();
    } else {
        $("#highcircle").show();
    }
    
}

$(function() {
    init_logo();

    var initial_top;
    var initial_left;

    initial_top  = $("div.highlighter").position().top;
    initial_left = $("div.highlighter").position().left;

    // Make sure the contact link appears below the highlighter image
    $("div.contact").css("margin-top", $("div.highlighter").offset().top);

    $("div.highlighter").resizable({ alsoResize: "#highcircle"}).draggable();

    // Run it the initial time, and then set up a change func.
    set_style_preview();
    $("select#styleselect").change(function () {
        set_style_preview();
    });
    

    $("button#done").click(function () {
        var hl        = $("div.highlighter");
        var enc_id    = $("#enc_id").val();
        var ext       = $("#ext").val();
        var auth      = $("#auth").val();

        var get_params = {
            // The crop selection
            width:  $(hl).width(),
            height: $(hl).height(),
            top:    ($(hl).position().top  - initial_top),
            left:   ($(hl).position().left - initial_left),


            // The original image
            max_width:  $(".hlimg").attr("width"),  
            max_height: $(".hlimg").attr("height"),  
        
            enc_id: enc_id,
            ext:    ext,
            auth:   auth,
            style:  $("select#styleselect").val()
        };

        // Show spinner image while cropping
        $("#inputform").hide();
        $("#spinner").show();

        $.get("/app/crop", get_params, function (data) {
            resp = eval('(' + strip_pre(data) + ')');
           
            if (resp.error) {
                display_error(SELECT_ERROR, reset_select);
            } else {
                location.href = resp.final_uri;
            }
        });
    });
});
