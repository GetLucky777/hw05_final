from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.cache import cache

from posts.models import Group, Post, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа с текстом больше 15 символов',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Текст комментария'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
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

    def test_models_verbose_name(self):
        """Проверяем, что verbose_name полей совпадает с ожидаемым."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        follow = PostModelTest.follow
        fields_verbose_names = {
            ('Текст поста', post): 'text',
            ('Автор', post): 'author',
            ('Группа', post): 'group',
            ('Картинка', post): 'image',
            ('Название группы', group): 'title',
            ('Слаг', group): 'slug',
            ('Описание', group): 'description',
            ('Пост', comment): 'post',
            ('Автор', comment): 'author',
            ('Комментарий', comment): 'text',
            ('Дата', comment): 'created',
            ('Подписчик', follow): 'user',
            ('Автор', follow): 'author'
        }
        for verbose_name, field in fields_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    verbose_name[1]._meta.get_field(field).verbose_name,
                    verbose_name[0]
                )

    def test_models_help_text(self):
        """Проверяем, что help_text полей совпадает с ожидаемым."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        follow = PostModelTest.follow
        fields_help_texts = {
            ('Текст нового поста', post): 'text',
            ('Автор поста', post): 'author',
            ('Группа, к которой будет относиться пост', post): 'group',
            ('Картинка поста', post): 'image',
            ('Название группы', group): 'title',
            ('Название слага', group): 'slug',
            ('Описание группы', group): 'description',
            ('Пост с комментарием', comment): 'post',
            ('Автор комментария', comment): 'author',
            ('Текст комментария', comment): 'text',
            ('Дата добавления комментария', comment): 'created',
            ('Подписчик автора', follow): 'user',
            ('Автор, на которого подписываются', follow): 'author'
        }
        for help_text, field in fields_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    help_text[1]._meta.get_field(field).help_text,
                    help_text[0]
                )
