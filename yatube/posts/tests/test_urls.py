from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUp(self):
        super().setUpClass()
        Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание'
        )
        self.guest_client = Client()
        self.author = User.objects.create(username='author')
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        Post.objects.create(
            text='Тестовое содержимое поста',
            author=self.author,
        )
        self.post_id = Post.objects.last().id
        self.user = User.objects.create(username='TestUser')
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        cache.clear()

    def test_correct_templates(self):
        """Проверка соответсвия URL и шаблонов."""
        url_template_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            f'/posts/{self.post_id}/': 'posts/post_detail.html',
            f'/posts/{self.post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for address, template in url_template_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_guest_available(self):
        """Проверка доступа от имени незалогиненного юзера (страницы д-ны)."""
        guest_urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'author'}),
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        ]
        for url in guest_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_pages_authorized_author_available(self):
        """Проверка доступа от имени залогиненного автора."""
        authorized_urls = [
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}),
            reverse('posts:post_create')
        ]
        for url in authorized_urls:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_pages_authorized_user_not_abailable(self):
        """Проверка доступа от имени залогиненного автора (страницы нед-ны."""
        response = self.authorized_user.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )

    def test_pages_guest_not_available(self):
        """Проверка доступа незалогиненного юзера (страницы нед-ны)."""
        authorized_urls = {
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}):
                reverse('users:login')
                + '?next='
                + reverse('posts:post_edit', kwargs={'post_id': self.post_id}),
            reverse('posts:post_create'):
                reverse('users:login')
                + '?next='
                + reverse('posts:post_create')
        }
        for url, redirect_url in authorized_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_unknown_url(self):
        """Проверка открытия несуществующей страницы."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
