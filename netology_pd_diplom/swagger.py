from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


api_info = openapi.Info(
      title="ShopsBackend API",
      default_version='v1',
      description="Документация дипломного проекта",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="berson969@gmail.com"),
   )

schema_view = get_schema_view(
    info=api_info,
    public=True,
    permission_classes=[permissions.AllowAny, ],
)
