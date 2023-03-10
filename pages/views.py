from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.http import Http404
from datetime import datetime

# from .send_m import SendMSG


# Create your views here.
# C:\Users\ss\Desktop\school\project\
# ..\Scripts\activate
# python manage.py startapp
# python manage.py makemigrations
# python manage.py migrate
# python manage.py runserver
# python manage.py createsuperuser
# Anypassword2022

# اضافة
def index(request):
    delivery_point_model = apps.get_model('pages', 'delivery_point')
    user_message_model = apps.get_model('pages', 'user_message')

    delivery_points = delivery_point_model.objects.all()
    delivery_points_list = []
    for delivery_point in delivery_points:
        delivery_points_list.append([str(delivery_point.name),float(delivery_point.Lat),float(delivery_point.long)])

    print(delivery_points_list)

    if request.method == "POST":
        data = request.POST
        user_message_model.objects.create(name=data['name'],phone_num=data['phone_num'],email=data['email'],message=data['message'])
    x = {
        'delivery_points_list':delivery_points_list,
    }
    return render(request, 'pages/index.html',x)



@login_required(login_url='/login')
def add_donations(request):
    # SendMSG("05999","eid")
    delivery_point_model = apps.get_model('pages', 'delivery_point')
    item_model = apps.get_model('pages', 'item')
    item_desire_model = apps.get_model('pages', 'item_desire')
    donation_model = apps.get_model('pages', 'donation')
    message_model = apps.get_model('pages', 'message')
    receipt_model = apps.get_model('pages', 'receipt')
    registrar_model = apps.get_model('pages', 'registrar')
    beneficiary_model = apps.get_model('pages', 'beneficiary')
    item_demand_model = apps.get_model('pages', 'item_demand')
    
    loggined_delivery_point = delivery_point_model.objects.get(user= request.user)
    loggined_delivery_point_donations = donation_model.objects.filter(delivery_point_c = loggined_delivery_point)
    beneficiaries_phones = [["0"+str(beneficiary.phone_num.national_number),beneficiary.id] for beneficiary in  beneficiary_model.objects.all()]
    items = item_model.objects.all()

    empty = 0

    per_destance=-0.22
    per_time=0.33
    per_desire=1
    per_need_scale=1
    def chosen_beneficiary(donation):
        # step 1 : get all beneficiaries data
        my_l = [] # [b, all_sumed]
        for b in beneficiary_model.objects.all():
            # filtering beneficiaries due to donation type
            able = 0
            if donation.type == "clothes":
                if b.clothes_accept :
                    if donation.clothes_type == b.clothes_needed_type :
                        able = 1
            if donation.type == "study_supplies":
                if b.study_supplies_accept :
                    if donation.study_supplies_type == b.study_supplies_needed_type :
                        able = 1  
            if able:
                # get destance
                beneficiary_lat = b.Lat; beneficiary_long = b.long
                delivery_point_lat = donation.delivery_point_c.Lat; delivery_point_long = donation.delivery_point_c.long
                destance =((float(beneficiary_lat) - float(delivery_point_lat))**2+(float(beneficiary_long) - float(delivery_point_long))**2)**0.5
                # get desire
                desire = 5
                print("item_dddd",donation.item_c)
                if donation.item_c:
                    v = item_desire_model.objects.filter(item_c=donation.item_c, beneficiary_c=b).first()
                    print("desire_list",b.id,donation.item_c,v)
                    if v:
                        desire = v.desire_scale
                # get last_receiving_date
                last_receiving_date_days = 30
                r = receipt_model.objects.filter(beneficiary_id=b.id)
                if r:
                    last_receiving_date = r.latest('entry_date').entry_date        
                    date_format = "%Y-%m-%d %H:%M:%S"

                    now = datetime.strptime(str(datetime.today().strftime('%Y-%m-%d %H:%M:%S')), date_format)
                    last_receiving_date = datetime.strptime(str(last_receiving_date.strftime('%Y-%m-%d %H:%M:%S')), date_format)
                    last_receiving_date_days = (now - last_receiving_date).days
                # Multiply the data by its coefficient
                desire = desire * per_desire
                destance = destance * per_destance
                need_scale = b.need_scale * per_need_scale
                last_receiving_date = last_receiving_date_days * per_time
                # sum all
                all = desire + destance + need_scale + last_receiving_date
                # add all
                print('last_receiving_date_days',b.id,desire,destance,need_scale,last_receiving_date,all)

                if desire != 0:
                    my_l.append([b.id,all])
        print('bf_sord',my_l)
        # step 2 : sort the list  
        def takeSecond(elem):
            return elem[1]
        my_l.sort(key=takeSecond,reverse=True)
        print('af_sord',my_l)
        if my_l != []:
            print("higer_beneficiary_chosen_id",my_l[0],my_l[0])
        else :
            empty = 1

        # step 3 : return the higher beneficiary id 
        return  my_l[0][0]

        

        

            


            
                            

    def SendMSG(x,y):
        return True

    if request.method == "POST" and 'clothes' in request.POST:
        data = request.POST

        donation = donation_model.objects.create(
            delivery_point_c=loggined_delivery_point, type="clothes",pieces_number=data['pieces_number'], clothes_type=data["clothes_type"], img=data["img"],bio=data["bio"])
        if data['items'] != "0":
            donation.item_c = item_model.objects.get(id = data['items'])
            donation.save()


        beneficiary_chosen_id = chosen_beneficiary(donation)
        print("beneficiary_chosen_id",beneficiary_chosen_id)
        beneficiary = beneficiary_model.objects.get(id=beneficiary_chosen_id)

        send_message_done = SendMSG(beneficiary.phone_num, donation.delivery_point_c.name)
        if send_message_done:
            message = message_model.objects.create(done=True)
            receipt = receipt_model.objects.create(
                beneficiary=beneficiary, donation=donation, message_c=message)
            message.receipt_c = receipt
            message.save()
    elif request.method == "POST" and 'study' in request.POST:
        data = request.POST
        donation = donation_model.objects.create(
            delivery_point_c=loggined_delivery_point, type="study",pieces_number=data['pieces_number'], study_supplies_type=data["type"], img=data["img"],bio=data["bio"])
        if data['items'] != "0":
            donation.item = item_model.objects.get(id = data['items'])

        beneficiary_chosen_id = chosen_beneficiary(donation)
        beneficiary = beneficiary_model.objects.get(id=beneficiary_chosen_id)

        send_message_done = SendMSG(beneficiary.phone_num, donation.delivery_point_c.name)
        if send_message_done:
            message = message_model.objects.create(done=True)
            receipt = receipt_model.objects.create(
                beneficiary=beneficiary, donation=donation, message_c=message, by_ai=True)
            message.receipt_c = receipt
            message.save()

    if request.method == "POST" and 'recipient' in request.POST:
        data = request.POST
        donation = loggined_delivery_point_donations.get(id = data['recipient'])
        donation.recipient = True
        donation.save()

    if request.method == "POST" and 'item_desire' in request.POST:
        data = request.POST
        beneficiary = beneficiary_model.objects.get(id = data['beneficiary_id'])
        item = item_model.objects.get(id = data['item_desire'])
        item_desire_model.objects.create(item_c=item,beneficiary_c=beneficiary,desire_scale=data['desire'])

    if request.method == "POST" and 'item_demand' in request.POST:
        data = request.POST
        item_demand_model.objects.create(delivery_point_c= loggined_delivery_point,bio=data['bio'])

    print(beneficiaries_phones)
    x = {
        'delivery_point':loggined_delivery_point,
        'loggined_delivery_point_donations':loggined_delivery_point_donations,
        'beneficiaries_phones':beneficiaries_phones,
        'items':items,
        'empty':empty,
    }
    return render(request, 'pages/organization.html',x)





# Testpassword@2023
# test1@gmail.com
def login(request):

    worng_password = 0
    worng_email = 0
    email_value = None
    password_value = None

    if request.method == "POST":
        data = request.POST
        try:
            user = User.objects.get(email=data['email'])
            if user.check_password(data['password']):
                user_login = authenticate(
                    username=user.username, password=data['password'])
                auth_login(request, user_login)
                if 'next' in data :
                    return redirect(data['next'])
                else:
                    return redirect('pages:add_donations')

            else:
                worng_password = 1
                email_value = data['email']
                password_value = data['password']
        except User.DoesNotExist:
            worng_email = 1
            email_value = data['email']
            password_value = data['password']
    print(email_value)
    x = {
        'worng_email': worng_email,
        'worng_password': worng_password,
        'email_value': email_value,
        'password_value': password_value,
    }
    return render(request, 'pages/sign-in.html', x)

# clo =  desire : destance : need_scale : last_receiving_date
# max =     10  :    40    :   10       :  inf ~ 30
# nom =     5   :    40    :   5       :  inf ~ 30
# div =      1  :    4     :   2        :  inf ~ 3
# *   =      1  :    0.25  :   0.5      :  inf ~ 0.33