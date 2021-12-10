/* global $ */
import 'bootstrap';
import './admin-forms';
import 'select2';
import 'django-select2';
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
    show_notifications();
})
