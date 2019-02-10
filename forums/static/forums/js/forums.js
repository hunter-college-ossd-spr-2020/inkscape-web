/*
 * Provides a way for javascript to show if links have changed since the last visit.
 */
var emojis = ['1f600', '1f602', '1f607', '1f608', '1f609', '1f613', '1f623', '1f621', '270b', '270a', '270c', '1f918', '261d', '270d', '2764', '2605', '2618', '2714', '2716', '2754', '2755', '2622', '270e', '1f58c', '1f58d', '1f58a', '1f588', '1f525', '1f527', '1f528', '1f427', '1f426', '1f431', '1f433', '1f438'];

function refresh_render_time() {
  $(".render-time").each(function() {
    var time = new Date($(this).attr('title'));
    var since = timeSince(time);
    if(since != '0 seconds') {
      $('i', this).text(since);
      if(since.indexOf('seconds') == -1) {
        // Minutes and above
        $(this).addClass('text-danger');
      }
    }
  });
}
window.setInterval(refresh_render_time, 60000);

$(document).ready(function() {
  refresh_render_time();

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

  var users = new Object(); // Dictionary of users {pk: username}
  var users_str = localStorage.getItem("known_users");
  if (users_str) {
      users = JSON.parse(users_str);
      if(Array.isArray(users)) { // Not array
          users = new Object(); // Dictionary
      }
  }
  // Gather any usernames
  $('*[data-user]').each(function() {
      var username = $(this).data('user');
      var userid = $(this).data('userid');
      if (username != "" && userid && !(userid in users)) {
          users[userid] = username;
      }
  });
  localStorage.setItem("known_users", JSON.stringify(users));
  // This map turns the dictionary into a list.
  var usernames = Object.keys(users).map(function(key){return users[key];});
  $(document).data('usernames', usernames);
  $(document).data('users', users);

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
  $('#add_attachments').show().click(function() {
      if(!$(this).data('setup')) {
          $(this).data('setup', 1);

          // Ask for information about the user's quota
          var qt = $('#quota');
          $.getJSON('/json/quota.json', function(data) {
              var pc = parseInt(data.used / data.quota * 100);
              var pb = $('.progress-bar', qt);
              pb.attr('title', pc + '% Used');
              if(pc > 90) {
                  pb.addClass('progress-bar-danger');
              } else if(pc > 60) {
                  pb.addClass('progress-bar-warning');
              }
              var quota = parseInt(data.quota / 1024 / 1024); // MB
              var used = parseInt(data.used / 1024 / 1024); // MB
              $('strong', qt).text(used + " of " + quota + ".");
              pb.animate({width: pc + "%"});
          });

          // Generate information about any existing attachments
          add_attachments({
              'pks': JSON.parse('[' + $('.group-id_attachments input').val() + ']')
          }, {'inline': 0});
          add_attachments({
              'pks': JSON.parse('[' + $('.group-id_inlines input').val() + ']')
          }, {'inline': 1});
      }
      $('#attachment-draw').toggle();
      $(this).remove();
  });
  // Click on the "Add Existing Upload" option
  $('#resource_add').click(function() {
      var query = $('#resource_search').val();
      if(query) {
          add_attachments({'q': query}, {'inline': 0, 'update': 1});
      }
      return false;
  });
  $('#file_add').on('change', function() {
      var formData = new FormData();
      var file = this.files[0];
      formData.append('download', file);
      formData.append('name', "$"+file.name);
      formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

      var xhr = new XMLHttpRequest();
      xhr.open('POST', '/json/upload.json');

      xhr.upload.onprogress = function (event) {
          if (event.lengthComputable) {
              //progress.value = event.loaded;
              console.log("Uploading: " + event.loaded)
          }
      };
      xhr.onload = function () {
          if (xhr.status === 200) {
              var datum = JSON.parse(xhr.responseText);
              add_attachment(datum, {'update': 1, 'inline': datum.is_image});
          } else {
              var datum = JSON.parse(xhr.responseText);
              if(datum.download) {
                  alert("Problem uploading: " + datum.download);
              } else {
                  alert("Problem uploading: " + datum);
              }
          }
      };
      xhr.send(formData);
  });
  // Auto show the attachments controls if comment already has comments
  if($('.group-id_attachments input').val() || $('.group-id_inlines input').val()) {
    $('#add_attachments').click();
  }
  // Hide input boxes (inface entire input groups)
  $('.group-id_attachments').hide();
  $('.group-id_inlines').hide();

  $('[data-toggle="tooltip"]').tooltip();
  $('[data-toggle="emojitip"]').tooltip(
      {placement: "bottom", container: "body", animated: "fade"});
  $('.comment-author span.emoji').tooltip(
      {placement: "bottom", container: "body", animated: "fade"});
});

