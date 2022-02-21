from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow

TEXT_PREVIEW_SYMBOLS = 30
POSTS_PER_PAGE = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': 'Последние обновления на сайте',
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': f'Последние обновления в группе {group.title}',
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    user_posts = user.posts.all()
    paginator = Paginator(user_posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_amount = user_posts.count()
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=user
        ).exists()
    else:
        following = False
    context = {
        'title': f'Профайл пользователя {user.first_name} {user.last_name}',
        'author': user,
        'user_posts': user_posts,
        'post_amount': post_amount,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        input_post = form.save(commit=False)
        input_post.author = request.user
        input_post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(
        request,
        'posts/create_post.html',
        {
            'form': form,
            'is_edit': True,
            'post': post
        }
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_amount = Post.objects.all().filter(author=post.author).count()
    comments = Comment.objects.filter(post=post)
    comment_form = CommentForm(
        request.POST or None
    )
    context = {
        'title': post.text[:TEXT_PREVIEW_SYMBOLS],
        'post': post,
        'post_amount': post_amount,
        'comments': comments,
        'form': comment_form

    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related('author').filter(
        author__following__user=request.user
    )
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': 'Последние обновления от авторов, на которых вы подписаны',
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if (
        request.user != user
        and not Follow.objects.filter(
            user=request.user,
            author=user
        ).exists()
    ):
        Follow.objects.create(
            user=request.user,
            author=user
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    )
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username=username)
