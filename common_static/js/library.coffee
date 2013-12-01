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
