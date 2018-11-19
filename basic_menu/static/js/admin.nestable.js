(function($) {

var nest_init = false;

$(document).ready(function() {
  var body = $('body.change-form');
  if(body.length == 0) { 
    return;
  }

  //update_nest();

  $('#mechanisms-group fieldset .dd').nestable({
      maxDepth: 10,
  }).on('change', update_nest)

  $('#mechanisms-group fieldset table th').hide();
  $('#dataselector_form').submit(form_submit);

  initialise_columns($('.dd3-content'));
  $('.dd3-content').initialize(function () { initialise_columns(this); })

  $('input[type="number"]').keypress(function(ev) {
    if($(this).attr('type') == 'number') {
      return $.isNumeric(ev.key) || ev.key.length > 1 || ev.key == ".";
    }
  }).dblclick(function () {
    // Switch between number and text fields
    if($(this).attr('type') == 'number') {
      $(this).attr('type', 'text');
    } else {
      $(this).attr('type', 'number');
    }
  }).each(function() {
    // Check on start up if we have a variable name
    var orig = $(this).attr('value');
    if($.isNumeric(orig) == false) {
      $(this).dblclick();
      $(this).val(orig);
    }
  });
  $('.help-tooltip', document).each(function() {
    $(this).wrap('<span href="#" title="' + $(this).attr('title') + '" class="tooltip"></span>');
  });
});

/*
   when called will move source options and source selection to a mechanism like row.
 */
function setup_source_fields() {
  var container = $('#mechanisms-group fieldset.module');
  
  container.append('<div id="source-dd" class="dd-item dd3-item" style="diaply: block;"></div>');
  $('#source-dd').append('<div class="dd3-source glyphicon glyphicon-align-center"></div>')
                 .append('<div class="dd3-add glyphicon glyphicon-plus" title="Add filter mechanism"></div>')
                 .append('<div class="dd3-output glyphicon glyphicon-eye-open" title="Data from this level will be in the final output."></div>')
                 .append('<div class="dd3-content"></div>');

  var tr = $('<tr id="source-row"></tr>');
  $('#source-dd .dd3-content').append(tr);

  var cell = $('<td style="display: table-cell;"></td>');
  cell.append($('#id_source_id'));
  tr.append(cell);

  $('.field-source_id').hide();
  $('.field-output').hide();

  $('div[class^="form-row field-source__"] div').each(function() {
    $(this).parent().parent().hide().attr('class', '');
    var cell = $('<td style="display: table-cell;"></td>');
    tr.append(cell);
    cell.append($(this));
    $('label', this).hide();
    var p = $('p', this);
    if(p[0]) {
      $(this).append('<img class="help help-tooltip" src="/static/admin/img/icon-unknown.gif" title="'+p.text()+'"/>');
      p.hide();
    }
  });

  the_eye_of_output($('#source-dd .dd3-output'), $('#id_output'));

  // This mutation observer is watching for any node changes in the html tree
  // it will trigger once on multiple nodes being added, although we've set it
  // to both disconnect after the first run AND are selective onlyto trigger on
  // childList events. This does mean that we trigger on the div being added
  // and not the "Add filter mechanism" objects.
  var observer = new MutationObserver(function(mutationsList, obs) {
      var add = $('tr.add-row a', container);
      add.closest('tbody').hide();
      $('#source-dd .dd3-add').click(function() {
        add.click();
      });
      obs.disconnect();
  });
  observer.observe(container[0], {childList: true, subtree: false});

  $('#id_source_id').change(function(event) {
    update_options(tr, null, 'td', 'source', $(this).val());
  }).change();
}

(function($) {
  $.fn.addOption = function(name, value) {
    $(this).append($("<option></option>").attr("value", value).text(name));
  }
  $.fn.replaceOptions = function(options) {
    this.empty();
    var self = this;

    $.each(options, function(index, option) {
      $(self).addOption(option.text, option.value);
    });
    $(this).addOption("(Custom)", '-');
  };
  $.fn.toMasterValue = function() {
    var ret = '';
    // We take each of the visible elements and compile them
    $('#'+this[0].id+'_holder .column:visible').each(function() {
        if($(this).val() != '') {
          if(ret != '') { ret += ',' }
          ret += $(this).val().replace(/,/g, "_");
          $('#' + this.id + '_eq').each(function() {
            ret += '=' + $(this).val().replace(/,/g, ";");
          });
        }
    });
    this.val(ret);
  };
  $.fn.fromMasterValue = function() {
    var ret = {};
    var whole_value = $(this).val();
    if($(this).hasClass('column-list') || $(this).hasClass('column-dict')) {
        if(whole_value) {
          $.each(whole_value.split(','), function(index, value) {
            bits = value.split("=", 2);
            if(bits[0]) {
              ret[bits[0]] = bits[1];
            }
          });
        }
    } else if(whole_value) {
        ret[whole_value] = undefined;
    }
    return ret
  };
})(jQuery);

/*
 * The idea here is that a list of columns is much like a signle column
 * we would take any number of fields and concat them together into the
 * final input as well as taking the csv list and making multiple drops
 */
function initialise_columns(parent) {
  select = $('input.auto-column', parent);
  select.each(function() {
    var holder = $("<div class='column-holder'></div>");
    $(holder).attr('id', this.id + '_holder');
    $(holder).insertAfter($(this));

    $(this).on("change", function() {
        var original = this;
        original.counter = 0;
        //$(this).attr('style', 'border: 1px solid red');
        $(this).hide();

        $.each($(this).fromMasterValue(), function(key, value) {
            add_column_select(original, key, value);
        });

        if(original.counter == 0) {
            // Where we have no drop downs, we should at least have one
            // on load. We may not have one for lists and dicts after the
            // user has deleted them, but that's ok.
            add_column_select(original);
        }

        if($(this).hasClass('column-list') || $(this).hasClass('column-dict')) {
          var add = $("<img src='/static/admin/img/icon-add.gif' class='help help-add'>");
          add.insertAfter(holder);
          add.click(function() {
              add_column_select(original);
          });
        }
        $(this).off("change")
    });

  });

  update_columns();
  $('#id_source_id').change(update_columns);
  $('*[data-target="source"]').change(update_columns);
}

function add_column_select(original, key, value) {
    var holder = $('#'+original.id+'_holder');
    var elem_id = original.id + '_value_' + original.counter;
    holder.append($("<b>,</b>"));

    var select = $('<select></select>');
    holder.append(select);
    $(select).attr('id', elem_id);
    $(select).replaceOptions($('body')[0].cols);
    $(select).addClass('column');
    $(select).change(function() {
      var val = $(this).val();
      if(val == '-') {
        // Change to text box when selecting '-' option.
        $(this).hide();
        $("input#" + this.id).show();
      } else if(val == '' && ($(original).hasClass('column-list') || $(original).hasClass('column-dict'))) {
        // Delete drop down in this case
        $("select#" + this.id).remove();
        $("input#" + this.id).remove();
        $("input#" + this.id + '_eq').remove();
        $(holder).find('b:last').remove();
        $(holder).find('b:last').remove();
      } else {
        // We update the text box, assuming it's not '-'
        $("input#" + this.id).val(val);
      }
      // Update the master value
      $(original).toMasterValue();
    });

    var input = $('<input type="text"/>');
    $(input).attr('id', elem_id);
    $(input).insertAfter(select);
    $(input).addClass('column');
    $(input).hide();
    $(input).change(function() {
      // Update the master input
      $(original).toMasterValue();
    });

    if(key) {
      if(0 == $(select).find('option[value="'+key.replace('/\"/g',"\\\"")+'"]').length) {
        // Show text box on load
        $(input).val(key);
        $(input).show();
        $(select).hide();
      } else {
        $(select).val(key);
      }
    }

    if($(original).hasClass('column-dict')) {
        var value_input = $('<input type="text"/>');
        value_input.attr('id', elem_id + '_eq');
        value_input.insertAfter(input);
        value_input.val(value);
        value_input.addClass('eq');
        value_input.change(function() {
          // Update the master input
          $(original).toMasterValue();
        });
        $("<b>=</b>").insertAfter(input);
    }

    $(input).dblclick(function() {
      $(this).hide();
      $("select#" + this.id).show();
      $("select#" + this.id).val($(this).val());
    });

    $(holder).find('b:first').remove();
    $(holder).find('b:first').remove();
    original.counter += 1;
}

function update_columns() {
  $.post('/select/cols/s/json/', $('#dataselector_form').serialize(),
    function(data, textStatus, jqXHR) {
      // Store the cols globally on the body element
      $('body')[0].cols = data['columns'];
      $('input.auto-column').each(function() {
        $(this).change();
      });
    }
  );
}

function form_submit(event) {
  try {
    sanity_checks();
  } catch (e) {
    if($('.errornote').length == 0) {
      $(this).prepend('<p class="errornote">Please correct the error below.</p>')
    }
    return false;
  }
  return true;
}

function sanity_checks() {
  var errors = 0;
  $('ol > li.dd-item').each(function() {
    var output = $(this).find('.field-output > input:checked').length > 0;
    errors += assertTrue(output, $(this).find('> .dd3-content .field-mechanism_id'), "This mechanism doesn't appear to do anything.");
  });
  // Runs some sanity checks to make sure this data selector makes sense.
  var output = $('#id_output:checked, .field-output > input:checked').length > 0;
  errors += assertTrue(output, $('#id_source_id').parent(), "This data selector needs some output, either raw or mechanism output.");
  if(errors > 0) { throw errors; }
}

function assertTrue(check, field, msg) {
  if(check) {
    $(field).removeClass('errors');
    $(field).find('ul.errorlist').remove();
    return 0;
  } else {
    $(field).addClass('errors');
    if($(field).find('ul.errorlist').length == 0) {
      $(field).prepend('<ul class="errorlist"><li>'+msg+'</li></ul>');
    }
    return 1;
  }
}

function update_nest(event) {
  var order = 0;
  $('#mechanisms-group .dd li.dd-item').each(function() {
    $(this).removeClass('parent-error');
    var trs = $(this).find('tr');
    if(trs.length > 0) {
      var id = trs[0].id;
      // Update the order of the mechanism as shown.
      $('#id_'+id+'-order').val(order);

      if(!nest_init) {
        var parent_pk = $('#id_'+id+'-source').val();
        if(!parent_pk){ return }
        var parent_el = $('.dd3-content td.original input[value="'+parent_pk+'"][id$="-id"]').closest('li');
        if(parent_el.length == 0) {
          return $(this).addClass('parent-error');
        }
        if(parent_el.find('> ol.dd-list').length == 0) {
          parent_el.append('<ol class="dd-list"></ol>');
        }
        parent_el.find('> ol.dd-list').append($(this));
      } else {
        var parents = $(this).parent().closest('li');
        if(parents.length > 0) {
          var parent_id = parents.find('tr')[0].id;
          if(parent_id != id) {
            $('#id_'+id+'-source_link').val(parent_id);
          }
        } else {
          $('#id_'+id+'-source_link').val('ROOT');
        }
      }
    }
    order += 1;
  });
  nest_init = true;
}

var out_icon = 'glyphicon-eye-open';
var nout_icon = 'glyphicon-wrench';
function the_eye_of_output(eye, input) {
  // Provide a show/hide button for output checkbox
  eye.click(function() {
    if(input.prop("checked")) {
      input.prop("checked", false);
      eye.removeClass(out_icon).addClass(nout_icon);
    } else {
      input.prop("checked", true);
      eye.removeClass(nout_icon).addClass(out_icon);
    }
  }).click().click();
}


function update_mechanism(event) {
  if(this.id.startsWith('mechanisms-') && !this.id.endsWith('empty')) {
    var tr = $(this);
    var id = tr[0].id;
    var mid = '#'+id+'-dd';
    if($(mid).length == 0) {
      // Create here
      var index  = parseInt(mid.split('-')[1]) + 1;
      var holder = $('<li class="dd-item dd3-item" data-id="'+index+'" id="'+mid+'"></li>');
      var handle = $('<div class="dd-handle dd3-handle"></div>');
      var output = $('<div class="dd3-output glyphicon"></div>');
      var del = $('<div class="dd3-delete glyphicon glyphicon-minus"></div>');
      var table = $('<div class="dd3-content"></div>');
      holder.append(handle);
      holder.append(del);
      holder.append(output);
      holder.append(table);
      table.append(tr);
      $('#mg-root').append(holder);
      holder.hide();

      // Add delete function for this
      del.click(function(event) {
        // Find all children and process them first to cache any new/existing mixes
        holder.find('> ol > li > div.dd3-delete').click();
        // Now actually do the delete function for this element.
        var checkbox = table.find('td.delete input');
        if(checkbox.length == 0) {
          // New mechanism, delete it!
          holder.remove();
        } else {
          // Existing mechanism, mark for delete and move it out of the tree.
          checkbox.prop('checked', true);
          $('#mechanisms-deleted').append(holder);
          table.prepend('<h1>DELETED</h1>');
          holder.hide();
        }
      });

      // Connect the eye icon to the output input field.
      the_eye_of_output(output, table.find('.field-output input'));

      // Show and hide the right options for each mechanism
      holder.find('.field-mechanism_id select').change(function(event) {
        update_options(table, null, 'td', 'm', $(this).val());
      }).change();

      tr.find('td').each(function() {
        // Attach all the question marks with the help texts to each field.
        var pos = $(this).index() - 1; // -1 for the paragraph tag
        $('#mechanisms-group fieldset table th:eq('+pos+') img').clone().appendTo(this);
      });

      // Hide a lot of the stuff
      tr.find('.original').hide();
      tr.find('.delete').hide();
      tr.find('.field-output').hide();
      tr.find('.field-source').hide();
      tr.removeClass();

      holder.fadeIn(600);
    }
  }
}

function update_options(root, set, row, name, value) {
  /*
   * Hide/show relevant section's controls
   *
   * root = the base container
   * set =  a grouping parent element to show/hide (if available)
   * row = the container for each element to show/hide
   * name = the overall set being manipulated
   */
  var items = root.find('[data-target="'+name+'"]');
  var shown = items.filter('[data-target-id*="\''+value+'\'"]');
  var hiddn = items;

  if(set) {
    if(shown.length == 0) {
      items.closest(set).fadeOut(hide_timeout, function() {
        hiddn.closest(row).addClass('na_option');
      });
    } else {
      items.closest(set).fadeIn(function() {
        hiddn.closest(row).addClass('na_option', hide_timeout);
        shown.closest(row).removeClass('na_option', 600);
      });
    }
  } else {
    hiddn.closest(row).hide(0, function() {
      shown.closest(row).removeClass('na_option', 0);
      shown.closest(row).show();
    });
  }
}

})(django.jQuery);
