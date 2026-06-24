from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from rockapi.views import (
    register_user, login_user,
    TypeView, RockView, RockImageView
)
from rockapi.views.health_check import health_check

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'types', TypeView, 'type')
router.register(r'rocks', RockView, 'rock')
router.register(r'rock-images', RockImageView, 'rock-image')  

urlpatterns = [
    path('', include(router.urls)),
    path('register', register_user),
    path('login', login_user),
    path('health', health_check),
    path('admin/', admin.site.urls),
]
