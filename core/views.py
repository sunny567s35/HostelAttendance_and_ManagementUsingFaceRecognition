from django.shortcuts import render, HttpResponse, redirect
from .models import *
from .forms import *
import face_recognition
import cv2
import numpy as np
import winsound
from django.db.models import Q
from playsound import playsound
import os
import pickle
from csv import writer
from csv import reader
from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.urls import reverse
import pandas as pd
from datetime import datetime
import datetime as dta
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
import pathlib
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.views.decorators.csrf import ensure_csrf_cookie,csrf_protect



last_face = 0
current_path = os.path.dirname(__file__)
sound_folder = os.path.join(current_path, 'sound/')
face_list_file = os.path.join(current_path, 'face_list.txt')
sound = os.path.join(sound_folder, 'beep.wav')
nameList=[]
flag=0

@ensure_csrf_cookie
@csrf_protect
@login_required
def index(request):
    scanned = LastFace.objects.all().order_by('date').reverse()
    present = Profile.objects.filter(present=True).order_by('updated').reverse()
    absent = Profile.objects.filter(present=False).order_by('shift')
    context = {
        'scanned': scanned,
        'present': present,
        'absent': absent,
    }
    return render(request, 'core/index.html', context)

@login_required
def ajax(request):
    last_face = LastFace.objects.last()
    context = {
        'last_face': last_face
    }
    return render(request, 'core/ajax.html', context)

@login_required
def scan(request):
    name=0
    name1='Unknown!!'
    global last_face
    global flag
    flag=0
    known_face_encodings = []
    known_face_names = []
    date=datetime.now().strftime("%Y-%m-%d")
    profiles = Profile.objects.all()
    data = {}
    attendance={}
    if os.path.getsize("media/picklefiles/pickle_file.pickle") > 0:
        data = pickle.loads(open('media/picklefiles/pickle_file.pickle',"rb").read())
    pickel_attendance(str(date))
    if os.path.getsize("media/picklefiles/attendance.pickle") > 0:
        attendance=pickle.loads(open('media/picklefiles/attendance.pickle',"rb").read())
    #print(data)
    #print(attendance)
    att=attendance[date]
    for profile in profiles:
        person = str(profile.phone)
        person_name=profile.first_name
        # image_of_person = face_recognition.load_image_file(f'media/{person}')
        # person_face_encoding = face_recognition.face_encodings(image_of_person)[0]
        known_face_encodings.append(data[person])
        known_face_names.append(profile.phone)


    video_capture = cv2.VideoCapture(0)

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    
    while True:
        if(flag==1):
            break
        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0),None,fx=0.25, fy=0.25)
        # rgb_small_frame = small_frame[:, :, ::-1]
        rgb_small_frame=cv2.cvtColor(small_frame,cv2.COLOR_BGR2RGB)
        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame,number_of_times_to_upsample=2)
            face_encodings = face_recognition.face_encodings(rgb_small_frame,model='large',known_face_locations=face_locations )
            face_names = []
            for face_encoding in face_encodings:
                mat = False
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = 0
                name1="Unknown!!"
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if(face_distances[best_match_index] <= 0.38):
                    mat = True
                if mat == True:
                    name =  known_face_names[best_match_index]
                elif mat ==False:
                
                    name = 0
                if matches[best_match_index] and mat:
                    print(12345)
                    name = known_face_names[best_match_index]
                    profile = Profile.objects.get(pk=name)
                    name1=profile.first_name
                    if profile.present == True or profile.pk in att[1]:
                        # messages.error(request,'Already present!')
                        pass
                    else:
                        #print(profile.shift)
                        profile.present = True
                        winsound.PlaySound(sound, winsound.SND_ASYNC)
                        if len(att[0])==0:
                            #print('all attendance over!')
                            messages.success(request, "All Attendance Over!!")
                            break
                        att[0].remove((profile.pk))
                        att[1].append(profile.pk)
                        #print(attendance[date])
                        # markAttendance(profile)
                        profile.save()
                    
                    if last_face != name and name != 0:
                        print(123)
                        last_face = LastFace(last_face=name)
                        print(last_face)
                        last_face.save()
                        last_face = name
                        # winsound.PlaySound(sound, winsound.SND_ASYNC)
                    else:
                        pass
                print(name)
                print(last_face != name)
                print(last_face)
                face_names.append(name1)
        process_this_frame = not process_this_frame
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35),
                          (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, str(name), (left + 6, bottom - 6),
                        font, 0.5, (255, 255, 255), 1)
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            #print("db sucessfully update!")
            messages.success(request, "attendance db Successfully updated!!")
            break
    video_capture.release()
    cv2.destroyAllWindows()
    attendance[date]=att
    pickle_file=open('media/picklefiles/attendance.pickle', 'wb')
    pickle.dump(attendance, pickle_file )
    return HttpResponse('scaner closed', last_face)

