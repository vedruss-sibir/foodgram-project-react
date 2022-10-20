from django.core import validators
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(
        verbose_name="Электронная почта", max_length=254, unique=True
    )
    first_name = models.CharField(verbose_name="Имя", max_length=150, blank=True)
    last_name = models.CharField(verbose_name="Фамилия", max_length=150, blank=True)
    username = models.CharField(verbose_name="Ник", max_length=150, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ("id",)
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"


class Ingredient(models.Model):
    name = models.CharField("Ингредиент", max_length=200)
    measurement_unit = models.CharField("Единица измерения", max_length=200)

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}."


class Tag(models.Model):
    name = models.CharField("Название", max_length=60, unique=True)
    color = models.CharField("Цвет в HEX формате", max_length=7, unique=True)
    slug = models.SlugField("Ссылка", max_length=100, unique=True)

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
        ordering = ("-id",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", verbose_name="Автор"
    )
    name = models.CharField("Рецепт", max_length=200)
    image = models.ImageField("Картинка", upload_to="static/recipe/")
    text = models.TextField("Описание рецепта")

    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
    )
    tags = models.ManyToManyField(Tag, verbose_name="Тэги", related_name="recipes")
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message="Минимальное время приготовления 1 минута"
            ),
        ),
        verbose_name="время приготовления",
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredient_recipe"
    )
    ingredients = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name="recipe_ingredient"
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message="Минимальное количество ингридиентов 1"
            ),
        ),
        verbose_name="Количество",
    )

    def __str__(self):
        return f"{self.ingredients.name} для {self.recipe.name}"


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="favorite_recipe",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="favorite_recipe",
        verbose_name="Избранный рецепт",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"

    def __str__(self):
        return f"Пользователь {self.user} добавил рецепт {self.recipe} в избранные."


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="shopping_cart",
        verbose_name="Покупка",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Покупка"
        verbose_name_plural = "Покупки"
        ordering = ("-id",)

    def __str__(self):
        return f"Пользователь {self.user.username} добавил список {self.recipe.name} в покупки."
