import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTests(TestCase):
    @classmethod
    def setUp(self):
        super().setUpClass()
        self.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
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
            group=self.group
        )
        self.post_id = Post.objects.latest('id').id
        self.form = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': self.uploaded_image
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Проверка создания поста и формы для этого."""
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group,
            ).exists()
        )
        self.assertEqual(
            Post.objects.latest('id').image,
            f'posts/{self.form["image"]}'
        )

    def test_edit_post(self):
        """Проверка редактирования поста и формы для этого."""
        original_post_text = Post.objects.get(pk=self.post_id).text
        self.assertEqual(original_post_text, 'Тестовое содержимое поста')
        self.form['text'] = 'Новое тестовое содержание'
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}),
            data=self.form,
        )
        edited_post_text = Post.objects.get(pk=self.post_id).text
        self.assertEqual(edited_post_text, 'Новое тестовое содержание')

    def test_guest_cant_create_post(self):
        """Проверка того, что неавт-ый юзер не может создать пост."""
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form,
            follow=True
        )
        self.assertRedirects(
            response,
            (reverse('users:login') + '?next=/create/')
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group.pk
            ).exists()
        )

    def test_guest_cant_comment_posts(self):
        """Проверка, что только авторизованный юзер может оставлять комм-ий."""
        comment_form = {
            'text': 'Текст комментария'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post_id}),
            data=comment_form
        )
        self.assertEqual(
            Post.objects.get(pk=self.post_id).comments.count(), 1
        )
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post_id}),
            data=comment_form
        )
        self.assertEqual(
            Post.objects.get(pk=self.post_id).comments.count(), 1
        )
