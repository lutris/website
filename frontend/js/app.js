/* global $ */
import 'bootstrap';
import './library';
import './admin-forms';
import 'select2';
import 'django-select2';
import 'ace-builds';
import '@fortawesome/fontawesome-free/js/fontawesome';
import '@fortawesome/fontawesome-free/js/solid';
import '@fortawesome/fontawesome-free/js/regular';
import '@fortawesome/fontawesome-free/js/brands';
import * as blueimp_gallery from 'blueimp-gallery/js/blueimp-gallery';

(function() {

  /**
   * Return the cookie value referenced by name
   * @param {string} name - Name of the cookie to return
   * @returns {string} value of the cookie
   */
  function getCookie(name) {
    var cookieValue = null;
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = $.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
    return cookieValue;
  }

  /**
   * Return true if the method does not require CSRF protection
   * @param {string} method - Name of the method
   * @returns {Boolean} True if the method is CSRF safe
   */
  function isCsrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }


  /**
   * Returns true if url is the same origin of current website
   * @param {string} url - URL to test
   * @returns {Boolean} Whether the url is same origin
   */
  function isSameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var srOrigin = '//' + host;
    var origin = protocol + srOrigin;
    // Allow absolute or scheme relative URLs to same origin
    return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
      (url === srOrigin || url.slice(0, srOrigin.length + 1) === srOrigin + '/') ||
      // or any other URL that isn't scheme relative or absolute i.e relative.
      !(/^(\/\/|http:|https:).*/.test(url));
  }

  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!isCsrfSafeMethod(settings.type) && isSameOrigin(settings.url)) {
        // Send the token to same-origin, relative URLs only.
        // Send the token only if the method warrants CSRF protection
        // Using the CSRFToken value acquired earlier
        var csrftoken = getCookie('csrftoken');
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
    }
  });
}).call(this);

$(window).on('load', function () {
  if ($("#blueimp-gallery-carousel").length) {
    blueimp_gallery(document.getElementById('carousel_links').getElementsByTagName('a'), {
      container: '#blueimp-gallery-carousel',
      carousel: true,
      toggleControlsOnSlideClick: false,
      stretchImages: true,
      onslide: function (index, slide) {
        let text = this.list[index].getAttribute('data-description', ''),
            url = this.list[index].getAttribute('data-link', '#'),
            node = $(this.container.find('#carousel_game_link'));
        node.attr('href', url);
        node.text(text);
      }
    })
  }
})