@login_required
def profiles(request):
    profiles = Profile.objects.all()
    context = {
        'profiles': profiles
    }
    return render(request, 'core/profiles.html', context)

@login_required
def details(request):
    try:
        last_face = LastFace.objects.last().last_face
        profile = Profile.objects.get(pk=last_face)
    except Exception as e:
        print(e)
        last_face = None
        profile = None
        print(404)

    context = {
        'profile': profile,
        'last_face': last_face
    }
    return render(request, 'core/details.html', context)

@login_required
def add_profile(request):
    form = ProfileForm
    try:
        if request.method == 'POST':
            form = ProfileForm(request.POST,request.FILES)
            print(form.is_valid())
            if form.is_valid():
                #encoding_image(name,image)
                encoding_image(str(int(request.POST.get("phone"))),request.FILES["image"])
                form.save()
                # encoding_image(str(int(request.POST.get("phone"))),request.FILES["image"])
                return redirect('profiles')
            else:
                messages.error(request,"One field is missing ,tryagain!")
                return redirect('index')
    except:
        messages.error(request,"Try again!add photo and phoneno")
    context={'form':form}
    return render(request,'core/add_profile.html',context)

@login_required
def edit_profile(request,id):
    profile = Profile.objects.get(pk=id)
    form = ProfileForm(instance=profile)
    try:
        if request.method == 'POST':
            form = ProfileForm(request.POST,request.FILES,instance=profile)
            #print(request.POST.get("phone"),profile.pk)
            if int(request.POST.get("phone"))!=profile.pk:
                messages.error(request,"Can't Change Your phone number!!")
                return redirect('profiles')
            #print(str(profile.image))
            image_path=str(profile.image)
            #print(123)
            # if str(profile.image)!=str(request.FILES["image"]):
            #     #print(12345)
            #     os.remove("media/"+str(profile.image))
            #     profile.image=request.FILES["image"]
            #     os.remove("media/"+str(request.FILES["image"]))
            if form.is_valid():
                #print(404)
                
                #encoding_image(name,image)
                form.save()
                try:
                    encoding_image(str(int(request.POST.get("phone"))),request.FILES["image"])
                    if image_path!=str(request.FILES["image"]):
                        #print(12345)
                        os.remove("media/"+image_path)
                        #os.remove("media/"+str(request.FILES["image"]))
                    #encoding_image(request.POST.get("phone"),request.POST.get("image"))
                    messages.success(request,'update image Sucessfully!')
                except:
                    messages.error(request,'update Sucessfully!')
                return redirect('profiles')
            else :
                messages.error(request,"Enter All the details !")
                return redirect('index')
    except Exception as e:
        #print(1)
        #print(e)
        messages.error(request,"Try again! add photo and phoneno")
    context={'form':form}
    return render(request,'core/add_profile.html',context)

@login_required
def delete_profile(request,id):
    profile = Profile.objects.get(pk=id)
    del_dict={}
    if os.path.getsize("media/picklefiles/delete_user.pickle") > 0:
        pickle_del_file = open('media/picklefiles/delete_user.pickle', 'rb')
        del_dict=pickle.load(pickle_del_file)
    del_dict[profile.pk]={'first_name':profile.first_name,'last_name':profile.last_name,'date':profile.date,'hostelname':profile.hostelname,'hosteltype':profile.hosteltype,'roomno':profile.roomno,'phone':profile.phone}
    pickle_del_file1 = open('media/picklefiles/delete_user.pickle', 'wb')
    pickle.dump(del_dict, pickle_del_file1)
    pickle_del_file1.close()
    image_path=profile.image
    image_phone=str(profile.pk)
    profile.delete()
    os.remove("media/"+str(image_path))
    pickled_object={}
    if os.path.getsize("media/picklefiles/pickle_file.pickle") > 0:
        pickle_file = open('media/picklefiles/pickle_file.pickle', 'rb')
        pickled_object = pickle.load(pickle_file)
    if image_phone in pickled_object.keys():
            del pickled_object[image_phone]
            pickle_file1=open('media/picklefiles/pickle_file.pickle', 'wb')
            pickle.dump(pickled_object, pickle_file1 )
            pickle_file1.close()
    return redirect('profiles')

