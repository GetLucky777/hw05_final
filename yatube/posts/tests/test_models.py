from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа с текстом больше 15 символов',
        )
        cache.clear()

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        models_str_magic = {
            group: 'Тестовая группа',
            post: 'Тестовая группа'
        }
        for object, expected_value in models_str_magic.items():
            with self.subTest(object=object):
                self.assertEqual(
                    str(object), expected_value
                )

    def test_text_label(self):
        """Проверяем, что verbose_name полей совпадает с ожидаемым."""
        post = PostModelTest.post
        fields_verbose_names = {
            'text': 'Текст поста',
            'group': 'Группа'
        }
        for field, verbose_name in fields_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    verbose_name
                )

    def test_group_help_text(self):
        """Проверяем, что help_text полей совпадает с ожидаемым."""
        post = PostModelTest.post
        fields_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, help_text in fields_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    help_text
                )
