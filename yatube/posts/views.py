from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    #  Вытаскиваем номер страницы из адресной строки
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html',
                  {'page': page, }
                  )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html',
                  {'group': group,
                   'page': page, }
                  )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_count = author.posts.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html',
                  {'author': author,
                   'post_count': post_count,
                   'page': page, }
                  )


def post_view(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related('author'),
                             id=post_id, author__username=username)
    author = post.author
    post_count = author.posts.count()
    form = CommentForm()
    comments = post.comments.all()
    return render(request, 'post.html',
                  {'author': author,
                   'post_count': post_count,
                   'post': post,
                   'form': form,
                   'comments': comments, }
                  )


def add_comment(request, username, post_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post_id = post_id
        comment.author_id = request.user.id
        comment.save()
        return redirect(request.path, username, post_id)


@login_required
def follow_index(request):
    """Отображает персональную ленту пользователя"""
    post_list = request.user.following.posts
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html',
                  {'page': page})


@login_required
def profile_follow(request, username):
    Follow.objects.create(
        user_id=request.user.id,
        author_id=get_object_or_404(User, username=username).id
    )
    return redirect(request.path)


@login_required
def profile_unfollow(request, username):
    Follow.objects.get(
        user_id=request.user.id,
        author_id=get_object_or_404(User, username=username).id
    ).delete()
    return redirect(request.path)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author_id = request.user.id
        post.save()
        return redirect('index')
    return render(request, 'post_form.html',
                  {'form': form,
                   'title': 'Новая запись',
                   'header': 'Добавить запись', }
                  )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user.id != post.author_id:
        return redirect('post', username, post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'post_form.html',
                  {'form': form,
                   'header': 'Редактировать запись',
                   'title': 'Редактировать запись',
                   'edit': True, }
                  )


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)