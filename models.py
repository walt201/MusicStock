from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class GameUser(models.Model):
    user = models.OneToOneField(User)
    points = models.DecimalField(max_digits=7, decimal_places=2)
    invested_points = models.DecimalField(max_digits=7, decimal_places=2)
    free_points = models.DecimalField(max_digits=7, decimal_places=2)

    def __unicode__(self):
        return u'%s' % self.user.username


class GameUserData(models.Model):
    user = models.ForeignKey(GameUser) #Who owns the trade
    date = models.DateTimeField('date created', auto_now_add=True)
    points = models.DecimalField(max_digits=7, decimal_places=2)
    invested_points = models.DecimalField(max_digits=7, decimal_places=2)
    free_points = models.DecimalField(max_digits=7, decimal_places=2)
    rank = models.IntegerField(null=True,blank=True)


class Artist(models.Model):
    name = models.CharField(max_length=100)
    short_description = models.TextField(max_length=1000,null=True,blank=True)
    long_description = models.TextField(max_length=2000,null=True,blank=True)
    icon_URL = models.TextField(max_length=500,null=True,blank=True)
    cover_URL = models.TextField(max_length=500,null=True,blank=True)
    pic3_URL = models.TextField(max_length=500,null=True,blank=True)
    soundcloud_URL = models.TextField(max_length=1000,null=True,blank=True)
    metric = models.TextField(max_length=500,null=True,blank=True)
    metric2 = models.TextField(max_length=500,null=True,blank=True)
    youtube_URL = models.TextField(max_length=500,null=True,blank=True)
    twitter_URL = models.TextField(max_length=500,null=True,blank=True)
    is_featured = models.BooleanField(null=False,blank=False)
    price = models.DecimalField(max_digits=7, decimal_places=3,null=True,blank=True)
    yesterday_price = models.DecimalField(max_digits=7, decimal_places=3,null=True,blank=True)
    week_price = models.DecimalField(max_digits=7, decimal_places=3,null=True,blank=True)
    soundcloud_id = models.TextField(max_length=200,null=True,blank=True)
    NSB_id = models.TextField(max_length=200,null=True,blank=True)

    def __unicode__(self):
        return u'%s' % self.name


class Investment(models.Model):
    user = models.ForeignKey(GameUser)
    media = models.ForeignKey(Artist)
    buy_price = models.DecimalField(max_digits=6, decimal_places=2,default=5)
    sell_price = models.DecimalField(max_digits=6, decimal_places=2, null=True,blank=True)
    value = models.DecimalField(max_digits=7, decimal_places=2)
    shares = models.DecimalField(max_digits=7, decimal_places=2, null=True,blank=True) #Shares bought
    buy_date = models.DateTimeField('date created', auto_now_add=True)
    sell_date = models.DateTimeField(null=True,blank=True)

    def __unicode__(self):
        return u'%s traded %d in  %s' % (self.user, self.value, self.media)


class ArtistData(models.Model):
    media = models.ForeignKey(Artist)
    date = models.DateTimeField('date created', auto_now_add=True)
    value = models.DecimalField(max_digits=6, decimal_places=2, null=True,blank=True)
    spotify_followers = models.IntegerField(null=True,blank=True)
    spotify_popularity = models.IntegerField(null=True,blank=True)
    youtube_views =  models.IntegerField(null=True,blank=True)
    youtube_downvotes =  models.IntegerField(null=True,blank=True)
    vevo_views = models.IntegerField(null=True,blank=True)
    wikipedia_view = models.IntegerField(null=True,blank=True)
    twitter_mentions = models.IntegerField(null=True,blank=True)
    twitter_retweets = models.IntegerField(null=True,blank=True)
    sentiment = models.IntegerField(null=True,blank=True)
    billboard_ranking = models.IntegerField(null=True,blank=True)
    billboard_ranking2 = models.IntegerField(null=True,blank=True)
    type = models.TextField(max_length=500,null=True,blank=True)
    category = models.TextField(max_length=500,null=True,blank=True)

    def __unicode__(self):
        return u'%s at %d' % (self.media, self.value)


class Reward(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=2000,null=True,blank=True)
    in_game_price = models.DecimalField(max_digits=7, decimal_places=2,null=True,blank=True)
    real_price = models.DecimalField(max_digits=7, decimal_places=2,null=True,blank=True)
    amazon_image = models.TextField(max_length=2000,null=True,blank=True)
    amazon_graphic = models.TextField(max_length=2000,null=True,blank=True)
    name_link = models.TextField(max_length=1000,null=True,blank=True)
    alt_image_url = models.TextField(max_length=1000,null=True,blank=True)

    def __unicode__(self):
        return u'%s' % (self.name)


