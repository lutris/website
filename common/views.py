from django.shortcuts import render
from django.contrib.syndication.views import Feed
from django.conf import settings
from django.views.generic import DetailView, TemplateView

from common.models import News


def home(request):
    """Homepage view"""
    news = News.objects.all()[:5]
    return render(request, 'home.html', {
        'news': news,
        'client_version': settings.CLIENT_VERSION
    })


class Downloads(TemplateView):
    template_name = "common/downloads.html"

    def get_context_data(self, **kwargs):
        context = super(Downloads, self).get_context_data(**kwargs)
        context['version'] = settings.CLIENT_VERSION
        context['download_url'] = 'http://lutris.net/releases/'
        return context


def news_archives(request):
    news = News.objects.all()
    return render(request, 'news.html', {'news': news})


class NewsDetails(DetailView):
    queryset = News.objects.all()
    template_name = 'common/news_details.html'
    context_object_name = 'news'

    def get_object(self, queryset=None):
        return super(NewsDetails, self).get_object()


class NewsFeed(Feed):
    title = "Lutris news"
    link = '/news/'
    description = u"Latest news about Lutris"
    feed_size = 20

    def items(self):
        return News.objects.order_by("-publish_date")[:self.feed_size]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return item.get_absolute_url()


def error_testing(request):
    raise ValueError("Making things crash")
