from django.http import HttpResponse

from recipes.models import ShoppingCart, RecipeIngredient, Ingredient


def get_shopping_list(request):
    shopping_cart = ShoppingCart.objects.filter(user=request.user).all()
    shopping_list = {}
    for item in shopping_cart:
        for ingredient1_recipe in item.recipe.ingredient_recipe.all():
            name = ingredient1_recipe.ingredients.name
            measuring_unit = ingredient1_recipe.ingredients.measurement_unit
            amount = ingredient1_recipe.amount
            if name not in shopping_list:
                shopping_list[name] = {
                    "name": name,
                    "measurement_unit": measuring_unit,
                    "amount": amount,
                }
            else:
                shopping_list[name]["amount"] += amount
    content = [
        f'{item["name"]} ({item["measurement_unit"]}) ' f'- {item["amount"]}\n'
        for item in shopping_list.values()
    ]
    filename = "shopping_list.txt"
    response = HttpResponse(content, content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename={0}".format(filename)
    return response


def create_ubdate_ingredients(recipe, ingredients):
    for ingredient in ingredients:
        current_ingredient, status = Ingredient.objects.get_or_create(**ingredient)
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=current_ingredient,
            amount=ingredient.get("amount"),
        )
