import datetime
from time import time

from django.db import models



types = [('None','None'),('cvr','cvr'),('asr','asr'),('vvk','vvk'),('vsr','vsr'),('sac','sac')]
H_types=[('None','None'),('AC','AC'),('Non AC','Non AC')]
class Profile(models.Model):
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    date = models.DateField()
    phone = models.BigIntegerField(primary_key=True)
    parentphone=models.BigIntegerField(null=True)
    email = models.EmailField()
    roomno = models.IntegerField()
    address = models.CharField(max_length=500,null=True)
    college = models.CharField(max_length=200)
    course = models.CharField(max_length=200,null=True)
    hostelname = models.CharField(choices=types,max_length=20,null=True,blank=False,default='employee')
    hosteltype=models.CharField(choices=H_types,max_length=20,null=True,blank=False,default='non_ac')
    present = models.BooleanField(default=False)
    image = models.ImageField()
    updated = models.DateTimeField(auto_now=True)
    shift = models.TimeField(default=datetime.time(20, 45))
    def __str__(self):
        return self.first_name +' '+self.last_name


class LastFace(models.Model):
    last_face = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.last_face)
