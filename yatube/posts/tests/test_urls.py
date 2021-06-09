from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PostsURLTests.group = Group.objects.create(
            title="test group",
            slug="slug",
        )
        PostsURLTests.author = User.objects.create(username="serge")
        PostsURLTests.user = User.objects.create(username="max")
        PostsURLTests.post = Post.objects.create(
            text="Just text",
            author_id=PostsURLTests.author.id
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_exists_and_available_for_guest(self):
        """Общедоступные страницы на месте"""
        self.slug = self.group.slug
        urls = (
            "/",
            f"/{self.author.username}/",
            f"/group/{self.group.slug}/",
            f"/{self.author.username}/{self.post.id}/",
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_new_url_exists_at_desired_location_authorized(self):
        """Страница /new/ доступна залогиненому пользователю"""
        response = self.authorized_client.get("/new/")
        self.assertEqual(response.status_code, 200)

    def test_edit_url_availible_for_author_and_use_correct_template(self):
        """Страница /serge/1/edit/ доступна автору для редактирования
        и использует корректный шаблон"""
        self.authorized_client.force_login(self.author)
        response = self.authorized_client.get(
            f"/{self.author.username}/{self.post.id}/edit/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "post_form.html")

    def test_edit_url_redirect_user_to_post_url(self):
        """Пользователь, не являющийся автором, редиректится
        с /serge/1/edit/ на /serge/1/"""
        response = self.authorized_client.get(
            f"/{self.author.username}/{self.post.id}/edit/"
        )
        self.assertRedirects(response,
                             f"/{self.author.username}/{self.post.id}/")

    def test_guest_redirect_to_login_page(self):
        """Страницы /new/ и /serge/1/edit/ просят гостя авторизоваться"""
        urls = (
            "/new/",
            f"/{self.author.username}/{self.post.id}/edit/",
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f"/auth/login/?next={url}")

    def test_urls_uses_correct_templates(self):
        """URL-адреса используют соответствующие шаблоны"""
        templates_url_names = {
            "index.html": "/",
            "group.html": f"/group/{self.group.slug}/",
            "post_form.html": "/new/",
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