@login_required
def clear_history(request):
    history = LastFace.objects.all()
    history.delete()
    return redirect('index')

@login_required
def reset(request):
    profiles = Profile.objects.all()
    for profile in profiles:
        if profile.present == True:
            profile.present = False
            profile.save()
        else:
            pass
    history = LastFace.objects.all()
    history.delete()
    return redirect('index')



# def markAttendance(profile):
#     now = datetime.now()
#     profiles = Profile.objects.all()
#     today = now.strftime("%Y/%m/%d_%H:%M")
#     filename = "media/documents/" + datetime.now().strftime("%Y-%m-%d") + ".csv"
#     #print(401)
#     try:
#         #print(402)
#         with open(filename, 'a') as f:
#             #print(403)
#             #print(profile.first_name)
#             #for profile in nameList :
#                 # now = datetime.now()
#                 # dtString = now.strftime('%H:%M:%S')
#                 # f.writelines(f'\n{name},{dtString},{sid_name[sid.index(name)]}')
#             f.writelines(f'\n{profile.first_name},{profile.last_name},{profile.date},{profile.hostelname},{profile.roomno},{profile.phone}')
#             f.close()
#     except:
#         # #print(404)
#         # for profile in profiles:
#         #     if profile.present == True:
#         #         profile.present = False
#         #         profile.save()
#         #     else:
#         #         pass
#         # history = LastFace.objects.all()
#         # history.delete()
#         with open(filename, 'w') as f:
#             #print(profile.first_name)
#             #for profile in nameList :
#                 # now = datetime.now()
#                 # dtString = now.strftime('%H:%M:%S')
#                 # f.writelines(f'\n{name},{dtString},{sid_name[sid.index(name)]}')
#             #print('write')
#             f.writelines(f'first_name,last_name,date,hostelname,roomno,phone')
#             # f.writelines(f'\n{profile.first_name},{profile.last_name},{profile.date},{profile.hostelname},{profile.roomno},{profile.phone}')
#             f.close()

 
def encoding_image(name,image):
    # Step 1: Open the pickle file in append mode
    #print(404)
    try:
        #print(os.path.getsize("media/picklefiles/pickle_file.pickle"))
        if os.path.getsize("media/picklefiles/pickle_file.pickle") > 0:
            #print(1)
            pickle_file = open('media/picklefiles/pickle_file.pickle', 'rb')
            #print(2)
            pickled_object = pickle.load(pickle_file)

        else:
            pickled_object={}
        image_of_person = face_recognition.load_image_file(image)
        person_face_encoding = face_recognition.face_encodings(image_of_person,num_jitters=100)[0]
        if name in pickled_object.keys():
            del pickled_object[name]
        pickled_object[name]=person_face_encoding
        pickle_file=open('media/picklefiles/pickle_file.pickle', 'wb')
        pickle.dump(pickled_object, pickle_file )
        pickle_file.close()
    except EOFError:
        # #print(pickled_object = pickle.load(pickle_file))
        pickled_object = {}

def camoff(request):
    global flag
    flag=1
    #print("db sucessfully update!")
    messages.success(request, "attendance db Successfully updated!!")
    return redirect('index')

    
    



