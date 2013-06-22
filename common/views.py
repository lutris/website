from django.shortcuts import render
from django.views.generic import DetailView

from common.models import News
from games.models import Game


def home(request):
    """Homepage view"""
    news = News.objects.all()[:5]
    latest_games = Game.objects.published().order_by('-created')[:5]
    return render(request, 'home.html', {
        'latest_games': latest_games,
        'news': news,
    })


def news_archives(request):
    news = News.objects.all()
    return render(request, 'news.html', {'news': news})


class NewsDetails(DetailView):
    queryset = News.objects.all()
    template_name = 'common/news_details.html'
    context_object_name = 'news'

    def get_object(self):
        obj = super(NewsDetails, self).get_object()
        return obj
