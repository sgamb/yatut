from django.test import TestCase

from posts.models import Group, Post, User


class PostsModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="test_group",
            slug="tg"
        )
        cls.author = User.objects.create(
            first_name="tester",
            id="1",
            password="testpasswd"
        )
        cls.post = Post.objects.create(
            text="h" * 20,
            author=PostsModelsTest.author,
        )

    def test_group_object_name_is_title_field(self):
        """group.__str__() must return group.title field"""
        group = PostsModelsTest.group
        expected_group_object_name = group.title
        self.assertEqual(expected_group_object_name, str(group))

    def test_post_object_name_is_truncated_text_fiels(self):
        """post.__str__() must return first 15 characters of text"""
        post = PostsModelsTest.post
        expected_post_object_name = post.text[:15]
        self.assertEqual(expected_post_object_name, str(post))
