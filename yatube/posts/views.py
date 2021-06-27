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


def get_author_card_data(author, request):
    post_count = author.posts.count()
    following = Follow.objects.filter(
        user_id=request.user.id,
        author_id=author.id
    )
    following_number = User.objects.filter(following__author=author).count()
    follower_number = User.objects.filter(follower__user=author).count()
    return {
        'post_count': post_count,
        'profile': author,
        'following': following,
        'following_number': following_number,
        'follower_number': follower_number,
    }


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = get_author_card_data(author, request)
    context.update(page=page)
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related('author'),
                             id=post_id, author__username=username)
    author = post.author
    form = CommentForm()
    comments = post.comments.all()
    context = get_author_card_data(author, request)
    context.update(post=post,
                   form=form,
                   comments=comments)
    return render(request, 'post.html', context)


def add_comment(request, username, post_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post_id = post_id
        comment.author_id = request.user.id
        comment.save()
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    """Отображает персональную ленту пользователя"""
    post_list = Post.objects.filter(author__following__user=request.user.id)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html',
                  {'page': page}
                  )


@login_required
def profile_follow(request, username):
    if username != request.user.username:
        Follow.objects.create(
            user_id=request.user.id,
            author_id=get_object_or_404(User, username=username).id
        )
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.get(
        user_id=request.user.id,
        author_id=get_object_or_404(User, username=username).id
    ).delete()
    return redirect('profile', username)


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
