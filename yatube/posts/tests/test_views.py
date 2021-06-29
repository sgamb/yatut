import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PostPagesTests.user = User.objects.create(
            username="serges"
        )
        PostPagesTests.group = Group.objects.create(
            title="test group",
            slug="test-slug"
        )
        PostPagesTests.post = Post.objects.create(
            text="Test post text",
            author_id=PostPagesTests.user.id,
            group_id=PostPagesTests.group.id
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_templates(self):
        """Страницы используют соответствующие шаблоны"""
        templates_page_names = {
            "index.html": reverse("index"),
            "group.html": reverse("group", kwargs={"slug": "test-slug"}),
            "post_form.html": reverse("new"),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_view_pass_correct_context(self):
        """Контекст шаблона index.html — страница с постами"""
        response = self.authorized_client.get(reverse("index"))
        self.assertIsNotNone(response.context.get("page"))
        first_post = response.context.get("page").object_list[0]
        self.assertIsInstance(first_post, Post)
        self.assertEqual(first_post, self.post)

    def test_group_view_pass_correct_content(self):
        """Контекст шаблона group_page.html — страница с постом и группа"""
        response = self.authorized_client.get(
            reverse("group", kwargs={"slug": "test-slug"})
        )
        self.assertIsNotNone(response.context.get("page"))
        first_post = response.context.get("page").object_list[0]
        self.assertIsInstance(first_post, Post)
        self.assertEqual(first_post, self.post)
        self.assertEqual(response.context.get("group"), self.group)

    def test_new_post_view_show_correct_context(self):
        """Шаблон post_form.html сформирован с правильным контекстом
        при добавлении поста"""
        response = self.authorized_client.get(reverse("new"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get("title"), "Новая запись")
        self.assertEqual(response.context.get("header"), "Добавить запись")

    def test_edit_view_pass_correct_context(self):
        """Шаблон post_form.html сформирован с правильным контекстом
        при изменении поста"""
        response = self.authorized_client.get(
            reverse("post_edit", kwargs={"username": self.user.username,
                    "post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get("title"),
                         "Редактировать запись")
        self.assertEqual(response.context.get("header"),
                         "Редактировать запись")
        self.assertTrue(response.context.get("edit"))

    def test_profile_view_pass_correct_contxt(self):
        """Шаблон profile.html сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse("profile", kwargs={"username": self.user.username})
        )
        self.assertIsNotNone(response.context.get("page"))
        first_post = response.context.get("page").object_list[0]
        self.assertIsInstance(first_post, Post)
        self.assertEqual(first_post, self.post)
        self.assertEqual(response.context.get("profile"), self.user)
        self.assertEqual(response.context.get("post_count"), 1)

    def test_post_view_pass_correct_context(self):
        """Шаблон post.html сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse("post", kwargs={"username": self.user.username,
                                    "post_id": self.post.id})
        )
        self.assertEqual(response.context.get("post"), self.post)
        self.assertEqual(response.context.get("post_count"), 1)
        self.assertEqual(response.context.get("profile"), self.user)

    def test_nonexistent_page_return_404(self):
        response = self.authorized_client.get("/abacaba_page_not_exists/")
        #  Юзер с именем abacaba_page_not_exists сломает тест :)
        self.assertEqual(response.status_code, 404)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PaginatorViewsTest.user = User.objects.create(
            username="serge"
        )
        PaginatorViewsTest.posts = [Post.objects.create(
            text=str(i),
            author_id=PaginatorViewsTest.user.id
        ) for i in range(13)]

    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_first_page_conteins_ten_records(self):
        """ На первой странице максимум — 10 постов """
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_second_page_conteins_three_records(self):
        """ На второй странице остаток — 3 поста """
        response = self.client.get(reverse("index") + "?page=2")
        self.assertEqual(len(response.context.get("page").object_list), 3)


class GroupPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        GroupPagesTest.groups = [Group.objects.create(
            slug=f"test-slug-{i}"
        ) for i in range(2)]
        GroupPagesTest.user = User.objects.create(username="serges")
        GroupPagesTest.posts = Post.objects.create(
            text="test post text",
            author_id=GroupPagesTest.user.id,
            group_id=GroupPagesTest.groups[0].id
        )

    def setUp(self):
        self.cllient = Client()
        cache.clear()

    def test_index_page_list_is_1(self):
        """ На главной пост отображается """
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context.get("page").object_list), 1)

    def test_group_1_page_list_is_1(self):
        """ Пост отображается на странице группы,
        в которую он добавлен """
        response = self.client.get(
            reverse("group", kwargs={"slug": "test-slug-0"})
        )
        self.assertEqual(len(response.context.get("page").object_list), 1)

    def test_group_2_page_list_is_0(self):
        """ Пост не отображается на странице группы,
        в которую он не был добавлен """
        response = self.client.get(
            reverse("group", kwargs={"slug": "test-slug-1"})
        )
        self.assertEqual(len(response.context.get("page").object_list), 0)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageViewTest(TestCase):
    """Проверяет, что пост с картинкой порождает объект
    image в контексте различных страниц"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        ImageViewTest.user = User.objects.create(username="sergi")
        ImageViewTest.group = Group.objects.create(
            slug="test-slug"
        )
        ImageViewTest.post = Post.objects.create(
            text="Hello image",
            author_id=ImageViewTest.user.id,
            group_id=ImageViewTest.group.id,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_index_post_has_image_in_context(self):
        """В контексте главной страницы у поста есть поле image"""
        response = self.guest_client.get(reverse("index"))
        first_post = response.context.get("page").object_list[0]
        self.assertEqual(first_post.image, "posts/small.gif")

    def test_profilr_post_has_image_in_context(self):
        """В контексте профиля у поста есть поле image"""
        response = self.guest_client.get(
            reverse("profile", kwargs={"username": self.user.username})
        )
        first_post = response.context.get("page").object_list[0]
        self.assertEqual(first_post.image, "posts/small.gif")

    def test_group_post_has_image_in_context(self):
        """В контексте группы у поста есть поле image"""
        response = self.guest_client.get(
            reverse("group", kwargs={"slug": "test-slug"})
        )
        first_post = response.context.get("page").object_list[0]
        self.assertEqual(first_post.image, "posts/small.gif")

    def test_post_has_image_in_context(self):
        """В контексте отдельного поста есть поле image"""
        response = self.guest_client.get(
            reverse("post", kwargs={"username": self.user.username,
                                    "post_id": self.post.id})
        )
        post = response.context.get("post")
        self.assertEqual(post.image, "posts/small.gif")


class CacheViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        CacheViewTest.user = User.objects.create(username="sergios")
        CacheViewTest.group = Group.objects.create(slug="test-slug")

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_index_cache(self):
        response = self.guest_client.get(reverse("index"))
        self.assertFalse(response.context.get("page").object_list)
        Post.objects.create(
            text="hi text",
            author_id=self.user.id
        )
        response = self.guest_client.get(reverse("index"))
        self.assertIsNone(response.context)
        time.sleep(20)
        response = self.guest_client.get(reverse("index"))
        self.assertTrue(response.context.get("page").object_list)
