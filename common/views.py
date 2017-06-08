from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.syndication.views import Feed
from django.conf import settings
from django.views.generic import DetailView, TemplateView

from common.forms import UploadForm
from common.models import News


def home(request):
    """Homepage view"""
    try:
        article = News.objects.latest('pk')
    except News.DoesNotExist:
        article = None
    return render(request, 'home.html', {
        'article': article,
        'client_version': settings.CLIENT_VERSION
    })


class Downloads(TemplateView):
    template_name = "common/downloads.html"

    def get_context_data(self, **kwargs):
        context = super(Downloads, self).get_context_data(**kwargs)
        context['version'] = settings.CLIENT_VERSION
        context['download_url'] = 'https://lutris.net/releases/'
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
        return item.content.rendered

    def item_link(self, item):
        return item.get_absolute_url()


def upload_file(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        upload = form.save(commit=False)
        upload.uploaded_by = request.user
        upload.save()
        return HttpResponseRedirect('/')
    return render(request, 'common/upload.html', {'form': form})


def error_testing(request):
    raise ValueError("Making things crash")
