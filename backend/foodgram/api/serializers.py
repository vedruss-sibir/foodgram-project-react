from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import (
    Ingredient,
    RecipeIngredient,
    Recipe,
    Tag,
    User,
    Follow,
    FavoriteRecipe,
    ShoppingCart,
)
from api.utils import create_update_ingredients


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = ("email", "id", "password", "username", "first_name", "last_name")
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
            "password": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[: int(limit)]
        return ShoppingCartValidateSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def validate(self, data):
        request = self.context.get("request")
        author_id = data["author"].id
        follow_exists = Follow.objects.filter(
            user=request.user, author__id=author_id
        ).exists()

        if request.method == "GET":
            if request.user.id == author_id:
                raise serializers.ValidationError("Нельзя подписаться на себя")
            if follow_exists:
                raise serializers.ValidationError(
                    "Вы уже подписаны на этого пользователя"
                )
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class AmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount", "name", "measurement_unit")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientCreateSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField(write_only=True)
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Ingredient
        fields = ["id", "amount"]


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer()
    image = Base64ImageField()
    ingredients = AmountSerializer(many=True, source="ingredient_recipe")
    is_favorited = serializers.SerializerMethodField(method_name="get_is_favorited")
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name="get_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorite_recipe__user=user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(shopping_cart__user=user, id=obj.id).exists()


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateSerializer(many=True)
    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        tags_data = self.initial_data.get("tags")
        recipe.tags.set(tags_data)
        create_update_ingredients(recipe, ingredients)
        recipe.save()
        recipe.is_favorited = False
        recipe.is_in_shopping_cart = False
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        super().update(instance, validated_data)
        instance.tags.clear()
        tags_data = self.initial_data.get("tags")
        instance.tags.set(tags_data)
        RecipeIngredient.objects.filter(recipe=instance).all().delete()
        recipe = instance
        create_update_ingredients(recipe, ingredients)
        instance.save()
        return instance

    def validate(self, data):
        cooking_time = self.initial_data.get("cooking_time")
        if int(cooking_time) <= 0:
            raise serializers.ValidationError(
                {"errors": "Время приготовление должно быть больше нуля!"}
            )
        ingredients = self.initial_data.get("ingredients")
        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Нужен хоть один ингридиент для рецепта"}
            )
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=ingredient_item["id"])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    "Ингридиенты должны " "быть уникальными"
                )
            ingredient_list.append(ingredient)
            if int(ingredient_item["amount"]) < 0:
                raise serializers.ValidationError(
                    {
                        "ingredients": (
                            "Убедитесь, что значение количества " "ингредиента больше 0"
                        )
                    }
                )
        data["ingredients"] = ingredients
        return data


class FavoriteValidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        recipe = self.context.get("recipe")
        recipe_in_favorite = FavoriteRecipe.objects.filter(user=user, recipe=recipe)
        if request.method == "POST":
            if recipe_in_favorite.exists():
                raise serializers.ValidationError(
                    {"errors": "Этот рецепт уже есть в избранном!"}
                )
        if request.method == "DELETE" and not recipe_in_favorite.exists():
            raise serializers.ValidationError(
                {"errors": "Этого рецепта нет в избранном пользователя!"}
            )
        return data


class ShoppingCartValidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
