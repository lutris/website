/* global $ */

(function() {
  $(function() {
    $("#game-filter").on('keyup', function() {
      var query;
      query = this.value.toLowerCase();
      return $('.game-title').each(function() {
        var listElement, name;
        name = $(this).html().toLowerCase();
        listElement = $(this).parent().parent();
        if (name.indexOf(query) === -1) {
          return listElement.hide();
        } else {
          return listElement.show();
        }
      });
    });
    return $(".fold-btn").click(function() {
      $("#advanced-search-panel .collapsable-panel").toggleClass('active');
      if ($("#advanced-search-panel .collapsable-panel").hasClass('active')) {
        return $("#advanced-search-panel .fold-indicator").html("&#9660;");
      } else {
        return $("#advanced-search-panel .fold-indicator").html("&#9658;");
      }
    });
  });
}).call(this);
