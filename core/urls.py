from django.urls import path,include
from .views import *


urlpatterns = [
    path('',home, name='home'),
    path('signin', signin, name= 'signin'),
    path('signup', signup, name='signup'),
    path('signout/', signout, name='signout'),


    path('index/', index,name='index'),
    path('ajax/', ajax, name= 'ajax'),
    path('scan/',scan,name='scan'),
    path('profiles/', profiles, name= 'profiles'),
    path('details/', details, name= 'details'),

    path('add_profile/',add_profile,name='add_profile'),
    path('edit_profile/<int:id>/',edit_profile,name='edit_profile'),
    path('delete_profile/<int:id>/',delete_profile,name='delete_profile'),


    path('clear_history/',clear_history,name='clear_history'),
    path('reset/',reset,name='reset'),

    path('camoff/',camoff,name='camoff'),

    path('attendance/',day_attendance,name='day_attendance'),
    path('month_attendance/',month_attendance,name='month_attendance'),
    path('month_attendance/dayattendance/',download,name='download'),
    path('month_attendance/attendanceview/',attendanceview,name='attendanceview'),
    path('month_attendance/hostelreport',hostelreport,name='hostelreport'),
    path('month_attendance/studentreport/',studentreport,name='studentreport'),

    path('index/manual_checking',manual_checking,name='manual_checking'),
    path('index/manual_attendance',manual_attendance,name='manual_attendance')



]
