/* global $ */

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

  function setActiveMenu() {
    var menuIndex, url;
    url = window.location.pathname;
    $('#main-nav li').removeClass('active');
    if (url === "/") {
      menuIndex = 0;
    } else if (url.substr(0, 6) === '/about') {
      menuIndex = 1;
    } else if (url.substr(0, 10) === '/downloads') {
      menuIndex = 2;
    } else if (url.substr(0, 6) === '/games') {
      menuIndex = 3;
    } else if (url.slice(-8) === 'library/') {
      menuIndex = 4;
    } else if (url.slice(-6) === 'login/') {
      menuIndex = 4;
    } else if (url.slice(-9) === 'register/') {
      menuIndex = 5;
    } else if (url.substr(0, 5) === '/user') {
      menuIndex = 5;
    }
    return $('#main-nav li').eq(menuIndex).addClass('active');
  };

  $(function() {
    return setActiveMenu();
  });

}).call(this);
