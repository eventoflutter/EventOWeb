from django.shortcuts import render, HttpResponse
from django.template import loader
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import os
from .models import Event
from EventOWeb.settings import BASE_DIR

from GrabzIt import GrabzItImageOptions
from GrabzIt import GrabzItClient

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles import colormasks

import PIL

# Use a service account.
serviceAccount = os.path.join(BASE_DIR, 'FormApp/path/to/evento-9a40a-9940427641e4.json')
cred = credentials.Certificate(serviceAccount)

app = firebase_admin.initialize_app(cred, {'storageBucket': 'evento-9a40a.appspot.com'})

db = firestore.client()

# Create your views here.

def index(request):
    return HttpResponse("Welcome to EventO")

def createForm(request):
    eventId = request.GET["eventid"] 

    doc_ref = db.collection(u'Events').document(eventId)

    doc = doc_ref.get()

    if doc.exists:
        event = createEventObj(doc)
    
    strtdate = "On " + event.time.strftime("%d %B, %Y | %A ")
    strttime = "At " + event.time.strftime("%I : %M %p")

    context = {
        'eventid': eventId,
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

def createImage(request):

    eventId = request.POST['eventid']

    visitorRef = registerVisitor(request)

    print(BASE_DIR)

    makeQR(visitorRef)

    bucket = storage.bucket()

    qrcodefile = visitorRef + '.png' 

    blob = bucket.blob('QRCodes/' + qrcodefile)
 
    blob.upload_from_filename('static/' + qrcodefile)

    blob.make_public()

    grabzIt = GrabzItClient.GrabzItClient("NGZkN2U2ODU5OGU5NDI1MDkwY2Q5ZGU3Y2E4ZmFmNmQ=", "TVMcMj8/CDs/OBs/Pz8FPz9ROT8/Pz8/Pz8/Hz8zPz8=")

    options = GrabzItImageOptions.GrabzItImageOptions()
    options.hd = True
    options.targetElement = "#main-container"
    options.format = "png"

    url = "https://theevento.live/temp_1?eventid="+ eventId + "&visitorid=" + visitorRef

    grabzIt.URLToImage(url, options)
    grabzIt.SaveTo(os.path.join(BASE_DIR, 'static/finalCard.png'))


    return HttpResponse(render(request, "created.html", {"Dir" : blob.public_url})) 

def temp_1(request):

    eventid = request.GET['eventid']
    visitorid = request.GET['visitorid']

    event_ref = db.collection(u'Events').document(eventid)

    doc = event_ref.get()

    event = createEventObj(doc)

    qrcodeurl = "https://storage.googleapis.com/evento-9a40a.appspot.com/QRCodes/" + visitorid + ".png"

    context = {
        'eventid': eventid,
        'qrurl': qrcodeurl,
        'Event_Name' : event.name,
        'Event_Desc' : event.desc,
        'Event_date' : event.time.strftime("%d"),
        'Event_month' : event.time.strftime("%b"),
        'Event_day' : event.time.strftime("%A"),
        'Event_time' : "At " + event.time.strftime("%I : %M %p"),
        'invitedBy' : event.invitedBy,
        'address' : event.address,
        'scans' : event.scans,
    }

    return HttpResponse(render(request, "Passes/template_1.html", context))

def registerVisitor(request):
    eventId = request.POST['eventid']

    event_ref = db.collection(u'Events').document(eventId)

    event = event_ref.get().to_dict()

    newVisitor = event_ref.collection(u'Visitors').document()

    data = {
        'visitorId' : newVisitor.id,
    }

    if(event['IsQr']):
        data['Scans_rem'] = event['Scans']

    if(event['FormName'] == True):
        data['Name'] = request.POST['vname']

    if(event['FormEmail'] == True):
        data['Email'] = request.POST['email']

    if(event['FormMobile'] == True):
        data['Phone'] = request.POST['phone']

    if(event['FormAddress'] == True):
        data['Address'] = request.POST['address']

    newVisitor.set(data)

    return newVisitor.id

def makeQR(visitorId):

    qr= qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,border=1,)
    qr.add_data(visitorId)


    mask = colormasks.HorizontalGradiantColorMask(back_color=(255,255,255), left_color=(52, 148, 230), right_color=(236, 110, 173))

    img_1 = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer(), color_mask=mask)
    img_1.save(os.path.join('static/' + visitorId + '.png'))

def createEventObj(doc):
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
        data["InvitedBy"],
        data["Location"],
        data["Scans"],
    )

    return event
 