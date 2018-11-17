/*
 * Provides a way for javascript to show if links have changed since the last visit.
 */
var emojis = ['1f600', '1f602', '1f607', '1f608', '1f609', '1f613', '1f623', '1f621', '270b', '270a', '270c', '1f918', '261d', '270d', '2764', '2605', '2618', '2714', '2716', '2754', '2755', '2622', '270e', '1f58c', '1f58d', '1f58a', '1f588', '1f525', '1f527', '1f528', '1f427', '1f426', '1f431', '1f433', '1f438'];

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

  $('.emoji-selector').each(function() {
      var selector = $(this);
      var a = $('a', this);
      var pot = $('#bar-' + a.attr('id'));
      // Move href to data
      a.data('href', a.attr('href')).attr('href', '#')

      a.click(function() {
          $('.dropdown-menu', selector).each(function() {
              if($(this).children().length == 0) {
                  generate_emoji_pallet($(this), a.data('href'), pot);
              }
          });
          return true;
      });
  });

  /* Page Emojis */
  $('span.emoji').each(clean_emoji);
});

function generate_emoji_pallet(dropdown, post_url, pot) {
    for(var i = 0; i < emojis.length; i++) {
        var code = emojis[i];
        var chr = String.fromCodePoint(parseInt(code, 16));
        var span = $('<span class="dropdown-item emoji">'+chr+'</span>');
        clean_emoji(-1, span);
        span.data('chr', chr);
        dropdown.append(span);
        span.click(function() {
            var span = $(this);
            $.post(post_url, {
                csrfmiddlewaretoken: Cookies.get('csrftoken'),
                flag: $(this).data('chr'),
            }, function() {
                var bar_span = $('<span class="emoji">'+span.data('chr')+'</span>');
                pot.append(bar_span);
                clean_emoji(-1, bar_span);
            });
        });
    }
}

function clean_emoji(index, elem) {
    var static_dir = $('body').data('static');
    var emoji = $(elem).text();
    if(emoji) {
        var code = emoji.codePointAt(0).toString(16);
        var sibling = $('.code-' + code, $(elem).parent());

        $(elem).empty();

        if(sibling.length) {
            // Count number of emojis of the same kind
            $(elem).remove();
            var count = sibling.data('count') + 1;
            sibling.data('count', count);
            $('i', sibling).text(count).show();
        } else {
            // Create a new emoji of the right kind
            $(elem).data('count', 1);
            $(elem).addClass('code-'+code);
            $(elem).append($('<img src="' + static_dir + 'emoji/48/'
                + code+'.png" alt="'+emoji+'" class="emoji">'));
            $(elem).append($('<i class="count" style="display: none;">1</i>'));
        }
    }
}
