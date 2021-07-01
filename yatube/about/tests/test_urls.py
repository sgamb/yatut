from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls_exists_at_desired_location(self):
        urls = ("/about/author/", "/about/tech/")
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)
