var prevpos = 0;

$("body").on("click", ".sendcomment", function (e) {
  if (!$("#wrapper").hasClass("insensitive")) {
    e.preventDefault();
    var win = window.open($(this).attr("href"), '_blank');
    win.focus();
  }
});

$("body").on("click", ".resource, .tooltip", function () {
  if (!$("#wrapper").hasClass("insensitive")) {
    prevpos = $("html").scrollTop();
    $("html").scrollTop(0);
    $("#wrapper").css("height",$(window).height() - 40);
    $("#wrapper").addClass("insensitive");
    $("#wrapper").addClass("loading");
    $("body").addClass("open");
    $("#grid").css("opacity", "0");
    $("html").css("background-color","#fff");
    $("#wrapper").css("background-image","none");
    var downloadimage = $('<img>');
    downloadimage.on("load", function () {
      $("#wrapper").css("background-image","url(" + $(this).attr("src") + ")");
      $("#wrapper").removeClass("loading");
    });
    if ($(this).hasClass("tooltip")) {
        downloadimage.attr("src", $(this).parent().prev().data("rendering"));
    } else {
        downloadimage.attr("src", $(this).data("rendering"));
    }
  } 
}); 

$("body").on("click", ".insensitive", function () {
  $("html").scrollTop(prevpos);
  $("#wrapper").css("min-height",$(window).height() - 40);
  $("#wrapper").removeClass("insensitive");
  $("#wrapper").removeClass("loading");
  $("body").removeClass("open");
  $("#grid").css("opacity", "1");
  $("html").css("background-color","#000");
  $("#wrapper").css("background-image","none");
  $("#wrapper").css("height","auto");
});