// Writes the state of the attachments into the inputs.
function update_attachments() {
  var attachments = [];
  var inlines = [];

  $('tr', '#file_box').each(function() {
      var pk = $(this).data('pk');
      if(pk != undefined) {
          if($('.inline span', this).hasClass('glyphicon-picture')) {
              inlines.push(pk);
          } else {
              attachments.push(pk);
          }
      }
  });

  $('.group-id_attachments input').val(attachments.join(','));
  $('.group-id_inlines input').val(inlines.join(','));
}

function add_attachments(query, options) {
    $.getJSON('/json/resources.json', query, function(data) {
        $.each(data.resources, function(index, datum) {
            add_attachment(datum, options);
        });
    });
}

function add_attachment(datum, options) {
    var box = $('#file_template').clone();
    box.attr('id', 'r' + datum.pk);
    box.data('pk', datum.pk);
    $('.fn', box).text(datum.filename);
    box.show();
    $('#file_box').append(box);
    if(options.inline) {
        $('.inline span', box).addClass('glyphicon-picture');
        $('.inline', box).addClass('btn-primary');
    } else {
        $('.inline span', box).addClass('glyphicon-file');
    }
    $('.inline', box).click(function() {
        $('span', this).toggleClass('glyphicon-picture');
        $('span', this).toggleClass('glyphicon-file');
        $(this).toggleClass('btn-primary');
        update_attachments();
        return false;
    });
    $('.delete', box).click(function() {
        box.remove();
        update_attachments();
        return false;
    });
    if(options.update) {
        update_attachments();
    }
}

function generate_emoji_pallet(dropdown, post_url, pot) {
    for(var i = 0; i < emojis.length; i++) {
        var code = emojis[i];
        var chr = String.fromCodePoint(parseInt(code, 16));
        var span = $('<span class="dropdown-item emoji">'+chr+'</span>');
        clean_emoji(-1, span);
        span.data('chr', chr);
        dropdown.append(span);
        span.click(function() {
            add_emote_to_comment($(this), post_url);
        });
    }
}

function add_emote_to_comment(span, post_url) {
    $.post(post_url, {
        csrfmiddlewaretoken: Cookies.get('csrftoken'),
        flag: span.data('chr'),
    }, function(data) {
        var bar_span = $('#emote-'+data.id);
        if(bar_span.length) {
            bar_span.text(span.data('chr'));
        } else {
            bar_span = $('<span class="emoji" id="emote-'+data.id+'">'+span.data('chr')+'</span>');
            span.append(bar_span);
        }
        clean_emoji(-1, bar_span);
    });
}

/* Turn an emoji into a code string */
function get_emoji_code(emoji) {
    var ret = '';
    for(var x = 0; x < emoji.length; x += 2) {
        if(ret) ret += '-';
        ret += emoji.codePointAt(x).toString(16);
    }
    return ret;
}

