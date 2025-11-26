from rest_framework import serializers
from .models import *


class DirectorSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='crewid.firstname')
    lastname  = serializers.CharField(source='crewid.lastname')

    class Meta:
        model  = Directors
        fields = ['crewid', 'firstname', 'lastname']

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movies
        fields = ('movieid', 'title', 'releaseyear', 'duration', 'platformname', 'poster_url')


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reviews
        fields = ['userid', 'movieid', 'content', 'rating', 'reviewdate']

class ActorSerializer(serializers.ModelSerializer):
   
    firstname = serializers.CharField(source='crewid.firstname')
    lastname  = serializers.CharField(source='crewid.lastname')

    class Meta:
        model  = Actors
        fields = ['crewid', 'firstname', 'lastname']

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genres
        fields = ('genrename',)

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        # don’t accidentally return passwords in the API
        fields = ('userid', 'firstname', 'lastname', 'email')

class AdminsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admins
        # don’t accidentally return passwords in the API
        fields = ('adminid', 'firstname', 'lastname', 'email')

class StreamingPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamingPlatforms
        fields = ('platformname', 'url')


class AdminMovieManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminMovieManagement
        fields = ('adminid', 'movieid')


class ReviewModerationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ReviewModeration
        fields = ('userid', 'movieid', 'adminid')