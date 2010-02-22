jQuery(document).ready(function() {
  $('div.inline-group').sortable({
    /*containment: 'parent',
    zindex: 10,*/
    items: 'div.inline-related',
    handle: 'h3:first',
    update: function() {
      /* fix the order for all filled-in inlines */
      $(this).find('div.inline-related').each(function(i) {
        var r = $(this);
        var f = function(t, nm) { return r.find(t+'[name$='+nm+']').val(); };
        if (f('textarea','body') || f('input','image') || f('select','section')) {
          r.find('input[id$=order]').val(i+1);
        }
      });
    }
  });
  $('div.inline-related h3').css('cursor', 'move');
  $('div.inline-related').find('input[id$=order]').parent('div').parent('div').hide();
});
/* vi: set sw=2 ts=2 sts=2 tw=79 ai et: */
