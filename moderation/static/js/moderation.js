function popUpModeration(msg, cancel, ok, next, note) {
  var a = document.currentScript.previousElementSibling;
  var p = a.parentNode;
  $(document).ready( function() {
    var ajax = function(data) {
      var b = $('.i_voted', p); 
      if(b.length > 0) {
        b.removeClass('i_voted');
        var b_vote = $('.'+$(b).attr('class')+'_votes', p); 
        b_vote.text(parseInt(b_vote.text()) - 1); 
      }   
      if(data.weight) {
        $('.weight', p).text(data.weight);
      }   
      var a_vote = $('.'+$(a).attr('class')+'_votes', p); 
      a_vote.text(parseInt(a_vote.text()) + 1); 
      $(a).addClass('i_voted');

      // Next we look at the vote rolls
      $('#vote-' + data.id).remove();
      var mark = $('<p id="vote-'+data.id+'"><img src="'+data.weight_icon+'" title="'+data.weight_label+', Weight: '+data.weight+'"/><strong>'+data.user+'</strong> <em>'+data.notes+' - Just Now</em></p>');
      $('#votes-'+data.target).append(mark);
    }   
    var href = a.href;
    $(a).click(function() { return popUp(a.title, msg, href, cancel, ok, next, note, ajax) }); 
    a.href = '#' + href;
  }); 
}
