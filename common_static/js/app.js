/* global $ */

(function() {
  var setActiveMenu = function() {
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
