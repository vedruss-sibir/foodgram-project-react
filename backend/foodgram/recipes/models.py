from django.core import validators
from django.db import models
from users.models import User


class Ingredient(models.Model):
    name = models.CharField("Ингредиент", max_length=200)
    measurement_unit = models.CharField("Единица измерения", max_length=200)

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}."


class Tag(models.Model):
    name = models.CharField("Название", max_length=60)
    color = models.CharField("Цвет", max_length=7)
    slug = models.SlugField("Ссылка", max_length=100, unique=True)

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
        ordering = ("-id",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipe", verbose_name="Автор"
    )
    name = models.CharField("Рецепт", max_length=200)
    image = models.ImageField("Картинка", upload_to="static/recipe/")
    text = models.TextField("Описание рецепта")
    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")
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
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe")
    ingredient = models.ForeignKey(
        "Ingredient", on_delete=models.CASCADE, related_name="ingredient"
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message="Минимальное количество ингридиентов 1"
            ),
        ),
        verbose_name="Количество",
    )


class FavoriteRecipe(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="favorite_recipe",
        verbose_name="Пользователь",
    )
    recipe = models.ManyToManyField(
        Recipe, related_name="favorite_recipe", verbose_name="Избранный рецепт"
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"

    def __str__(self):
        list_ = [item["name"] for item in self.recipe.values("name")]
        return f"Пользователь {self.user} добавил рецепт {list_} в избранные."


class ShoppingCart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ManyToManyField(
        Recipe, related_name="shopping_cart", verbose_name="Покупка"
    )

    class Meta:
        verbose_name = "Покупка"
        verbose_name_plural = "Покупки"
        ordering = ("-id",)

    def __str__(self):
        list_ = [item["name"] for item in self.recipe.values("name")]
        return f"Пользователь {self.user} добавил список {list_} в покупки."