def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            login(request, user)
            # fname = user.first_name
            messages.success(request, "Logged In Sucessfully!!")
            # now = datetime.now()
            # filename = "media/documents/" + datetime.now().strftime("%Y-%m-%d") + ".csv"
            # try:
            #     #print(402)
            #     f=open(filename, 'r')
            # except:
            #     #print(404)
            #     profiles = Profile.objects.all()
            #     with open(filename, 'w') as f:
            #         #for profile in nameList :
            #             # now = datetime.now()
            #             # dtString = now.strftime('%H:%M:%S')
            #             # f.writelines(f'\n{name},{dtString},{sid_name[sid.index(name)]}')
            #         #print('write')
            #         f.writelines(f'first_name,last_name,date,hostelname,roomno,phone')
            #         # f.writelines(f'\n{profile.first_name},{profile.last_name},{profile.date},{profile.hostelname},{profile.roomno},{profile.phone}')
            #         f.close()
            #     for profile in profiles:
            #         if profile.present == True:
            #             profile.present = False
            #             profile.save()
            #         else:
            #             pass
            #     history = LastFace.objects.all()
            #     history.delete()
            return redirect('index')
            # return redirect('index_call')
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect('home')
    
    return render(request, 'core/signin.html')

@login_required
def signout(request):
    # absent()
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')

def home(request):
    return render(request,'core/open.html')

@login_required
def signup(request):
    if request.method=="POST":
        username=request.POST['username']
        fname = request.POST['fname']
        lname =request.POST['lname']
        # mobileno = request.POST['mobileno']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        if User.objects.filter(username=username).exists():
            messages.error(request,"User already exist! try other username....")
            return redirect('home')
        # if User.objects.filter(mobileno=mobileno).exists():
        #     messages.error(request,"mobileno already exist!....")
        #     return redirect('home')
        if len(username)>11:
            messages.error(request,"username must under 11 characters!....")
            return redirect('home')
        if pass1!=pass2:
            messages.error(request,"Passwoed not matched!....")
            return redirect('home')
        myuser = User.objects.create_user(username,None,pass1)
        myuser.lname=lname
        myuser.fname=fname
        myuser.save()  
        return render(request,'core/index.html')
        
        
    return render(request, "core/signup.html")


# def absent():
#     # file_path="media/documents/" + datetime.now().strftime("%Y-%m-%d") + ".csv"
#     # dt =pd.read_csv(file_path)
#     # dt=dt.sort_values('hostelname')
#     # list_present_id=dt['phone']
#     file="absentees_documents/" + datetime.now().strftime("%Y-%m-%d") + ".csv"
#     profiles = Profile.objects.all()
#     with open(file, 'w') as f:
#         f.writelines(f'first_name,last_name,date,hostelname,roomno,phone')
#         f.close()
#     for profile in profiles:
#         if profile.present == False:
#             with open(file, 'a') as f:
#                 #print(profile.first_name)
#                 f.writelines(f'\n{profile.first_name},{profile.last_name},{profile.date},{profile.hostelname},{profile.roomno},{profile.phone}')
#                 f.close()


