/* global $ */

(function() {
  $('#id_q').keypress(onSearchKeyPressed);
}).call(this);

function onSearchKeyPressed(event) {
    if (event.which == 13) {
        applyLibraryFilter();
    }
}

function applyLibraryFilter() {
    var ordering = $("<input>").attr("type", "hidden").attr("name", "ordering").val($('#order_by').val());
    $('#library_filter_form').append($(ordering));
    if ($('#paginate_by').length > 0) {
        var paginate_by = $("<input>").attr("type", "hidden").attr("name", "paginate_by").val($('#paginate_by').val());
        $('#library_filter_form').append($(paginate_by));
    }
    $('#library_filter_form').submit();
}

function clearLibraryFilter() {
    $('#id_q').val('');
    $('#id_platforms').val([]).change();
    $('#id_genres').val([]).change();
    $('#id_companies').val([]).change();
    var order_by = $('#order_by').val();
    var paginate_by = $('#paginate_by').val();
    if (paginate_by !== undefined)
        window.location.href = '?paginate_by=' + paginate_by + '&ordering=' + order_by
    else
        window.location.href = '?ordering=' + order_by
}

function changeLibraryPaginateCount() {
    var paginate_by = $('#paginate_by').val();
    var filter = $('#paginate_by').data('filter');
    var order_by = $('#order_by').val();
    window.location.href = '?paginate_by=' + paginate_by + '&ordering=' + order_by + filter;
}

function changeLibraryOrderBy() {
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
