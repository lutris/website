set_active_menu = () ->
  url = window.location.pathname
  $('#main-nav li').removeClass('active')
  if url == "/"
    menu_index = 0
  else if url.substr(0, 6) == '/about'
    menu_index = 1
  else if url.substr(0, 10) == '/downloads'
    menu_index = 2
  else if url.substr(0, 6) == '/games'
    menu_index = 3
  else if url.slice(-8) == 'library/'
    menu_index = 4
  else if url.slice(-6) == 'login/'
    menu_index = 4
  else if url.slice(-9) == 'register/'
    menu_index = 5
  else if url.substr(0, 5) == '/user'
    menu_index = 5
  $('#main-nav li').eq(menu_index).addClass('active')

$ ()->
  set_active_menu()
