$ () ->
  $("#game-filter").on('keyup', (evt) ->
    query = @.value.toLowerCase()
    $('.game-title').each(()->
      name = $(@).html().toLowerCase()
      list_elem = $(@).parent().parent()
      if name.indexOf(query) == -1
        list_elem.hide()
      else
        list_elem.show()
    )
  )

  $(".fold-btn").click((e)->
    $("#advanced-search-panel .collapsable-panel").toggleClass('active')
    if $("#advanced-search-panel .collapsable-panel").hasClass('active')
      $("#advanced-search-panel .fold-indicator").html("&#9660;")
    else
      $("#advanced-search-panel .fold-indicator").html("&#9658;")
  )
