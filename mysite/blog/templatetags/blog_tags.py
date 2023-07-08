from ..models import Post
from django import template
from django.utils.safestring import mark_safe
import markdown
from django.db.models import Count

# 定义标签库 register
register = template.Library()


@register.simple_tag
def total_posts():
    return Post.published.count()


@register.inclusion_tag('blog/post/latest_posts.html')
def show_lates_posts(counts=5):
    latest_posts = Post.published.order_by('-publish')[:counts]
    return {'latest_posts': latest_posts}


@register.simple_tag
def get_most_commented_post(counts=5):
    return Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:counts]


@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))
