from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientsViewSet, RecipeViewSet, TagsViewSet, SubscribesViewSet

app_name = "api"

router = DefaultRouter()
router.register("tags", TagsViewSet)
router.register("ingredients", IngredientsViewSet)
router.register("recipes", RecipeViewSet)

urlpatterns = [
    path("users/subscriptions/", SubscribesViewSet.as_view({"get": "list"})),
    path(
        "users/<id>/subscribe/",
        SubscribesViewSet.as_view({"post": "create", "delete": "delete"}),
    ),
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
