from django.shortcuts import render
from rest_framework import viewsets,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.db import transaction
from django.db.models import Max
from datetime import date
from .models import *
from .serializers import *
from .models import *
from .serializers import *


class ActorsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Actors.objects.select_related().all()
    queryset = (
        Actors.objects
              .select_related('crewid')
              .order_by('crewid__firstname', 'crewid__lastname')
    )
    serializer_class = ActorSerializer
    def retrieve(self, request, *args, **kwargs):
        actor = self.get_object()  
        actor_name = f"{actor.crewid.firstname} {actor.crewid.lastname}"
        print(f"[Django] Selected actor: {actor_name}")
        return super().retrieve(request, *args, **kwargs)

class GenresViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genres.objects.all().order_by('genrename')
    serializer_class = GenreSerializer

class DirectorsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Directors.objects
                 .select_related('crewid')
                 .order_by('crewid__firstname', 'crewid__lastname')
    )
    serializer_class = DirectorSerializer

    def retrieve(self, request, *args, **kwargs):
        director = self.get_object()
        name = f"{director.crewid.firstname} {director.crewid.lastname}"
        print(f"[Django] Selected director: {name}")
        return super().retrieve(request, *args, **kwargs)
    

class MoviesViewSet(viewsets.ModelViewSet):
    queryset = Movies.objects.all()
    serializer_class = MovieSerializer

    filter_backends = [filters.SearchFilter]
    search_fields   = ['title']

    def create(self, request, *args, **kwargs):
        data = request.data
        required = ('title','releaseyear','duration','platformname','genre','actor_id','director_id')
        if not all(field in data and data[field] for field in required):
            return Response(
                {'error': 'Missing one of required fields: ' + ', '.join(required)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # start an atomic transaction so that if one insert fails we roll back
        with transaction.atomic():
            try:
                platform = StreamingPlatforms.objects.get(
                    platformname__iexact = data['platformname']
                )
            except StreamingPlatforms.DoesNotExist:
                transaction.set_rollback(True)
                return Response(
                {"error": f"Platform '{data['platformname']}' not found"},
                status=status.HTTP_400_BAD_REQUEST
                )
            
            last_id = Movies.objects.aggregate(Max('movieid'))['movieid__max'] or 0
            new_id  = last_id + 1

            movie = Movies.objects.create(
                movieid      = new_id,
                title        = data['title'],
                releaseyear  = data['releaseyear'],
                duration     = data['duration'],
                platformname = platform,                # now this is a proper instance
                poster_url   = data.get('poster_url')
            )

            # 2) Link a genre
            try:
                genre_obj = Genres.objects.get(genrename__iexact=data['genre'])
            except Genres.DoesNotExist:
                transaction.set_rollback(True)
                return Response(
                    {'error': f"Genre '{data['genre']}' not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            BelongsTo.objects.create(movieid=movie, genrename=genre_obj)

            # 3) Link the actor
            try:
                actor_fc = FilmCrew.objects.get(crewid=data['actor_id'])
            except FilmCrew.DoesNotExist:
                transaction.set_rollback(True)
                return Response(
                    {'error': f"Actor with CrewID={data['actor_id']} not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            PartOf.objects.create(
                movieid=movie,
                crewid =actor_fc,
                role   ='Actor'
            )

            # 4) Link the director
            try:
                director_fc = FilmCrew.objects.get(crewid=data['director_id'])
            except FilmCrew.DoesNotExist:
                transaction.set_rollback(True)
                return Response(
                    {'error': f"Director with CrewID={data['director_id']} not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            PartOf.objects.create(
                movieid=movie,
                crewid =director_fc,
                role   ='Director'
            )

        # 5) Return the newly created movie
        serializer = self.get_serializer(movie)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        movie = self.get_object()
        data  = request.data

        # begin atomic to roll back if anything fails
        with transaction.atomic():
            # 1) title
            movie.title       = data.get('title', movie.title)
            

            # 2) platform → StreamingPlatforms FK
            if 'platformname' in data:
                try:
                    plat = StreamingPlatforms.objects.get(
                        platformname__iexact=data['platformname']
                    )
                except StreamingPlatforms.DoesNotExist:
                    return Response(
                      {'error': f"Platform '{data['platformname']}' not found"},
                      status=status.HTTP_400_BAD_REQUEST
                    )
                movie.platformname = plat

            # 3) poster
            if 'poster_url' in data:
                movie.poster_url = data['poster_url']

            movie.save()

            # 4) genre (BelongsTo)
            if 'genre' in data:
                # remove old link(s)
                BelongsTo.objects.filter(movieid=movie).delete()
                try:
                    g = Genres.objects.get(genrename__iexact=data['genre'])
                except Genres.DoesNotExist:
                    transaction.set_rollback(True)
                    return Response(
                      {'error': f"Genre '{data['genre']}' not found"},
                      status=status.HTTP_400_BAD_REQUEST
                    )
                BelongsTo.objects.create(movieid=movie, genrename=g)

        # return updated
        serializer = self.get_serializer(movie)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'], url_path='recommend')
    def recommend(self, request):
        qs = self.get_queryset()
        actor_id    = request.query_params.get('actor_id')
        director_id = request.query_params.get('director_id')
        genre_name  = request.query_params.get('genre_id')
        year        = request.query_params.get('year')

        if actor_id:
            qs = qs.filter(partof__crewid=actor_id, partof__role='Actor')
        if director_id:
            qs = qs.filter(partof__crewid=director_id, partof__role='Director')
        if genre_name:
            qs = qs.filter(belongsto__genrename__genrename__iexact=genre_name)
        if year:
            qs = qs.filter(releaseyear=year)

        qs = qs.distinct()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        movie = self.get_object()
        serializer = self.get_serializer(movie)
        return Response(serializer.data)

   
    @action(detail=True, methods=['get'], url_path='genres')
    def genres(self, request, pk=None):
        belongs_to = BelongsTo.objects.filter(movieid=pk)
        genres = [b.genrename for b in belongs_to]
        genre_data = [{'genrename': genre.genrename} for genre in genres]
        return Response(genre_data)

   
    @action(detail=True, methods=['get'], url_path='actors')
    def actors(self, request, pk=None):
        part_of = PartOf.objects.filter(movieid=pk, role='Actor').select_related('crewid')
        actors = [{'firstname': p.crewid.firstname, 'lastname': p.crewid.lastname} for p in part_of]
        return Response(actors)

   
    @action(detail=True, methods=['get'], url_path='directors')
    def directors(self, request, pk=None):
        part_of = PartOf.objects.filter(movieid=pk, role='Director').select_related('crewid')
        directors = [{'firstname': p.crewid.firstname, 'lastname': p.crewid.lastname} for p in part_of]
        return Response(directors)

   
    @action(detail=True, methods=['get'], url_path='reviews')
    def reviews(self, request, pk=None):
        reviews = Reviews.objects.filter(movieid=pk).select_related('userid')
        review_data = [
            {
                'rating': r.rating,
                'content': r.content,
                'reviewer': f"{r.userid.firstname} {r.userid.lastname}" if r.userid else "Anonymous",
                'reviewdate': r.reviewdate.strftime('%Y‑%m‑%d')
            }
            for r in reviews
        ]
        return Response(review_data)

class ReviewsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reviews.objects.all()
    serializer_class = ReviewSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        cont = self.request.query_params.get('content')
        if content:
            return qs.filter(content=cont) 

        return qs.none()
    
    def create(self, request, *args, **kwargs):
        data = request.data
        required = ('userid', 'rating', 'content', 'moviename')
        missing = [f for f in required if not data.get(f)]
        if missing:
            return Response(
                {'error': 'Missing required fields: ' + ', '.join(missing)},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # 1) fetch existing user by ID
            try:
                user = Users.objects.get(pk=data['userid'])
            except Users.DoesNotExist:
                return Response(
                    {'error': f"User with id={data['userid']} not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2) look up the movie by title
            try:
                movie = Movies.objects.get(title__iexact=data['moviename'])
            except Movies.DoesNotExist:
                return Response(
                    {'error': f"Movie '{data['moviename']}' not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 3) create the review
            review = Reviews.objects.create(
                userid     = user,
                movieid    = movie,
                rating     = data['rating'],
                content    = data['content'],
                reviewdate = date.today()
            )

        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        data = request.data
        required = ('firstname', 'lastname', 'email', 'rating', 'content', 'moviename')
        if not all(data.get(f) for f in required):
            return Response(
                {'error': 'Missing required fields: ' + ', '.join(required)},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # 1) fetch existing user or fail
            try:
                user = Users.objects.get(email__iexact=data['email'])
            except Users.DoesNotExist:
                return Response(
                    {'error': 'Only registered users may submit reviews'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # (optional) you could verify first/last name matches:
            if user.firstname.lower() != data['firstname'].lower() \
            or user.lastname.lower()  != data['lastname'].lower():
                return Response(
                    {'error': 'Name does not match our records'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2) look up the movie by title
            try:
                movie = Movies.objects.get(title__iexact=data['moviename'])
            except Movies.DoesNotExist:
                return Response(
                    {'error': f"Movie '{data['moviename']}' not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 3) create the review
            review = Reviews.objects.create(
                userid     = user,
                movieid    = movie,
                rating     = data['rating'],
                content    = data['content'],
                reviewdate = date.today()
            )

        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='fetch')
    def fetch_review(self, request):
        user_id  = request.query_params.get('userid')
        movie_id = request.query_params.get('movieid')
        if not (user_id and movie_id):
            return Response(
                {'error': 'userid and movieid are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            review = Reviews.objects.get(userid=user_id, movieid=movie_id)
        except Reviews.DoesNotExist:
            return Response({'error': 'Review not found'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(review)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='delete')
    def delete_review(self, request):
        user_id  = request.data.get('userid')
        movie_id = request.data.get('movieid')
        if not (user_id and movie_id):
            return Response(
                {'error': 'userid and movieid are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            review = Reviews.objects.get(userid=user_id, movieid=movie_id)
        except Reviews.DoesNotExist:
            return Response({'error': 'Review not found'},
                            status=status.HTTP_404_NOT_FOUND)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UsersViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        email = self.request.query_params.get('email')
        pwd   = self.request.query_params.get('password')
        if email and pwd:
            return qs.filter(email=email, password=pwd)
            
        if email:
            return qs.filter(email=email)
            
        return qs.none()
    
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        first_name = request.data.get('firstname')
        last_name = request.data.get('lastname')
        email = request.data.get('email')
        password = request.data.get('password')
    

        # Basic backend check
        if not (first_name and last_name and email and password):
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)
            p
    

        # Check if email already exists
        if Users.objects.filter(email=email).exists():
            print(f"[Django] Email already registered: {email}")
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        # Create and save new user
        user = Users.objects.create(
            firstname=first_name,
            lastname=last_name,
            email=email,
            password=password
        )

        return Response({'message': 'User created successfully!'}, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='update-name')
    def update_name(self, request):
        """
        Expects JSON: { userId, firstname, lastname }
        """
        user_id = request.data.get('userId')
        first   = request.data.get('firstname')
        last    = request.data.get('lastname')
        print(user_id, first, last)
        if not (user_id and first and last):
            return Response({'error': 'userId, firstname and lastname are all required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return Response({'error': 'User not found'},
                            status=status.HTTP_404_NOT_FOUND)

        user.firstname = first
        user.lastname  = last
        user.save()

        return Response({
            'message':   'Name updated successfully',
            'firstname': user.firstname,
            'lastname':  user.lastname
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='update-password')
    def update_password(self, request):
        """
        Expects JSON: { userId, old_password, new_password, confirm_password }
        """
        user_id = request.data.get('userId')
        old     = request.data.get('old_password')
        new     = request.data.get('new_password')
        conf    = request.data.get('confirm_password')

        if not (user_id and old and new and conf):
            return Response({'error': 'userId, old, new and confirm are all required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return Response({'error': 'User not found'},
                            status=status.HTTP_404_NOT_FOUND)

        if old != user.password:
            return Response({'error': 'Old password is incorrect'},
                            status=status.HTTP_400_BAD_REQUEST)
        if new != conf:
            return Response({'error': 'New passwords do not match'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.password = new
        user.save()
        return Response({'message': 'Password updated successfully'},
                        status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='update-email')
    def update_email(self, request):
        """
        Expects JSON: { userId, email }
        """
        user_id  = request.data.get('userId')
        new_email = request.data.get('email')

        if not (user_id and new_email):
            return Response(
                {'error': 'userId and email are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for uniqueness
        if Users.objects.filter(email=new_email).exclude(pk=user_id).exists():
            return Response(
                {'error': 'That email is already in use'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        user.email = new_email
        user.save()

        return Response(
            {'message': 'Email updated successfully', 'email': user.email},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], url_path='update-password')
    def admin_update_password(self, request):
        """
        Expects JSON: { userId, new_password, confirm_password }
        """
        user_id = request.data.get('userId')
        new     = request.data.get('new_password')
        conf    = request.data.get('confirm_password')

        if not (user_id and new and conf):
            return Response({'error': 'userId, new and confirm are all required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return Response({'error': 'User not found'},
                            status=status.HTTP_404_NOT_FOUND)

        if new != conf:
            return Response({'error': 'New passwords do not match'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.password = new
        user.save()
        return Response({'message': 'Password updated successfully'},
                        status=status.HTTP_200_OK)
    

class AdminsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Admins.objects.all()
    serializer_class = AdminsSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        email = self.request.query_params.get('email')
        pwd   = self.request.query_params.get('password')
        if email and pwd:
            return qs.filter(email=email, password=pwd)
        return qs.none()
    
    
    
class StreamingPlatformsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StreamingPlatforms.objects.all().order_by('platformname')
    serializer_class = StreamingPlatformSerializer


class AdminMovieManagementViewSet(viewsets.GenericViewSet):
   
    serializer_class = AdminMovieManagementSerializer
    queryset         = AdminMovieManagement.objects.all()

    def create(self, request, *args, **kwargs):
        admin_id = request.data.get('adminid')
        movie_id = request.data.get('movieid')
        if not (admin_id and movie_id):
            return Response(
                {'error': 'adminid and movieid are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # lookup and guard
        try:
            admin = Admins.objects.get(adminid=admin_id)
        except Admins.DoesNotExist:
            return Response(
                {'error': f'Admin with ID={admin_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            movie = Movies.objects.get(movieid=movie_id)
        except Movies.DoesNotExist:
            return Response(
                {'error': f'Movie with ID={movie_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # create or no‑op if already exists
        with transaction.atomic():
            obj, created = AdminMovieManagement.objects.get_or_create(
                adminid=admin,
                movieid=movie
            )

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status_code)
    
class ReviewModerationViewSet(viewsets.GenericViewSet):
    
    serializer_class = ReviewModerationSerializer
    queryset         = ReviewModeration.objects.all()

    def create(self, request, *args, **kwargs):
        u_id = request.data.get('userid')
        m_id = request.data.get('movieid')
        a_id = request.data.get('adminid')
        if not (u_id and m_id and a_id):
            return Response(
                {'error': 'userid, movieid and adminid are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate foreign keys
        try:
            user  = Users.objects.get(userid=u_id)
            movie = Movies.objects.get(movieid=m_id)
            admin = Admins.objects.get(adminid=a_id)
        except (Users.DoesNotExist, Movies.DoesNotExist, Admins.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            obj, created = ReviewModeration.objects.get_or_create(
                userid = user,
                movieid= movie,
                adminid= admin
            )

        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=code)