function emote_title(elem, target) {
    var myid = $('body').data('userid');
    var owner = $(elem).data('owner');
    if(!owner) { return; }

    var count = $(target).data('count'); // int, always-set >= 1
    var myself = $(target).data('myself'); // boolean, default=false
    var emoters = $(target).data('emoters'); // Array, default=[]
    if(!emoters) { emoters = new Array() }
    
    var users = $(document).data('users');
    if(!users) { users = new Object(); }

    if(owner == myid) {
        myself = 1;
        $(target).data('myself', myself);
    } else if(users[owner]) {
        emoters.push(users[owner]);
        $(target).data('emoters', emoters);
    }

    var unknowns = count - emoters.length;
    var title = '';

    if(myself) {
        unknowns = unknowns - 1;
        emoters.unshift('Me');
    }
    if(unknowns == 1) {
        emoters.push('1 other person');
    } else if(unknowns) {
        emoters.push(unknowns + ' other people');
    }

    var last = emoters.pop();
    var title = emoters.join(', ');
    if(title) {
        title = title + ' & ' + last;
    } else {
        title = last;
    }
    $(target).attr('title', title);
    $(target).attr('data-toggle', 'emojitip');
}

function clean_emoji(index, elem) {
    var static_dir = $('body').data('static');
    var emoji = $(elem).text();
    if(emoji) {
        var code = get_emoji_code(emoji);
        var sibling = $('.code-' + code, $(elem).parent());

        $(elem).empty();

        if(sibling.length) {
            // Count number of emojis of the same kind
            var count = sibling.data('count') + 1;
            sibling.data('count', count);
            $('i', sibling).text(count).show();
            emote_title(elem, sibling);
            $(elem).remove();
        } else {
            // Create a new emoji of the right kind
            $(elem).addClass('code-'+code);
            $(elem).append($('<img src="' + static_dir + 'emoji/48/'
                + code+'.png" alt="'+emoji+'" class="emoji">'));
            if($(elem).data('owner')) {
                $(elem).data('count', 1);
                $(elem).append($('<i class="count" style="display: none;">1</i>'));
                emote_title(elem, elem);
            }
        }
    }
}

/* Each new item is a HTML element that is marked as containing new unread
   items. All things are unread/new by default, unless the user hasseen
   the ahove element that contains the date/counts contained in this listing */
function have_you_seen_this(elem) {
    var seen_mode = $('#seenconf').data('mode');
    var primary_key = 'seen-' + $(elem).data('pk');
    var this_changed = new Date($(elem).data('changed'));
    var this_count = parseInt($(elem).data('count'));

    // Should we downgrade the visual apperence of the item because we've seen everything?
    var last_seen = new Date(parseInt(localStorage.getItem(primary_key + '-date')));
    if (last_seen && this_changed && last_seen >= this_changed) {
        if(seen_mode == 'DEL') {
          $(elem).hide();
        } else {
          $(elem).removeClass("new");
          $(elem).addClass("old");
        }
    }

    // Should we modify the counter and change the style of the counter because we've not
    // seen some items?
    var last_count = parseInt(localStorage.getItem(primary_key + '-count'));
    $('.counter', elem).each(function() {
        var delta = this_count - last_count;
        if(delta == 0 || this_count == 0) {
            //$(this).hide();
            $(this).addClass('label-muted');
        } else if(delta > 0) {
            $(this).text(delta);
            $(this).removeClass('label-default');
            $(this).addClass('label-primary');
        }
    });
}


function record_selected_text() {
    var text = '';
    if (typeof window.getSelection != "undefined") {
        text = window.getSelection().toString()
    } else if (typeof document.selection != "undefined" && document.selection.type == "Text") {
        text = document.selection.createRange().text;
    }
    if(text) {
        localStorage.setItem("quoteBox", window.getSelection().toString());
    }
}

$(document).on('mouseup', record_selected_text);
$(document).on('onkeyup', record_selected_text);

function timeSince(date) {
  var seconds = Math.floor((new Date() - date) / 1000);
  var interval = Math.floor(seconds / 31536000);

  if (interval > 1) {return interval + " years";}
  interval = Math.floor(seconds / 2592000);
  if (interval > 1) {return interval + " months";}
  interval = Math.floor(seconds / 86400);
  if (interval > 1) {return interval + " days";}
  interval = Math.floor(seconds / 3600);
  if (interval > 1) {return interval + " hours";}
  interval = Math.floor(seconds / 60);
  if (interval > 1) {return interval + " minutes";}
  return Math.floor(seconds) + " seconds";
}
