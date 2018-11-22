/*
 * Provides a way for javascript to show if links have changed since the last visit.
 */
var emojis = ['1f600', '1f602', '1f607', '1f608', '1f609', '1f613', '1f623', '1f621', '270b', '270a', '270c', '1f918', '261d', '270d', '2764', '2605', '2618', '2714', '2716', '2754', '2755', '2622', '270e', '1f58c', '1f58d', '1f58a', '1f588', '1f525', '1f527', '1f528', '1f427', '1f426', '1f431', '1f433', '1f438'];

$(document).ready(function() {
  console.log('ready');
  /* Each haveseen item is a HTML element that expresses how the user
     has seen this item. Once seen, the date and the counts are recorded
     for use in listings of this item. */
  $(".haveseen").each(function() {
    primary_key = 'seen-' + $(this).data('pk');
    localStorage.setItem(primary_key + '-date', +new Date);
    localStorage.setItem(primary_key + '-count', $(this).data('count'));
  });

  $(".new").each(function() { have_you_seen_this(this); });

  // Special button for marking all as read/seen
  $('#seenall').click(function() {
    $(".new").each(function() {
        var primary_key = 'seen-' + $(this).data('pk');
        localStorage.setItem(primary_key + '-date', +new Date);
        localStorage.setItem(primary_key + '-count', $(this).data('count'));
        have_you_seen_this(this);
    });
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

  /* Attachments */
  $('.check-dropdown .dropdown-menu').each(function() {
      if(!$(this).children().length) {
          $(this).parent().hide();
      }
  });
  $('.inline-attachments').each(function() {
      if(!$(this).children().length) {
          $(this).hide();
      }
  });
  $('.group-id_attachments').hide();
  $('.group-id_inlines').hide();
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

/* Each new item is a HTML element that is marked as containing new unread
   items. All things are unread/new by default, unless the user hasseen
   the ahove element that contains the date/counts contained in this listing */
function have_you_seen_this(elem) {
    var primary_key = 'seen-' + $(elem).data('pk');
    var this_changed = new Date($(elem).data('changed'));
    var this_count = parseInt($(elem).data('count'));

    // Should we downgrade the visual apperence of the item because we've seen everything?
    var last_seen = new Date(parseInt(localStorage.getItem(primary_key + '-date')));
    if (last_seen && this_changed && last_seen >= this_changed) {
        $(elem).removeClass("new");
        $(elem).addClass("old");
    }

    // Should we modify the counter and change the style of the counter because we've not
    // seen some items?
    var last_count = parseInt(localStorage.getItem(primary_key + '-count'));
    $('.counter', elem).each(function() {
        var delta = this_count - last_count;
        if(delta == 0 || this_count == 0) {
            $(this).hide();
        } else if(delta > 0) {
            $(this).text(delta);
            $(this).removeClass('label-default');
            $(this).addClass('label-primary');
            }
    });
}
