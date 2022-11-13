from django_filters import rest_framework as filters
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet


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
from api.permissions import  IsOwnerOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    FavoriteValidateSerializer,
    RecipeListSerializer,
    ShoppingCartValidateSerializer,
    FollowSerializer,
    CustomUserSerializer
)
from api.utils import get_shopping_list


class UserViewset(UserViewSet):
    pagination_class = LimitPageNumberPagination

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=("post", "delete",),
    )
    def subscribe(self, request, id=None):
        """Подписка/Отписка."""
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            if request.user == author:
                return Response({
                    "errors": "Нельзя подписываться на себя."},
                    status=status.HTTP_400_BAD_REQUEST)
            if Follow.objects.filter(user=request.user,
                                        author=author).exists():
                return Response({
                    "errors": "Вы уже подписаны на данного пользователя"},
                    status=status.HTTP_400_BAD_REQUEST)

            follow = Follow.objects.create(user=request.user, author=author)
            serializer = FollowSerializer(
                follow, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if request.user == author:
                return Response({
                    "errors": "Нельзя подписываться на себя."},
                    status=status.HTTP_400_BAD_REQUEST)
            follow = Follow.objects.filter(user=request.user, author=author)
            if follow.exists():
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response({
                "errors": "Вы уже отписались"
            }, status=status.HTTP_400_BAD_REQUEST)

        return None

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Список подписок пользователя."""
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

   
class TagsViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientSearchFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AuthorAndTagFilter
    permission_classes = [IsOwnerOrReadOnly]     

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeListSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        author = self.request.user
        return serializer.save(author=author)
    
    @action(
        detail=True,
        methods=("delete", "post"),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(FavoriteRecipe, request.user, pk)
        elif request.method == 'DELETE':
            return self.delete_obj(FavoriteRecipe, request.user, pk)
        return None
                  
    @action(
        detail=True,
        methods=("delete", "post"),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        if request.method == "POST":
            return self.add_obj(ShoppingCart, request.user, pk)
        elif request.method == "DELETE":
            return self.delete_obj(ShoppingCart, request.user, pk)
        return None

    def add_obj(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {"errors": "Рецепт уже добавлен в список"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = ShoppingCartValidateSerializer(recipe)        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"errors": "Рецепт уже удален"}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        return get_shopping_list(request)