@login_required
def download(request):
    #print(request.method)
    if request.method=='GET':
        date=request.GET.get("date", "")
        present=request.GET.get("present","")
        hostel=request.GET["hostel"]
        hosteltype=request.GET["hosteltype"]
        option=request.GET["option"]
        #print(date)
        #print(present)
        #print(hostel)
        if present==None or hostel==None:
            return redirect('index')#####
        #pickle_attenance
        if os.path.getsize("media/picklefiles/attendance.pickle") > 0:
            attendance=pickle.loads(open('media/picklefiles/attendance.pickle',"rb").read())
        else:
            attendance={}
        if os.path.getsize("media/picklefiles/delete_user.pickle") > 0:
            del_list=pickle.loads(open('media/picklefiles/delete_user.pickle',"rb").read())
        else:
            del_list={}
        #print(date)
        #print(attendance)
        if date not in attendance.keys():
            messages.success(request,"attendance not found!!")
            return redirect('index')
        att=attendance[str(date)]
        print(attendance)
        att_db=att[2][0]
        #print(att)
        if present=="Absent":
            attendance_list=att[0]
        else:
            attendance_list=att[1]
        file="media/attendance_documents/" +date+"_"+present+"_"+hostel+"_"+"file.csv"
        with open(file, 'w') as f:
            f.writelines(f'first_name,last_name,phone_number,parent_phone,hostelname,hosteltype,roomno')
            f.close()
        for i in attendance_list:
            att_user=att_db[i]
            u=[]
            try:
                if hostel=='All' and hosteltype=='All':
                    u.append(str(att_user['first_name']))
                    u.append(str(att_user['last_name']))
                    u.append(str(att_user['phone']))
                    u.append(str(att_user['parentphone']))
                    u.append(str(att_user['hostelname']))
                    u.append(str(att_user['hosteltype']))
                    u.append(str(att_user['roomno']))
                    with open(file, 'a') as f:
                        f.writelines('\n'+",".join(u))
                        f.close()
                elif hosteltype=='All':
                    if att_user['hostelname'] == hostel:
                        u.append(str(att_user['first_name']))
                        u.append(str(att_user['last_name']))
                        u.append(str(att_user['phone']))
                        u.append(str(att_user['hostelname']))
                        u.append(str(att_user['hosteltype']))
                        u.append(str(att_user['roomno']))
                        with open(file, 'a') as f:
                            f.writelines('\n'+",".join(u))
                            f.close()
                elif hostel=="All":
                    if att_user['hosteltype'] == hosteltype:
                        u.append(str(att_user['first_name']))
                        u.append(str(att_user['last_name']))
                        u.append(str(att_user['phone']))
                        u.append(str(att_user['hostelname']))
                        u.append(str(att_user['hosteltype']))
                        u.append(str(att_user['roomno']))
                        with open(file, 'a') as f:
                            f.writelines('\n'+",".join(u))
                            f.close()
            except Exception as e:
                print(e)
                pass
        dt =pd.read_csv(file)
        if hostel=="All":
            dt=dt.sort_values('roomno')
            dt=dt.sort_values('hostelname')
        else:
            dt=dt.sort_values('roomno')
            dt=dt[dt['hostelname']==hostel]

        
        #print(dt)
        dt.to_csv("media/attendance_documents/"+date+"_"+present+"_"+hostel+"_"+'file.csv',index=False)
        # return HttpResponse(dt.to_html())
        
        print(dt)
        file_server = pathlib.Path("media/attendance_documents/"+date+"_"+present+"_"+hostel+"_"+'file.csv')
        if not file_server.exists():
            messages.error(request, 'file not found.')
        else:
            if option=='download':
                file_to_download = open(str(file_server), 'rb')
                response = FileResponse(file_to_download, content_type='application/force-download')
                response['Content-Disposition'] = 'inline; filename='+date+'"_"'+present+'"_"'+hostel+"_"+hosteltype+'file.csv'
                #print(123)
                return response
            dt.insert(0,"index",[int(i) for i in range(1,len(dt)+1)])
            table_content = dt.to_html(index=False)
            context = {
                    'table_content': table_content,
                    'string':date+' || present/absent : '+present+' ||  hostel : '+hostel+' ||  hosteltype : '+hosteltype
                    }
            return  render(request, 'core/table.html', context)
    return redirect('index')
@login_required
def month_attendance(request):
    return render(request,'core/attendance.html')
@login_required
def day_attendance(request):
    return render(request,'core/day_attendance.html')
defaultphone = 0
@login_required

def manual_checking(request):
    if request.method=='GET':
        phone=request.GET['phone']
        if len(phone)<10 or len(phone)>10:
            messages.error(request,"Check phone Number!")
            return redirect('index')
        try:
            phone=int(phone)
            global defaultphone 
            defaultphone= phone
        except:
            messages.error(request,"Check phone number!!")
            return redirect('index')
        try:

            profile = Profile.objects.get(pk=phone)
            #print(1)
            context = {'profile': profile}
            return render(request,'core/manul_attendance.html',context)
        except:
            #print('sorry')
            messages.error(request,"Check phone number,Try Again!!")
            pass
    return redirect('index')
@login_required

def manual_attendance(request):
    #print(2)
    date=datetime.now().strftime("%Y-%m-%d")
    attendance={}
    if os.path.getsize("media/picklefiles/attendance.pickle") > 0:
        attendance=pickle.loads(open('media/picklefiles/attendance.pickle',"rb").read())
    #print(date)
    #print(attendance)
    att=attendance[date]
    if len(att[0])==0:
        return redirect('index')
    try:
        if request.method=='POST':
            phone=request.POST['phone']
            phone=int(phone)
            try:
                global defaultphone
                if defaultphone != phone:
                    messages.error(request,"Number Mismatch !")
                    return redirect('index')
                defaultphone=0
                profile = Profile.objects.get(pk=phone)
                if profile.present!=True and profile.pk not in att[1]:
                    profile.present=True
                    att[0].remove(profile.pk)
                    att[1].append(profile.pk)
                    messages.success(request,str(profile.pk)+'present!')
                    # markAttendance(profile)
                else:
                    messages.success(request,'Already present!')
            except:
                #print('sorry')
                messages.success(request,'Sorry! Try Again..')
                pass
    except:
        messages.success(request,'Check phone number,Try again !!')
    attendance[date]=att
    pickle_file=open('media/picklefiles/attendance.pickle', 'wb')
    pickle.dump(attendance, pickle_file )
    #print("db sucessfully update!")
    return redirect('index')



