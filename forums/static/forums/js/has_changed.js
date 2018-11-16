/*
 * Provides a way for javascript to show if links have changed since the last visit.
 */

$(document).ready(function() {
  $(".changes").each(function() {
    primary_key = 'changed-' + $(this).data('pk');
    localStorage.setItem(primary_key, +new Date);
  });
  $(".unchanged").each(function() {
    var target = $(this);
    var primary_key = 'changed-' + target.data('pk');
    var changed = new Date(target.data('changed'));

    if(!changed || !target.data('pk')) {
      return;
    }
    var timestamp = localStorage.getItem(primary_key);
    var lastvisit = new Date(parseInt(timestamp));

    if (!timestamp || changed > lastvisit) {
        target.removeClass("unchanged");
        target.addClass("changed");
    }
  });

  var static_dir = $('body').data('static');
  /* Emojis */
  $('span.emoji').each(function() {
    var emoji = $(this).text();
    if(emoji) {
        $(this).empty();
        var code = emoji.charCodeAt(0).toString(16);
        var sibling = $('.code-' + code, $(this).parent());

        if(sibling.length) {
            // Count number of emojis of the same kind
            $(this).remove();
            var count = sibling.data('count') + 1;
            sibling.data('count', count);
            $('i', sibling).text(count).show();
        } else {
            // Create a new emoji of the right kind
            $(this).data('count', 1);
            $(this).addClass('code-'+code);
            $(this).append($('<img src="'+static_dir+'/emoji/48/'+code+'.png" alt="'+emoji+'" class="emoji">'));
            $(this).append($('<i class="count" style="display: none;">1</i>'));
        }
    }
  });
});
