from django.conf.urls import url
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from .views import CommentViewSet, FollowViewSet, GroupViewSet, PostViewSet

router = routers.DefaultRouter()

router.register(
    r'posts',
    PostViewSet,
)
router.register(
    r'groups',
    GroupViewSet,
)
router.register(
    r'posts/(?P<post_id>\d+)/comments',
    CommentViewSet,
    basename='comments',
)
router.register(
    r'follow',
    FollowViewSet,
    basename='followers',
)

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/', include('djoser.urls.jwt')),
]


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title="Yatut API",
        default_version='v1',
        description="Документация для приложения api проекта yatut",
        contact=openapi.Contact(email="sgamb2000@gmail.com"),
        license=openapi.License(name="BSD License"),
        generator_class=BothHttpAndHttpsSchemaGenerator,
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    url(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'),
]