def pickel_attendance(dte):
    #print(404)
    profiles = Profile.objects.all()
    try:
        #print(os.path.getsize("media/picklefiles/attendance.pickle"))
        if os.path.getsize("media/picklefiles/attendance.pickle") > 0:
            #print(1)
            pickle_file = open('media/picklefiles/attendance.pickle', 'rb')
            #print(2)
            pickled_object = pickle.load(pickle_file)

        else:
            pickled_object={}
        if dte  in pickled_object.keys():
            l1=pickled_object[dte]
            if (len(l1[0])+len(l1[1]))==len(profiles):
                return
        attendance_list=[[],[],[]]
        d={}
        for profile in profiles:
            attendance_list[0].append(profile.pk)
            d[profile.pk]={'first_name':profile.first_name,'last_name':profile.last_name,'date':profile.date,'hostelname':profile.hostelname,'hosteltype':profile.hosteltype,'roomno':profile.roomno,'phone':profile.phone,'parentphone':profile.parentphone}
            attendance_list[2].append(d)
        pickled_object[dte]=attendance_list
        pickle_file=open('media/picklefiles/attendance.pickle', 'wb')
        pickle.dump(pickled_object, pickle_file )
        pickle_file.close()
        history = LastFace.objects.all()
        history.delete()
        
    except EOFError:
        # #print(pickled_object = pickle.load(pickle_file))
        pickled_object = {}


# def index_call(request):
#     return render(request,'core/index.html')



