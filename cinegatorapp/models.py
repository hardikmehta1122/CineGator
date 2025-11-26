from django.db import models

class Users(models.Model):
    userid = models.AutoField(db_column='UserID', primary_key=True)
    firstname = models.CharField(db_column='FirstName', max_length=50)
    lastname = models.CharField(db_column='LastName', max_length=50)
    email = models.CharField(db_column='Email', max_length=100, unique=True)
    password = models.CharField(db_column='Password', max_length=255)

    class Meta:
        db_table = 'Users'
        managed = True
    


class Admins(models.Model):
    adminid = models.AutoField(db_column='AdminID', primary_key=True)
    firstname = models.CharField(db_column='FirstName', max_length=50)
    lastname = models.CharField(db_column='LastName', max_length=50)
    email = models.CharField(db_column='Email', max_length=100, unique=True)
    password = models.CharField(db_column='Password', max_length=255)

    class Meta:
        db_table = 'Admins'
        managed = False


class Genres(models.Model):
    genrename = models.CharField(db_column='GenreName', max_length=50, primary_key=True)

    class Meta:
        db_table = 'Genres'
        managed = False


class StreamingPlatforms(models.Model):
    platformname = models.CharField(db_column='PlatformName', max_length=100, primary_key=True)
    url = models.CharField(db_column='URL', max_length=255)

    class Meta:
        db_table = 'StreamingPlatforms'
        managed = False


class Movies(models.Model):
    movieid = models.IntegerField(db_column='MovieID', primary_key=True)
    title = models.CharField(db_column='Title', max_length=255)

    releaseyear = models.CharField(db_column='ReleaseYear', max_length=4)
    duration = models.IntegerField(db_column='Duration')
    platformname = models.ForeignKey(
        StreamingPlatforms,
        models.DO_NOTHING,
        db_column='PlatformName',
        null=True,
        blank=True
    )
    poster_url = models.URLField(db_column='PosterURL', max_length=500, null=True, blank=True)


    class Meta:
        db_table = 'Movies'
        managed = False


class FilmCrew(models.Model):
    crewid = models.AutoField(db_column='CrewID', primary_key=True)
    firstname = models.CharField(db_column='FirstName', max_length=50)
    lastname = models.CharField(db_column='LastName', max_length=50)
    dob = models.DateField(db_column='DOB')
    nationality = models.CharField(db_column='Nationality', max_length=50)

    class Meta:
        db_table = 'FilmCrew'
        managed = False


class Actors(models.Model):
    crewid = models.OneToOneField(
        FilmCrew,
        models.DO_NOTHING,
        db_column='CrewID',
        primary_key=True
    )

    class Meta:
        db_table = 'Actors'
        managed = False


class Directors(models.Model):
    crewid = models.OneToOneField(
        FilmCrew,
        models.DO_NOTHING,
        db_column='CrewID',
        primary_key=True
    )

    class Meta:
        db_table = 'Directors'
        managed = False




class BelongsTo(models.Model):
   
    movieid = models.ForeignKey(
        Movies,
        models.DO_NOTHING,
        db_column='MovieID'
    )
    genrename = models.ForeignKey(
        Genres,
        models.DO_NOTHING,
        db_column='GenreName'
    )

    class Meta:
        db_table = 'BelongsTo'
        managed = False
        unique_together = (('movieid', 'genrename'),)


class PartOf(models.Model):
    crewid = models.ForeignKey(
        FilmCrew,
        models.DO_NOTHING,
        db_column='CrewID'
    )
    movieid = models.ForeignKey(
        Movies,
        models.DO_NOTHING,
        db_column='MovieID'
    )
    role = models.CharField(db_column='Role', max_length=8)


    class Meta:
        db_table = 'PartOf'
        managed = False
        unique_together = (('crewid', 'movieid', 'role'),)


class Reviews(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='UserID')
    movieid = models.ForeignKey(Movies, models.DO_NOTHING, db_column='MovieID')
    content = models.CharField(db_column='Content', max_length=100)
    rating = models.IntegerField(db_column='Rating')
    reviewdate = models.DateField(db_column='ReviewDate')

    class Meta:
        db_table = 'Reviews'
        managed = False
        unique_together = (('userid', 'movieid'),)


class ReviewModeration(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='UserID')
    movieid = models.ForeignKey(Movies, models.DO_NOTHING, db_column='MovieID')
    adminid = models.ForeignKey(Admins, models.DO_NOTHING, db_column='AdminID')

    class Meta:
        db_table = 'ReviewModeration'
        managed = False
        unique_together = (('userid', 'movieid', 'adminid'),)


class AdminMovieManagement(models.Model):
    adminid = models.ForeignKey(Admins, models.DO_NOTHING, db_column='AdminID')
    movieid = models.ForeignKey(Movies, models.DO_NOTHING, db_column='MovieID')

    class Meta:
        db_table = 'AdminMovieManagement'
        managed = False
        unique_together = (('adminid', 'movieid'),)
