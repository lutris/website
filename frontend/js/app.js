/* global $ */
import 'bootstrap';
import './admin-forms';
import 'select2';
import 'django-select2';
import * as blueimp_gallery from 'blueimp-gallery/js/blueimp-gallery';
import alertify from 'alertifyjs';
import Cookies from 'js-cookie';
import 'bootstrap-icons/font/bootstrap-icons.css';

let csrftoken = Cookies.get('csrftoken');
let notification_queue = JSON.parse(sessionStorage.getItem('notification_queue')) || [];

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function checkBeforeSend(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
}

function queue_notification(status, message) {
    if (status && message) {
        notification_queue.push({status: status, message: message});
        sessionStorage.setItem('notification_queue', JSON.stringify(notification_queue));
    }
}

function onAjaxPostDone(data) {
    if (data.url) {
        queue_notification(data.status, data.message);
        window.location.replace(data.url);
    }
    else
        show_notification(data.status, data.message);
}

function onAjaxFail(jqXHR, textStatus, errorThrown) {
    alertify.error(jqXHR.responseText);
}

function configure_alertify() {
    alertify.defaults.transition = "fade";
    alertify.defaults.theme.ok = "btn btn-primary";
    alertify.defaults.theme.cancel = "btn btn-danger";
    alertify.defaults.theme.input = "form-control";
    alertify.defaults.movable = false;
    alertify.defaults.notifier.position = 'top-left';
    alertify.defaults.notifier.delay = 0;
}

function link_form_submit(modal_id, form_id, url, has_files) {
    let $form = $(form_id);
    let $modal = $(modal_id);
    $form.on('submit', function (event){
        event.preventDefault();
        if ($form[0].reportValidity()){
            if (has_files){
                let formData = new FormData($form[0]);
                $.post({
                    url: url,
                    data: formData,
                    processData: false,
                    contentType: false,
                    dataType: "json"
                }).done(function (response){
                    if (response.status === 'invalid') {
                        $modal.find('.modal-body').html(response.html);
                        link_form_submit(modal_id, form_id, url, has_files);
                    } else {
                        $modal.modal('hide');
                        onAjaxPostDone(response);
                    }
                });
            } else {
                $.post({
                    url: url,
                    data: $form.serialize(),
                }).done(function (response){
                    if (response.status === 'invalid') {
                        $modal.find('.modal-body').html(response.html);
                        link_form_submit(modal_id, form_id, url, has_files);
                    } else {
                        $modal.modal('hide');
                        onAjaxPostDone(response);
                    }
                });
            }
        }
    });
}

function configure_modal_form(modal_id, form_id, has_files=false) {
    $(modal_id).on('show.bs.modal', function (event) {
        let $modal = $(this);
        let $modal_body = $modal.find('.modal-body');
        let url = $(event.relatedTarget).data('url');
        $.get({
            url: url,
        }).done(function (response){
            $modal_body.html(response);
            let $form = $modal.find('form');
            $form.attr('id', form_id.substring(1));
            $form.attr('action', url);
            link_form_submit(modal_id, form_id, url, has_files);
        }).fail(function (){
            alertify.error('Failed to retrieve modal data.', '5');
            $modal.modal('hide');
        })
    });
}

function configure_modals() {
    configure_modal_form('#modal_login', '#form_login');
    configure_modal_form('#modal_register', '#form_register');
    configure_modal_form('#modal_password_change', '#form_password_change');
    configure_modal_form('#modal_password_reset', '#form_password_reset');
    configure_modal_form('#modal_profile_edit', '#form_profile_edit', true);
}

function show_notification(status, message) {
    if (status && message) {
        switch (status) {
            case 'success':
                alertify.success(message, '5');
                break;
            case 'info':
                alertify.message(message, '5');
                break;
            case 'warning':
                alertify.warning(message);
                break;
            case 'error':
                alertify.error(message);
                break;
            default:
                break;
        }
    }
}

function show_notifications(){
    $('#django_messages li').each(function () {
        let status = $(this).data('tags');
        let message = $(this).text();
        show_notification(status, message);
    })

    notification_queue.forEach(function (notification) {
        show_notification(notification.status, notification.message);
    });
    notification_queue = [];
    sessionStorage.removeItem('notification_queue');
}

$(window).on('load', function () {
    $.ajaxSetup({
      beforeSend: checkBeforeSend,
      error: onAjaxFail,
    });
    configure_alertify();
    configure_modals();
    show_notifications();
})