@login_required
def attendanceview(request):
    try:
        if request.method=='GET':
            fdate=request.GET.get("date1", "")
            tdate=request.GET.get("date2", "")
            date1=datetime.strptime(request.GET.get("date1", ""), "%Y-%m-%d").date()
            date2=datetime.strptime(request.GET.get("date2", ""), "%Y-%m-%d").date()
            present=request.GET.get("present","")
            hostel=request.GET["hostel"]
            hosteltype=request.GET["hosteltype"]
            option=request.GET["option"]
            print(hostel)
            print(hosteltype)
            if present==None or hostel==None :
                return redirect('index')#####
            #pickle_attenance
            if os.path.getsize("media/picklefiles/attendance.pickle") > 0:
                attendance=pickle.loads(open('media/picklefiles/attendance.pickle',"rb").read())
            else:
                attendance={}
            if os.path.getsize("media/picklefiles/delete_user.pickle") > 0:
                del_list=pickle.loads(open('media/picklefiles/delete_user.pickle',"rb").read())
            else:
                del_list={}
            
            delta = dta.timedelta(days=1)
            datelist=[]
            l=[]
            while (date1 <= date2):
                f=date1
                datelist.append(date1)
                l.append(f.strftime("%Y-%m-%d"))
                date1 += delta
            r=[]
            for i in l:
                if i in attendance.keys():
                    att=attendance[i]
                    r.extend(att[0])
                    r.extend(att[1])
                    r=list(set(r))
            print(r)
            file="media/attendance_documents/" +date1.strftime("%Y-%m-%d")+"to"+date2.strftime("%Y-%m-%d")+"_"+present+"_"+hostel+"_"+hosteltype+"file.csv"
            with open(file, 'w') as f:
                f.writelines('first_name,last_name,phone,parent_phone,hostelname,hosteltype,roomno,'+",".join(l)+',total_present_days,total_absent_days')
                f.close()
            for student in r:
                s=[]
                u=[]
                for date in l:
                    print(date not in attendance.keys())
                    if date not in attendance.keys():
                        print(123456)
                        s.append('No attendance')
                    else:
                        att=attendance[str(date)]
                        att_db=att[2][0]
                        if student not in att_db:
                            s.append('No data')
                            continue
                        att_user=att_db[student]
                        print(att_user)
                        if hostel=='All' and hosteltype=='All':
                            # 'first_name':profile.first_name,'last_name':profile.last_name,'date':profile.date,'hostelname':profile.hostelname,'hosteltype':profile.hosteltype,'roomno':profile.roomno,'phone':profile.phone
                            if len(u)==0:
                                u.append(str(att_user['first_name']))
                                u.append(str(att_user['last_name']))
                                u.append(str(att_user['phone']))
                                u.append(str(att_user['parentphone']))
                                u.append(str(att_user['hostelname']))
                                u.append(str(att_user['hosteltype']))
                                u.append(str(att_user['roomno']))
                            print((att_user['phone']) in att[1])
                            if (att_user['phone']) in att[1]:
                                s.append("Present")
                            elif (att_user['phone']) in att[0]:
                                s.append("Absent")
                        elif hosteltype=='All':
                            if att_user['hostelname']==hostel:
                                if len(u)==0:
                                    u.append(str(att_user['first_name']))
                                    u.append(str(att_user['last_name']))
                                    u.append(str(att_user['phone']))
                                    u.append(str(att_user['parentphone']))
                                    u.append(str(att_user['hostelname']))
                                    u.append(str(att_user['hosteltype']))
                                    u.append(str(att_user['roomno']))
                                if att_user['phone'] in att[1]:
                                    s.append("Present")
                                elif att_user['phone'] in att[0]:
                                    s.append("Absent")
                            else:
                                s.append('Shifted')
                        elif hostel=='All':
                            print(2)
                            if att_user['hosteltype']==hosteltype:
                                if len(u)==0:
                                    u.append(str(att_user['first_name']))
                                    u.append(str(att_user['last_name']))
                                    u.append(str(att_user['phone']))
                                    u.append(str(att_user['parentphone']))
                                    u.append(str(att_user['hostelname']))
                                    u.append(str(att_user['hosteltype']))
                                    u.append(str(att_user['roomno']))
                                if att_user['phone'] in att[1]:
                                    s.append("Present")
                                elif att_user['phone'] in att[0]:
                                    s.append("Absent")
                            else:
                                s.append('Shifted')
                        else:
                            if att_user['hostelname']==hostel and att_user['hosteltype']==hosteltype:
                                if len(u)==0:
                                    u.append(str(att_user['first_name']))
                                    u.append(str(att_user['last_name']))
                                    u.append(str(att_user['phone']))
                                    u.append(str(att_user['parentphone']))
                                    u.append(str(att_user['hostelname']))
                                    u.append(str(att_user['hosteltype']))
                                    u.append(str(att_user['roomno']))
                                if att_user['phone'] in att[1]:
                                    s.append("Present")
                                elif att_user['phone'] in att[0]:
                                    s.append("Absent")
                            else:
                                s.append('Shifted')
                s.append(str(s.count("Present")))
                s.append(str(s.count("Absent")))
                u.extend(s)
                s=u
                fl=0
                if ("Present" in s):
                    fl=1
                if ("Absent" in s):
                    fl=1
                print(fl)
                if fl==1:
                    with open(file, 'a') as f:
                        f.writelines("\n"+",".join(s))
                        f.close()
                else:
                    print(s)
                    continue
                    # messages.error(request,"Enter valid dates !")
                    # return redirect('index')

            dt=pd.read_csv(file)
            dt_list=list(dt.shape)
            if dt_list[0]<1:
                messages.error(request,"No one in hostel in those dates !")
                return redirect('index')
            dt=dt.sort_values('roomno')
            dt=dt.sort_values('hostelname')
            print(dt)
            # dt["index"] = 
            
            dt.insert(0,"index",[int(i) for i in range(1,len(dt)+1)])
            # if option=='view':
            #     table_content = dt.to_html(index=False)
            #     context = {'table_content': table_content}
            #     return  render(request, 'core/table.html', context)
            if option=='download':
                file_to_download = open(str(file), 'rb')
                response = FileResponse(file_to_download, content_type='application/force-download')
                response['Content-Disposition'] = 'inline; filename='+file
                return response
            table_content = dt.to_html(index=False)
            context = {'table_content': table_content,
                       'string':'FROM :' +fdate+'  || TO : '+tdate+' || hostel : '+hostel+' || hosteltype : '+hosteltype
                       }
            return  render(request, 'core/table.html', context)
        return redirect('index')
    except Exception as e:
        print(e)
        messages.error(request,'Something Wrong!!')
        return redirect('index')
    
