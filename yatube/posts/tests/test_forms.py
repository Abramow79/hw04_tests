from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group, User


class PostFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="Abramow_test")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создала запись в Post."""
        posts_count = Post.objects.count()
        form_data = {"text": "Тестовый текст"}
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse("posts:profile", kwargs={
                "username": self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())

    def test_post_edit(self):
        """Валидная форма изменила запись в Post."""
        self.post = Post.objects.create(
            author=self.user,
            text="Текст для теста",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        posts_count = Post.objects.count()
        form_data = {"text": "Изменяем текст", "group": self.group.id}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={
                "post_id": self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=self.group.id,
            pk=self.post.pk,
        ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
