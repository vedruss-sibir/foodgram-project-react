from import_export import resources
from recipes.models import (
    Ingredient,
    Recipe,
    Tag,
    FavoriteRecipe,
    ShoppingCart,
    User,
    Follow,
    RecipeIngredient,
)
from django.contrib import admin
from import_export.admin import ImportMixin


class IngredientsInline(admin.TabularInline):
    model = Ingredient
    extra = 1


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
    list_display = ("pk", "name", "author", "pub_date")
    #    inlines = IngredientsInline
    list_filter = ("author", "name", "tags")


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart)
admin.site.register(FavoriteRecipe)
admin.site.register(Follow)
admin.site.register(User)
