from django.shortcuts import render
from common.models import News
from games.models import Game


def home(request):
    """Homepage view"""
    featured = Game.objects.exclude(title_logo__exact="")[:5]
    news = News.objects.all()[:5]
    download_type = "Ubuntu"
    return render(request, 'home.html',
                  {'featured': featured, 'news': news,
                   'download_type': download_type})


def news_archives(request):
    news = News.objects.all()
    return render(request, 'news.html', {'news': news})
