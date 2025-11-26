from django.contrib import admin
from .models import (
    Users,
    Admins,
    Genres,
    StreamingPlatforms,
    Movies,
    FilmCrew,
    Actors,
    Directors,
    BelongsTo,
    PartOf,
    Reviews,
    ReviewModeration,
    AdminMovieManagement,
)

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    pass

@admin.register(Admins)
class AdminsAdmin(admin.ModelAdmin):
    pass

@admin.register(Genres)
class GenresAdmin(admin.ModelAdmin):
    pass

@admin.register(StreamingPlatforms)
class StreamingPlatformsAdmin(admin.ModelAdmin):
    pass

@admin.register(Movies)
class MoviesAdmin(admin.ModelAdmin):
    pass

@admin.register(FilmCrew)
class FilmCrewAdmin(admin.ModelAdmin):
    pass

@admin.register(Actors)
class ActorsAdmin(admin.ModelAdmin):
    pass

@admin.register(Directors)
class DirectorsAdmin(admin.ModelAdmin):
    pass

@admin.register(BelongsTo)
class BelongsToAdmin(admin.ModelAdmin):
    pass

@admin.register(PartOf)
class PartOfAdmin(admin.ModelAdmin):
    pass

@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    pass

@admin.register(ReviewModeration)
class ReviewModerationAdmin(admin.ModelAdmin):
    pass

@admin.register(AdminMovieManagement)
class AdminMovieManagementAdmin(admin.ModelAdmin):
    pass
