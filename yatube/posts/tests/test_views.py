from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..models import Post, Group, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="Abramow_test")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )
        cls.templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_posts", kwargs={"slug": cls.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": cls.post.author}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": cls.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": cls.post.id}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_index_show_correct_context(self):
        """Список постов в шаблоне index равен ожидаемому контексту."""
        response = self.guest_client.get(reverse("posts:index"))
        expected = list(Post.objects.all()[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_group_list_show_correct_context(self):
        """Список постов в шаблоне group_list равен ожидаемому контексту."""
        response = self.guest_client.get(
            reverse("posts:group_posts", kwargs={"slug": self.group.slug})
        )
        expected = list(Post.objects.filter(group_id=self.group.id)[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_profile_show_correct_context(self):
        """Список постов в шаблоне profile равен ожидаемому контексту."""
        response = self.guest_client.get(
            reverse("posts:profile", args=(self.post.author,))
        )
        expected = list(Post.objects.filter(author_id=self.user.id)[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        first_object = response.context['post']
        post_aurhor_0 = first_object.author.username
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        self.assertEqual(post_aurhor_0, 'Abramow_test')
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_group_0, 'Тестовая группа')

    def test_create_edit_show_correct_context(self):
        """Шаблон create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверяем создание поста на страницах с выбранной группой"""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_posts", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный Пост с группой не попап в чужую группу."""
        form_fields = {
            reverse(
                "posts:group_posts", kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Abramow_test')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse(
            'posts:group_posts', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.author.username}'}
        )
        cls.ADDPOSTS = 5

        cls.posts = Post.objects.bulk_create(
            Post(
                author=cls.author,
                text=f'{i + 1} длинный тестовый пост',
                group=cls.group
            )
            for i in range(settings.POSTS_PER_PAGE + cls.ADDPOSTS)
        )

    def test_accordance_posts_per_pages(self):
        """Проверяем, что количество постов
        на первой странице равно 10, а на второй - 5"""

        for url in [
            PostPaginatorTests.INDEX_URL,
            PostPaginatorTests.GROUP_LIST_URL,
            PostPaginatorTests.PROFILE_URL
        ]:
            with self.subTest(url=url):
                response = PostPaginatorTests.author_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE
                )
                response_second = PostPaginatorTests.author_client.get(
                    f'{url}?page=2'
                )
                self.assertEqual(
                    len(response_second.context['page_obj']),
                    PostPaginatorTests.ADDPOSTS
                )
