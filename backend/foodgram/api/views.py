from http import HTTPStatus
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, get_list_or_404
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from api.filters import AuthorAndTagFilter, IngredientSearchFilter
from recipes.models import (
    ShoppingCart,
    FavoriteRecipe,
    Ingredient,
    RecipeIngredient,
    Recipe,
    Tag,
    User,
    Follow,
)
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    FavoriteValidateSerializer,
    RecipesReadSerializer,
    CustomUserSerializer,
    FollowSerializer,
)


class SubscribesViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = FollowSerializer

    def create(self, request, *args, **kwargs):
        id = self.kwargs.get("id")
        user = get_object_or_404(User, id=id)
        if request.user == user:
            msg = "Нельзя подписываться на себя"
            return Response(msg, status=HTTPStatus.BAD_REQUEST)
        if Follow.objects.filter(user=request.user, author=user).exists():
            msg = "Подписка уже существует"
            return Response(msg, status=HTTPStatus.BAD_REQUEST)
        Follow.objects.create(user=request.user, author=user)
        msg = "Подписка создана успешно"
        return Response(msg, HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        author_id = self.kwargs["id"]
        id = request.user.id
        if not Follow.objects.filter(user_id=id, author_id=author_id).exists():
            msg = "Такой подписки не существует"
            return Response(msg, HTTPStatus.NOT_FOUND)
        Follow.objects.filter(user_id=id, author_id=author_id).delete()
        msg = "Успешная отписка"
        return Response(msg)


class TagsViewSet(ReadOnlyModelViewSet):
    permission_classes = (IsAdminOrReadOnly,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    search_fields = ("name",)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitPageNumberPagination
    filter_class = AuthorAndTagFilter
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=["POST", "DELETE"], permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        current_user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = FavoriteValidateSerializer(
            data=request.data,
            context={"request": request, "recipe": recipe},
        )
        serializer.is_valid(raise_exception=True)
        if request.method == "POST":
            FavoriteRecipe.objects.create(user=current_user, recipe=recipe)
            serializer = RecipesReadSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipe_in_favorite = FavoriteRecipe.objects.filter(
            user=current_user, recipe=recipe
        )
        recipe_in_favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
