from django_filters import rest_framework as filters 

from recipes.models import Recipe, Ingredient, User


class IngredientSearchFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class AuthorAndTagFilter(filters.FilterSet):   
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")   
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        print('начало избр')
        if value and not self.request.user.is_anonymous:
            print('if избр')
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        print('начало карта')
        if value and not self.request.user.is_anonymous:
            print('if карта')
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ("tags", "author")