@login_required
def hostelreport(request):
    day=request.GET['date']
    option=request.GET['option']
    if os.path.getsize("media/picklefiles/attendance.pickle") > 0:
        attendance=pickle.loads(open('media/picklefiles/attendance.pickle',"rb").read())
    else:
        attendance={}
    if day not in attendance:
        messages.error(request,"No hostel_report on that date!!")
        return redirect('index')
    att=attendance[str(day)]
    absent=att[0]
    present=att[1]
    att_db=att[2][0]
    hostellist_absent={'cvr':0,'vvk':0,'asr':0,'vsr':0,'dnr':0,'sac':0}
    hostellist_present={'cvr':0,'vvk':0,'asr':0,'vsr':0,'dnr':0,'sac':0}
    for i in absent:
        att_user=att_db[i]
        if att_user['hostelname'] in hostellist_absent.keys():
            hostellist_absent[att_user['hostelname']]+=1
    for j in present:
        att_user=att_db[j]
        if att_user['hostelname'] in hostellist_present.keys():
            hostellist_present[att_user['hostelname']]+=1
    df={}
        
    
    for h in hostellist_absent.keys():
        d={'Absent':hostellist_absent[h],'Present':hostellist_present[h]}
        df[h]=d
    df['total_hostel'] = {'Absent':len(att[0]),'Present':len(att[1])}
    dt = pd.DataFrame(df)
    dt=dt.T
    print(df)
    if option=='download':
        response = FileResponse(dt.to_csv(), content_type='application/force-download')
        response['Content-Disposition'] = 'inline; filename='+day+'_hostel report.csv'
        return response
    table_content = dt.to_html()
    context = {'table_content': table_content,
               'string':day
               }
    return  render(request, 'core/table.html', context)


def studentreport(request):
    print(123)
    fdate=request.GET.get("date1", "")
    tdate=request.GET.get("date2", "")
    date1=datetime.strptime(request.GET.get("date1", ""), "%Y-%m-%d").date()
    date2=datetime.strptime(request.GET.get("date2", ""), "%Y-%m-%d").date()
    phone=request.GET.get("phone","")
    option=request.GET["option"]
    if len(phone)<10 or len(phone)>10:
        messages.error(request,"Check phone Number!")
        return redirect('index')
    try:
        phone=int(phone)
        phone=str(phone)
    except:
        messages.error(request,"Check phone number!!")
        return redirect('index')
    if phone==None:
        return redirect('index')#####
    #pickle_attenance
    if os.path.getsize("media/picklefiles/attendance.pickle") > 0:
        attendance=pickle.loads(open('media/picklefiles/attendance.pickle',"rb").read())
    else:
        attendance={}
    
    delta = dta.timedelta(days=1)
    datelist=[]
    a={}
    A=0
    P=0
    H=0
    print(attendance)
    while (date1 <= date2):
        f=date1
        f=f.strftime("%Y-%m-%d")
        print( f in attendance.keys(),f)
        if f in attendance.keys():
            att=attendance[f]
            if int(phone) in att[0]:
                a[f]='Absent'
                A+=1
            elif int(phone) in att[1]:
                a[f]='Present'
                P+=1
        else:
            a[f]='holiday'
            H+=1
        date1 += delta
    a['total present days']=P
    a['total absent days']=A
    a["total holidays"]=H
    dt=pd.Series(a)
    df=dt.to_frame(name=str(phone)+"_report")
    print(df)
    if option=='download':
        response = FileResponse(df.to_csv(), content_type='application/force-download')
        response['Content-Disposition'] = 'inline; filename='+str(phone)+'_hostel report.csv'
        return response
    table_content = df.to_html()
    context = {'table_content': table_content,
               'string': 'FROM : '+fdate+' || TO : '+tdate+' || PHONE : '+str(phone)
               }
    return  render(request, 'core/table.html', context)
    