from django.shortcuts import render, HttpResponse
from django.template import loader
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from .models import Event
from EventOWeb.settings import BASE_DIR
import datetime

# Use a service account.
serviceAccount = os.path.join(BASE_DIR, 'FormApp/path/to/evento-9a40a-9940427641e4.json')
cred = credentials.Certificate(serviceAccount)

app = firebase_admin.initialize_app(cred)

db = firestore.client()

# Create your views here.

def index(request):
    return HttpResponse("Welcome to EventO")

def createForm(request):
    eventId = request.GET["eventid"]

    doc_ref = db.collection(u'Events').document(eventId)

    doc = doc_ref.get()

    name = "ABC"

    if doc.exists:
        data = doc.to_dict()
        event = Event(
            data["EventName"],
            data["Description"],
            data["StartTime"],
            data["FormName"],
            data["FormMobile"],
            data["FormEmail"],
            data["FormAddress"],
            data["Admin"],
        )
    
    strtdate = "On " + event.time.strftime("%d %B, %Y | %A ")
    strttime = "At " + event.time.strftime("%I : %M %p")

    context = {
        'Event_Name' : event.name,
        'Event_Desc' : event.desc,
        'Event_date' : strtdate,
        'Event_time' : strttime,
        'isName' : event.isName,
        'isPhone' : event.isNumber,
        'isEmail' : event.isEmail,
        'isAddress' : event.isAddress,
    }

    return render(request, "Form.html", context)
