from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        names = ("about:author", "about:tech")
        for name in names:
            with self.subTest(name=name):
                response = self.guest_client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_about_pages_uses_correct_templates(self):
        templates_page_names = {
            "about/author.html": reverse("about:author"),
            "about/tech.html": reverse("about:tech"),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
