"""
URL configuration for cinegator project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from cinegatorapp.views import *

router = DefaultRouter()
router.register(r'movies', MoviesViewSet, basename='movies')
router.register(r'reviews', ReviewsViewSet, basename='reviews')
router.register(r'actors', ActorsViewSet, basename='actors')
router.register(r'directors', DirectorsViewSet, basename='directors')
router.register(r'genres',    GenresViewSet,    basename='genres')
router.register(r'users', UsersViewSet, basename='users')
router.register(r'admins', AdminsViewSet, basename='admins')
router.register(r'streamingplatforms', StreamingPlatformsViewSet, basename='streamingplatforms')
router.register(r'admin-movie-management', AdminMovieManagementViewSet, basename='admin-movie-management')
router.register(r'review-moderation', ReviewModerationViewSet, basename='review-moderation')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
