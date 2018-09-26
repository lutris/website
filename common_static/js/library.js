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

function applyLibraryFilter(event) {
    var ordering = $("<input>").attr("type", "hidden").attr("name", "ordering").val($('#order_by').val());
    $('#library_filter_form').append($(ordering));
    if ($('#paginate_by').length > 0) {
        var paginate_by = $("<input>").attr("type", "hidden").attr("name", "paginate_by").val($('#paginate_by').val());
        $('#library_filter_form').append($(paginate_by));
    }
    $('#library_filter_form').submit();
}

function clearLibraryFilter(event) {
    $('#id_search').val('');
    $('#id_platform').val([]).change();
    $('#id_genre').val([]).change();
    var order_by = $('#order_by').val();
    var paginate_by = $('#paginate_by').val();
    if (paginate_by !== undefined)
        window.location.href = '?paginate_by=' + paginate_by + '&ordering=' + order_by
    else
        window.location.href = '?ordering=' + order_by
}

function changeLibraryPaginateCount(event) {
    var paginate_by = $('#paginate_by').val();
    var filter = $('#paginate_by').data('filter');
    var order_by = $('#order_by').val();
    window.location.href = '?paginate_by=' + paginate_by + '&ordering=' + order_by + filter;
}

function changeLibraryOrderBy(event) {
    var order_by = $('#order_by').val();
    var paginate_by = $('#paginate_by').val();
    var filter = $('#order_by').data('filter');
    if (paginate_by !== undefined)
        window.location.href = '?paginate_by=' + paginate_by + '&ordering=' + order_by + filter;
    else
        window.location.href = '?ordering=' + order_by + filter;
}

function changeLibraryPage(event) {
    if (event.key === 'Enter') {
        var source = $(event.currentTarget);
        var url = source.data('url');
        var max_page = source.data('maxPage');
        var target_page = source.val();
        if (target_page > max_page)
            target_page = max_page;
        if (target_page < 1)
            target_page = 1;
        window.location.href = '?page=' + target_page + url
    }
}