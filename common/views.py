import copy
from django.shortcuts import render
from django.conf import settings
from common.models import News
from games.models import FeaturedGame, Game


def get_download_links(user_agent):
    systems = ['ubuntu', 'fedora', 'linux']
    downloads = copy.copy(settings.DOWNLOADS)
    main_download = None
    for system in systems:
        if system in user_agent:
            main_download = {system: settings.DOWNLOADS[system]}
            downloads.pop(system)
    if not main_download:
        main_download = {'linux': downloads.pop('linux')}
    return (main_download, downloads)


def home(request):
    """Homepage view"""
    featured = FeaturedGame.objects.all()
    news = News.objects.all()[:5]
    latest_games = Game.objects.published().order_by('-created')[:5]
    user_agent = request.META['HTTP_USER_AGENT'].lower()
    main_download, downloads = get_download_links(user_agent)
    return render(request, 'home.html', {
        'featured_games': featured,
        'latest_games': latest_games,
        'news': news,
        'user_agent': user_agent,
        'main_download': main_download,
        'downloads': downloads
    })


def news_archives(request):
    news = News.objects.all()
    return render(request, 'news.html', {'news': news})


def news_details(request, slug):
    news = News.objects.get(slug=slug)
    return render(request, 'common/news_details.html', {'news': news})
