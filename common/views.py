from django.shortcuts import render
from common.models import News
from games.models import FeaturedGame


def home(request):
    """Homepage view"""
    featured = FeaturedGame.objects.all()
    news = News.objects.all()[:5]
    download_type = "Ubuntu"
    return render(request, 'home.html',
                  {'featured_games': featured,
                   'news': news,
                   'download_type': download_type})


def news_archives(request):
    news = News.objects.all()
    return render(request, 'news.html', {'news': news})


def news_details(request, slug):
    news = News.objects.get(slug=slug)
    return render(request, 'common/news_details.html', {'news': news})
