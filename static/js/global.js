function display_error(txt, postfunc) {
    $("div.errorbox div.textspace").html(txt);
    $("div.errorbox").show();
    postfunc();
}


function strip_pre(json) {
    // This is a badbad hack to get around bug in jquery.form
    return json.slice(json.indexOf('{'), json.lastIndexOf('}') + 1)
}

function init_logo() {
    // Highlight each letter of the logo by setting the
    // bg color to yellow when doing a mouseover
    $("div.logo span").mouseover(function () {
        $(this).css("background-color", "yellow");
    });

    $("div.logo span").mouseout(function () {
        var me = this;
        setTimeout(function () {
            $(me).css("background-color", "white");
        }, 100);
    });

    $("div.logo span").click(function () {
      location.href="/";
    });
}