class GrammyEntry(models.Model):
    user = models.ForeignKey(GameUser)
    date = models.DateTimeField('date created', auto_now_add=True)
    choice1 = models.TextField(max_length=150,null=True,blank=True)
    choice2 = models.TextField(max_length=150,null=True,blank=True)
    choice3 = models.TextField(max_length=150,null=True,blank=True)
    choice4 = models.TextField(max_length=150,null=True,blank=True)
    choice5 = models.TextField(max_length=150,null=True,blank=True)
    number_correct = models.IntegerField(null=True,blank=True)
 91  update_price.py 
@@ -0,0 +1,91 @@
from django.core.management.base import BaseCommand, CommandError
from game.models import Artist, ArtistData, GameUser, GameUserData, Investment
import random
import requests


class Command(BaseCommand):

    #method run once an hour by Django to calculate the stock price for each artist
    def handle(self, *args, **options):
        all_artists = Artist.objects.all()
        for artist in all_artists:
            try:
                spotify_data = self.get_spotify_data(artist)
                price = self.compute_artist_price(spotify_data)
                self.update_artist(artist, price, spotify_data[1], spotify_data[0])
            except:
                pass
        self.update_investments()
        self.update_users()

    def get_spotify_data(self, artist):
        cleaned_artist_name = artist.name.replace(" ", "%20")
        r = requests.get('https://api.spotify.com/v1/search?q=' + cleaned_artist_name + '&type=artist').json()
        popularity = r['artists']['items'][0]['popularity']
        id = r['artists']['items'][0]['id']
        artist_request = requests.get('https://api.spotify.com/v1/artists/' + id).json()
        followers = artist_request['followers']['total']
        return (popularity, followers)

    def compute_artist_price(self, spotify_data):
        popularity = spotify_data[0]
        followers = spotify_data[1]
        # pricing algo for lower popularity artists
        if (popularity < 57):
            variability = (popularity - 35.0) / 100.0
            noisy_popularity = popularity + random.gauss(0, variability)  # adding noise to spotify popularity
            price = (noisy_popularity - 45) * .56 + 2
            if (price < 2):
                price = 1.50  # price floor
        # pricing algo for higher popularity artists
        if (popularity >= 57):
            variability = (popularity - 30.0) / 100.0
            noisy_popularity = popularity + random.gauss(0, variability)  # adding noise to spotify popularity
            price = (noisy_popularity - 50) * 1.70 + (popularity - 73) * .2
            # extra price for very high popularity artists to create increased differentiation
            if (popularity > 81):
                price += (popularity - 82) * 0.4 * random.gauss(1, 0.01)
            if (popularity > 88):
                price += (popularity - 88) * 0.6 * random.gauss(1, 0.02)
            if (popularity > 92):
                price += (popularity - 92) * .75 * random.gauss(1, 0.03)
        rounded_price = round(price, 2)
        return rounded_price

    def update_artist(self, artist, price, spotify_followers, spotify_popularity):
        cur_artist = artist
        cur_artist.price = price
        cur_artist.save()
        new_data = ArtistData(media=artist, value=price, spotify_followers=spotify_followers,
                        spotify_popularity=spotify_popularity)
        new_data.save()

    def update_investments(self):
        investment_list = Investment.objects.all().exclude(shares=0)
        for investment in investment_list:
            if(investment.shares > 0):
                investment.value = investment.shares * investment.media.price
                investment.save()

    def update_users(self):
        all_users = GameUser.objects.all()
        for user in all_users:
            net_worth = user.free_points
            if (net_worth < 0):
                net_worth = 0
                user.free_points = 0
                user.save()
            investment_list = Investment.objects.all().filter(user=user).exclude(shares=0)
            invested_points = 0
            for investment in investment_list:
                if (investment.shares > 0):
                    net_worth += investment.shares * investment.media.price
                    invested_points += investment.shares * investment.media.price
            if (net_worth >= 0 and net_worth < 99999.99 and invested_points >= 0 and invested_points < 99999.99):
                user.points = net_worth
                user.invested_points = invested_points
                user.save()
                cur_user_data = GameUserData(user=user, points=net_worth, invested_points=user.invested_points,
                                free_points=user.free_points)
                cur_user_data.save()
