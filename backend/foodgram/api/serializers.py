from djoser.serializers import UserCreateSerializer, UserSerializer
from django.core.files.base import ContentFile
import base64
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
    is_subscribed = serializers.SerializerMethodField(read_only=True)

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

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()


class FollowSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipe_count = serializers.SerializerMethodField(read_only=True)
    username = serializers.CharField(required=False)

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipe_limit = request.GET.get("recipes_limit")
        queryset = Recipe.objects.filter(author_id=obj.id).order_by("pub_date")
        if recipe_limit is not None:
            queryset = Recipe.objects.filter(author_id=obj.id)[: int(recipe_limit)]
        return RecipeSerializer(queryset, many=True).data

    def get_recipe_count(self, obj):
        return Recipe.objects.filter(author__id=obj.id).count()

    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "recipes",
            "recipe_count",
        )
        model = User

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


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(read_only=True, source="ingredient.name")
    measurement_unit = serializers.CharField(
        read_only=True, source="ingredient.measurement_unit"
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class AmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredients.id")
    name = serializers.CharField(source="ingredients.name")
    measurement_unit = serializers.CharField(source="ingredients.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = "id", "amount", "name", "measurement_unit"


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsRecipeSerializer(many=True, source="ingredient_recipe")
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        curent_user = self.context["request"].user
        if curent_user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(user=curent_user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        curent_user = self.context.get("request").user
        if curent_user.is_anonymous:
            return False
        return Recipe.objects.filter(author=curent_user, id=obj.id).exists()

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        tags_data = self.initial_data.get("tags")
        recipe.tags.set(tags_data)
        for ingredient in ingredients_data:
            current_ingredient, status = Ingredient.objects.get_or_create(**ingredient)
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingredient.get("amount"),
            )
        recipe.is_favorited = False
        recipe.is_in_shopping_cart = False
        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.get("tags")
        ingredients = validated_data.get("ingredients")
        instance.image = validated_data.get("image", instance.image)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        if tags:
            instance.tags.clear()
            instance.tags.set(tags)

        if ingredients:
            instance.ingredients.clear()

        instance.save()
        return instance


class FavoriteValidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = (
            "user",
            "recipe",
        )
        read_only_fields = (
            "user",
            "recipe",
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
        model = ShoppingCart
        fields = (
            "user",
            "recipe",
        )
        read_only_fields = (
            "user",
            "recipe",
        )

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        recipe = self.context.get("recipe")
        recipe_in_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if request.method == "POST":
            if recipe_in_cart.exists():
                raise serializers.ValidationError(
                    {"errors": "Этот рецепт уже добавлен в корзину покупок!"}
                )
        if request.method == "DELETE" and not recipe_in_cart.exists():
            raise serializers.ValidationError(
                {"errors": "Этого рецепта нет в корзине покупок пользователя!"}
            )
        return data


class RecipesReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = "__all__"
