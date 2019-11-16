var prevpos = 0;

$("body").on("click", ".sendcomment", function (e) {
  if (!$("#wrapper").hasClass("insensitive")) {
    e.preventDefault();
    var win = window.open($(this).attr("href"), '_blank');
    win.focus();
  }
});

$("body").on("click", ".tooltip", function () {
  if (!$("#wrapper").hasClass("insensitive")) {
    prevpos = $("html").scrollTop();
    $("html").scrollTop(0);
    var factor = 750/625;
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
    downloadimage.attr("src", $(this).prev().data("rendering"));
  } 
});

$("body").on("click", ".insensitive", function () {
  $("html").scrollTop(prevpos);
  var factor = 750/625;
  $("#wrapper").css("min-height",$(window).height() - 40);
  //$("#wrapper").css("min-height",$("body").height() / factor);
  $("#wrapper").removeClass("insensitive");
  $("#wrapper").removeClass("loading");
  $("body").removeClass("open");
  $("#grid").css("opacity", "1");
  $("html").css("background-color","#000");
  $("#wrapper").css("background-image","none");
  $("#wrapper").css("height","auto");
});
