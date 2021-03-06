import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.form = PostForm()
        PostCreateFormTests.user = User.objects.create(username="sergeys")
        PostCreateFormTests.post = Post.objects.create(
            text="Edit me",
            author_id=PostCreateFormTests.user.id
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """ Валидная форма создает запись в Post """
        posts_count = Post.objects.count()
        form_data = {
            "text": "Hello test"
        }
        response = self.authorized_client.post(
            reverse("new"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"]
            ).exists()
        )

    def test_create_post_with_image(self):
        """Форма с картинкой создает запись в Post"""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )
        form_data = {
            "text": "Hello image",
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("new"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"]
            ).exists()
        )
        self.assertIsNotNone(
            Post.objects.get(
                text=form_data["text"]
            ).image
        )

    def test_edit_post(self):
        """Пост можно изменить"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Edit text"
        }
        response = self.authorized_client.post(
            reverse("post_edit",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("post", kwargs={
            "username": self.user.username,
            "post_id": self.post.id
        }))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"]
            ).exists()
        )

    def test_cant_create_void_post(self):
        """Нельзя создать пустой пост"""
        posts_count = Post.objects.count()
        form_data = {"text": ""}
        response = self.authorized_client.post(
            reverse("new"),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            "form",
            "text",
            "Обязательное поле."
        )
        self.assertEqual(response.status_code, 200)

    def test_guest_cant_do_post(self):
        posts_count = Post.objects.count()
        form_data = {"text": "i want to post"}
        response = self.guest_client.post(
            reverse("new"),
            data=form_data,
            follow=True
        )
        login_url = reverse('login')
        self.assertRedirects(response, f"{login_url}?next={reverse('new')}")
        self.assertEqual(Post.objects.count(), posts_count)

    def test_form_labels(self):
        text_label = PostCreateFormTests.form.fields["text"].label
        self.assertEqual(text_label, "Текст")
        group_label = PostCreateFormTests.form.fields["group"].label
        self.assertEqual(group_label, "Группа")

    def test_form_help_text(self):
        text_help_text = PostCreateFormTests.form.fields["text"].help_text
        self.assertEqual(text_help_text, "Пишите, что захотите")


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        CommentFormTest.author = User.objects.create(username="ponistar")
        CommentFormTest.user = User.objects.create(username="user")
        CommentFormTest.post = Post.objects.create(
            text="Comment it please",
            author_id=CommentFormTest.author.id,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_can_comment(self):
        """Комментарий создается"""
        comments_count = Comment.objects.count()
        form_data = {"text": "ha ha"}
        kwargs = {"username": self.author.username, "post_id": self.post.id}
        response = self.authorized_client.post(
            reverse("comment", kwargs=kwargs),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("post", kwargs=kwargs))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comment = response.context["comments"][0]
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.text, form_data["text"])

    def test_only_authorized_client_can_comment(self):
        self.guest_client.post(
            reverse("comment", kwargs={"username": self.author.username,
                                       "post_id": self.post.id}),
            data={"text": "comment text"},
            follow=True
        )
        self.assertFalse(Comment.objects.exists())
