from django.conf.urls.defaults import patterns, url
from games.views import GameList, GameListByYear


urlpatterns = patterns('games.views',
    url(r'^$', GameList.as_view(), name='game_list'),
    url(r'^year/(\d+)/$', GameListByYear.as_view(), name='game_list_by_year'),
    url(r'^genre/(?P<genre_slug>[\w\-]+/$)', 'game_list_by_genre',
        name='game_list_by_genre'),
    url(r'^runner/(?P<runner_slug>[\w\-]+)$', 'games_by_runner'),
    #url(r'^developer/(?P<developer_slug>[\w\-]+)$', views.games_by_developer),
    #url(r'^publisher/(?P<publihser_slug>[\w\-]+)$', views.games_by_publisher),
    #url(r'^platform/(?P<platform_slug>[\w\-]+)$', views.games_by_platform),
    url(r'install/(?P<slug>[\w\-]+).yml', 'serve_installer',
        name='serve_installer'),
    url(r'(?P<slug>[\w\-]+)/installer/new$', "new_installer",
        name="new_installer"),
    url(r'(?P<slug>[\w\-]+)/installer/edit$', 'edit_installer',
        name='edit_installer'),
    url(r'(?P<slug>[\w\-]+)/installer/complete$', 'installer_complete',
        name='installer_complete'),
    url(r'(?P<slug>[\w\-]+)/$', "game_detail", name="game_detail"),
)
