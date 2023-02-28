from rest_framework import routers
from backend.views_viewset import BasketViewSet


router = routers.SimpleRouter(trailing_slash=True)

router.register(r'basket', BasketViewSet, basename='viewset')

app_name = 'viewset'
urlpatterns = router.urls
