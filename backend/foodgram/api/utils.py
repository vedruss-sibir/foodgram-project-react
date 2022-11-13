from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from recipes.models import ShoppingCart, RecipeIngredient, Ingredient


def get_shopping_list(request):
    shopping_cart = ShoppingCart.objects.filter(user=request.user).all()
    shopping_list = {}
    for item in shopping_cart:
        for ingredient1_recipe in item.recipe.ingredient_recipe.all():
            name = ingredient1_recipe.ingredient.name
            measuring_unit = ingredient1_recipe.ingredient.measurement_unit
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


def create_update_ingredients(recipe, ingredients):
      for ingredient in ingredients:
            id = ingredient.get('id')
            amount = ingredient.get('amount')
            ingredient_id = get_object_or_404(Ingredient, id=id)
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_id, amount=amount
            )
   
