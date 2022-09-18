from import_export import resources
from recipes.models import Ingredient, Recipe, Tag, FavoriteRecipe, ShoppingCart
from django.contrib import admin
from import_export.admin import ImportMixin


class IngredientResource(resources.ModelResource):
    class Meta:
        model = Ingredient
        fields = (
            "id",
            "name",
            "measurement_unit",
        )


class IngredientAdmin(ImportMixin, admin.ModelAdmin):
    resource_class = IngredientResource
    list_filter = ("name",)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author")  # "count_favorites")
    list_filter = ("author", "name", "tags")


# def count_favorites(self, obj):
#      return obj.favorites.count()


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart)
admin.site.register(FavoriteRecipe)
