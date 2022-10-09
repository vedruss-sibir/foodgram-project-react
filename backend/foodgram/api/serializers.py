from djoser.serializers import UserCreateSerializer, UserSerializer
from django.core.files.base import ContentFile
import base64
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import Ingredient, RecipeIngredient, Recipe, Tag, User, Follow


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

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "is_subscribed")

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class FollowSerializer(serializers.ModelSerializer):
    queryset = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(queryset=queryset)
    author = serializers.PrimaryKeyRelatedField(queryset=queryset)

    class Meta:
        model = Follow
        fields = ("user", "author")

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


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Если полученный объект строка, и эта строка
        # начинается с 'data:image'...
        if isinstance(data, str) and data.startswith("data:image"):
            # ...начинаем декодировать изображение из base64.
            # Сначала нужно разделить строку на части.
            format, imgstr = data.split(";base64,")
            # И извлечь расширение файла.
            ext = format.split("/")[-1]
            # Затем декодировать сами данные и поместить результат в файл,
            # которому дать название по шаблону.
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class IngredientSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()    

    class Meta:
        model = Ingredient
        fields = ["id", "name", "amount", "measurement_unit"]

    def get_amount(self, obj):
        return obj.recipe_ingredient.values_list('amount', flat=True)[0]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True)
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
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorites__user=user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(cart__user=user, id=obj.id).exists()

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        tags_data = self.initial_data.get("tags")
        recipe.tags.set(tags_data)
        for ingredient in ingredients_data:
            current_ingredient, status=Ingredient.objects.get_or_create(**ingredient)
            RecipeIngredient.objects.create (recipe=recipe, ingredient=current_ingredient, amount=ingredient.get("amount"))
        recipe.is_favorited = False
        recipe.is_in_shopping_cart = False
        recipe.save()
        return recipe
