from django.shortcuts import render, get_list_or_404, get_object_or_404
from .models import Post
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
# from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchFrom
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count
# from django.urls import reverse, redirect
# Create your views here.


# class PostListView(ListView):
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        # print(type(tag[0]))
        print(object_list)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 3)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'page': page, 'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_list_or_404(Post, slug=post, status='published',
                           publish__year=year, publish__month=month, publish__day=day)[0]
    # print(post)
    # print('-----------------------------------------------------------------')
    comments = post.comments.filter(active=True)
    new_comments = None
    comment_form = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comments = comment_form.save(commit=False)
            new_comments.post = post
            new_comments.save()
        else:
            comment_form = CommentForm()
    # print(comments.count())
    post_tags_ids = post.tags.values_list('id', flat=True)
    # print(post_tags_ids)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, 'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'new_comments': new_comments,
                   'comment_form': comment_form,
                   'commends_count': comments.count(),
                   'similar_posts': similar_posts})


def post_share(request, id):
    post = get_list_or_404(Post, id=id, status='published')[0]
    # print(post.title)
    sent = False
    # print(post)
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read "f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n"f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'wqj15515109531@163.com', [cd['to']])
            sent = True
            # print('发送成功')
    else:
        form = EmailPostForm()
    # if sent:
    #     print('发送成功')
    # else:
    #     return redirect(reverse('blog/post/detail.html', {'post': post}))
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})


def post_search(request):
    form = SearchFrom()
    query = None
    results = []
    request.encoding = 'utf-8'
    if 'query' in request.GET:
        form = SearchFrom(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            # search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            # search_query = SearchQuery(query)
            results = Post.published.annotate(similarity=TrigramSimilarity('title',query)).filter(similarity__gt=0.1).order_by('-similarity')
            # results = Post.published.annotate(search=search_vector, rank=SearchRank(search_vector, search_query)).filter(rank_gte=0.3).order_by('-rank')
    return render(request, 'blog/post/search.html', {'form': form, 'query': query, 'results': results})
