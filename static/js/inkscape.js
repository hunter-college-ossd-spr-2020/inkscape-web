
function getPng(t) {
  if(t.src.slice(-3)=='svg') {
    t.src = t.src.slice(0,-3) + "png";
  }
}

/* Resize menu bar code (for translations) */
$(document).ready(function() {
      if($("#menu"))menu();
      if($('[class|="maxHeight"]')[0])maxHeight();
      if($("#toplogin"))adjustBar();
});

/* == PopUp implimentation == */
function toggle(div_id) {
    var el = document.getElementById(div_id);
    if ( el.getAttribute('class') == 'show' ) {
      el.setAttribute('class', '');
    } else {
      el.setAttribute('class', 'show');
    }
}
function window_pos(popId) {
    var pop = document.getElementById(popId);
    pop.setAttribute('style', 'top: calc(50% - ' + (pop.clientHeight / 2) + 'px); '+
                     'left: calc(50% - ' + (pop.clientWidth / 2) + 'px);');
}
function popUp(windowname) {
    toggle('blanket');
    toggle(windowname);     
    window_pos(windowname);
}
/* End popup */

jQuery.fn.getMaxHeight = function(){
    var ca = this.attr('class');
    var rval = [];
    if(ca && ca.length && ca.split){
        ca = jQuery.trim(ca); /* strip leading and trailing spaces */
        ca = ca.replace(/\s+/g,' '); /* remove doube spaces */
        var n = ca.indexOf("maxHeight-"); 
        ca.substring(n);
        rval = ca.split(' ');
    }
    return rval[0].replace("maxHeight-","");
}

function menu(){
    var elementHeight=0;
    var containerHeight=1;
    var i = 0;
    var onePixelLess = parseInt( $("#menu").children("li").children("a:first-child").css('font-size'))-1 + "px";
    while(containerHeight > elementHeight){
        $("#menu").children("li").each(function(){
            if(i != 0){
                $(this).children("a:first-child").css('font-size',onePixelLess);
                $(this).children("a:first-child").css('padding-left',parseInt($(this).children("a:first-child").css('padding-left'))-1 + "px");
                $(this).children("a:first-child").css('padding-right',parseInt($(this).children("a:first-child").css('padding-right'))-1 + "px");
            }
            elementHeight = $(this).height();
        })
        i++;
        containerHeight = $("#menu").height();
    }
}

function adjustBar(){
    var tw = parseInt( $("#toplogin").width() );
    var fw = parseInt( $("#toplogin").children("form").width() );
    $("#toplogin").children("form").css('margin-left', (tw-fw-20)+"px");
}

function maxHeight(){
    $('[class|="maxHeight"]').each(function(){
        var elementHeight = $(this).height();
        var containerHeight=$(this).getMaxHeight();
        var textSize;
        var i = 0;
        while(containerHeight < elementHeight){
            textSize =  parseInt($(this).css('font-size'));
            if(textSize == 5) break;
           if(i != 0){
                $(this).css('font-size',textSize-1 + "px");
            }
            i++;
            elementHeight = $(this).height();
        }
    })
}
