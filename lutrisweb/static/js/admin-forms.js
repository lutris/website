filters = function() {
    $('.confirm_text').toggle(
        $('#id_confirm_enabled').is(':checked')
    );
};

$(function(){
alert('plop');
    filters();
    $('#id_confirm_enabled').click(filters);
});



