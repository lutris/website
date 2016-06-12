# pylint: disable=E1120, C0103
from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from games import views


urlpatterns = patterns(
    'games.views',
    url(r'^$', views.GameList.as_view(),
        name='game_list'),
    url(r'^year/(\d+)/$', views.GameListByYear.as_view(),
        name='games_by_year'),
    url(r'^genre/([\w-]+)/$', views.GameListByGenre.as_view(),
        name='games_by_genre'),
    url(r'^by/([\w-]+)/$', views.GameListByCompany.as_view(),
        name='games_by_company'),
    url(r'^platform/(?P<slug>[\w\-]+)/$', views.GameListByPlatform.as_view(),
        name="games_by_plaform"),
    url(r'^add-game/$', 'submit_game',
        name='game-submit'),
    url(r'^game-submitted',
        TemplateView.as_view(template_name='games/submitted.html'),
        name="game-submitted"),

    url('^game-issue', 'submit_issue',
        name='game-submit-issue'),

    url(r'banner/(?P<slug>[\w\-]+).jpg', 'get_banner',
        name='get_banner'),
    url(r'icon/(?P<slug>[\w\-]+).png', 'get_icon',
        name='get_icon'),
    url(r'install/(?P<id>[\d]+)/view$', 'view_installer',
        name='view_installer'),
    url(r'install/(?P<id>[\d]+)/fork$', 'fork_installer',
        name='fork_installer'),
    url(r'install/(?P<slug>[\w\-]+)/$', 'get_installers',
        name='get_installers'),

    # Legacy URLs, do be removed with Lutris 0.4
    url(r'install/(?P<slug>[\w\-]+).yml$', 'serve_installer',
        name='serve_installer'),  # Legacy yaml installer url
    url(r'install/(?P<slug>[\w\-]+).jpg$', 'serve_installer_banner',
        name='serve_installer_banner'),  # Legacy banner url
    url(r'install/icon/(?P<slug>[\w\-]+).png$', 'serve_installer_icon',
        name='serve_installer_icon'),  # Legacy icon url

    url(r'(?P<slug>[\w\-]+)/installer/new/$', "new_installer",
        name="new_installer"),
    url(r'(?P<slug>[\w\-]+)/installer/edit/$', 'edit_installer',
        name='edit_installer'),
    url(r'(?P<slug>[\w\-]+)/installer/publish/$', 'publish_installer',
        name='publish_installer'),
    url(r'(?P<slug>[\w\-]+)/installer/complete/$', 'installer_complete',
        name='installer_complete'),
    url(r'installer/feed/$', views.InstallerFeed(), name='installer_feed'),

    url(r'([\w\-]+)/screenshot/add/', 'screenshot_add',
        name='screenshot_add'),
    url(r'screenshot/(?P<id>\d+)/publish/$', 'publish_screenshot',
        name='publish_screenshot'),

    url(r'game-for-installer/(?P<slug>[\w\-]+)/', 'game_for_installer',
        name='game_for_installer'),
    url(r'(?P<slug>[\w\-]+)/$', "game_detail",
        name="game_detail"),
)
