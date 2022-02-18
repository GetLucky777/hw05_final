import shutil
import tempfile

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms

from posts.models import Group, Post, User, Comment
from posts.forms import PostForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsAndContextTests(TestCase):
    @classmethod
    def setUp(self):
        super().setUpClass()
        self.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание'
        )
        self.wrong_group = Group.objects.create(
            title='Неправильная группа',
            slug='wrong-group',
            description='Тестовое описание'
        )
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.guest_client = Client()
        self.user = User.objects.create(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовое содержимое поста',
            author=self.user,
            group=self.group,
            image=self.uploaded_image
        )
        self.post_id = Post.objects.last().id

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_views_use_correct_template(self):
        """Проверка соответствия view и шаблона, который она открывает."""
        view_template_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'TestUser'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={
                        'post_id': self.post_id
                    }): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': self.post_id
                    }): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for view, template in view_template_names.items():
            with self.subTest(view=view):
                response = self.authorized_client.get(view)
                self.assertTemplateUsed(response, template)

    def test_main_page_have_correct_context(self):
        """Проверка словаря контекста главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_group_list_have_correct_context(self):
        """Проверка словаря контекста страницы группы."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(first_object, self.post)

    def test_profile_have_correct_context(self):
        """Проверка словаря контекста профиля юзера."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'TestUser'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)
        self.assertEqual(response.context.get('title'),
                         f'Профайл пользователя '
                         f'{self.user.first_name} {self.user.last_name}')
        self.assertEqual(response.context.get('author'),
                         self.user)
        self.assertEqual(response.context.get('user_posts')[0],
                         self.user.posts.all()[0])
        self.assertEqual(response.context.get('post_amount'),
                         self.user.posts.all().count())

    def test_post_detail_have_correct_context(self):
        """Проверка словаря контекста страницы поста."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id}))
        self.assertEqual(response.context.get('title'),
                         'Тестовое содержимое поста')
        self.assertEqual(response.context.get('post'),
                         self.post)
        self.assertEqual(response.context.get('post_amount'),
                         self.user.posts.all().count())

    def test_edit_post_have_correct_context(self):
        """Проверка словаря контекста страницы редактирования поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context.get('form')
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertIsInstance(form, PostForm)
        self.assertIsInstance(response.context.get('is_edit'), bool)
        self.assertEqual(response.context.get('is_edit'), True)
        self.assertEqual(response.context.get('post'),
                         self.user.posts.get(pk=self.post_id))

    def test_create_post_have_correct_context(self):
        """Проверка словаря контекста страницы создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context.get('form')
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertIsInstance(form, PostForm)

    def test_post_have_right_group(self):
        """Проверка корректности группы у нового поста."""
        wrong_group_posts = self.wrong_group.posts.all()
        rigth_group_post = self.group.posts.all()
        self.assertFalse(wrong_group_posts)
        self.assertTrue(rigth_group_post)

    def test_user_can_add_comment(self):
        """Проверка, что комментарий появляется на странице поста."""
        commented_post = Post.objects.get(pk=self.post_id)
        comment_form = {
            'text': 'Текст комментария'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post_id}),
            data=comment_form,
            follow=True
        )
        self.assertEqual(commented_post.comments.count(), 1)
        response = self.authorized_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post_id}),
            follow=True
        )
        self.assertEqual(
            response.context.get('comments').latest('id'),
            Comment.objects.all().latest('id')
        )

    def test_index_cache(self):
        """Проверка работы кеша"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        new_cache = response.content
        post = Post.objects.get(pk=1)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, new_cache)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, new_cache)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUp(self):
        super().setUpClass()
        self.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание'
        )
        self.guest_client = Client()
        self.user = User.objects.create(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.posts = [
            Post(
                pk=i,
                text='Тестовое содержимое поста',
                author=self.user,
                group=self.group
            )
            for i in range(1, 14)
        ]
        Post.objects.bulk_create(self.posts)

    def test_profile_and_group_paginator(self):
        """Проверка паджинатора страниц профиля и группы."""
        pages_with_paginator = {
            'posts:index': {},
            'posts:group_list': {'slug': 'test-slug'},
            'posts:profile': {'username': 'TestUser'}
        }

        for reverse_name, kwargs in pages_with_paginator.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse(reverse_name, kwargs=kwargs)
                )
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.authorized_client.get(
                    reverse(reverse_name, kwargs=kwargs), {'page': 2}
                )
                self.assertEqual(len(response.context['page_obj']), 3)