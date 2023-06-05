from django.shortcuts import render, HttpResponse
from django.template import loader
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import os
from .models import Event
from EventOWeb.settings import BASE_DIR

from django.conf import settings
import requests

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

def csvPasses(request):
    eventId = request.GET['eventid']

    print(eventId)
    visitors = db.collection(u'Events').document(eventId).collection(u'Visitors').where("Category", "==", "CSV").get()

    for i in visitors:
        visitor = i.to_dict()

        id = i.id

        print(visitor["Name"])  

        # Generate QR code 
        makeQR(id)

        # # Upload QR code to firebase storage 
        blob = uploadQR(id)
    
        # # Take screenshot of the Card i.e. Generate the card
        takeScreenshot(eventId, id)

        # # Upload the Card to the firebase storage
        card = uploadCard(id)
 
        print("sc taken")

        sendMessageCSV(visitor, eventId, card) 

        os.remove(os.path.join(BASE_DIR, 'static/' + id + '.png')) 
        os.remove(os.path.join(BASE_DIR, 'static/' + id + 'Card.png'))

    return HttpResponse('{"Sent" : "Success"}')

def createImage(request):

    eventId = request.POST['eventid']
    visitorRef = registerVisitor(request)

    # # Generate QR code 
    makeQR(visitorRef)

    # # Upload QR code to firebase storage 
    blob = uploadQR(visitorRef)

    print("1")
 
    # # Take screenshot of the Card i.e. Generate the card
    takeScreenshot(eventId, visitorRef)

    print("2")
    # # # Upload the Card to the firebase storage
    card = uploadCard(visitorRef)

    SendMessageOnMessage(request, eventId, card)

    os.remove(os.path.join(BASE_DIR, 'static/' + visitorRef + '.png')) 
    os.remove(os.path.join(BASE_DIR, 'static/' + visitorRef + 'Card.png'))  

    return HttpResponse(render(request, "created.html")) 

def SendMessageOnMessage(request, eventId, card):
    event_ref = db.collection(u'Events').document(eventId)

    doc = event_ref.get()

    event = createEventObj(doc)

    name = request.POST['vname']

    phonenumber = "91" + request.POST['phone']

    headers = {"Authorization" : settings.WHATSAPP_TOKEN}
    
    payload ={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phonenumber,
                "type": "template",
                "template": {
                    "name": "template_for_pass_sending",
                    "language": {
                        "code": "en_US"
                    },
                    "components": [
                        {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                    "link": card.public_url
                                }
                            }
                        ]
                        },
                        {
                        "type": "body",
                        "parameters": [
                            {
                            "type": "text",
                            "text": name
                            },
                            {
                            "type": "text",
                            "text": event.name
                            }
                        ]
                        }
                    ]
                }
            }

    response = requests.post(settings.WHATSAPP_URL, headers=headers, json=payload)

    ans = response.json()

    print(ans) 

def sendMessageCSV(visitor, eventId, card):

    event_ref = db.collection(u'Events').document(eventId)

    doc = event_ref.get()

    event = createEventObj(doc)

    name = visitor["Name"]

    phonenumber = "91" + str(visitor["Number"])

    print(phonenumber)

    headers = {"Authorization" : settings.WHATSAPP_TOKEN}
    
    payload ={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phonenumber,
                "type": "template",
                "template": {
                    "name": "template_for_pass_sending",
                    "language": {
                        "code": "en_US"
                    },
                    "components": [
                        {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                    "link": card.public_url
                                }
                            }
                        ]
                        },
                        {
                        "type": "body",
                        "parameters": [
                            {
                            "type": "text",
                            "text": name
                            },
                            {
                            "type": "text",
                            "text": event.name
                            }
                        ]
                        }
                    ]
                }
            }

    print(phonenumber) 

    response = requests.post(settings.WHATSAPP_URL, headers=headers, json=payload)

    ans = response.json()

    print(ans) 

def uploadCard(visitorRef):
    bucket = storage.bucket()

    finalCard = visitorRef + 'Card.png' 

    blob = bucket.blob('Cards/' + finalCard)
 
    blob.upload_from_filename('static/' + finalCard)

    blob.make_public()
    return blob

def takeScreenshot(eventId, visitorRef):
    grabzIt = GrabzItClient.GrabzItClient("NjUyOTVmN2U2NzhjNDY2ZGI0MDg5YjQ3MmMzM2ZkZjE=", "Pz9UU1U/DFwLPz8/PzU/bj8/JChdP29ZNS9rPz9qPz8=")

    options = GrabzItImageOptions.GrabzItImageOptions()
    options.hd = True
    options.targetElement = "#main-container"
    options.format = "png"

    url = "https://theevento.live/temp_1?eventid="+ eventId + "&visitorid=" + visitorRef

    grabzIt.URLToImage(url, options)
    grabzIt.SaveTo(os.path.join(BASE_DIR, 'static/' + visitorRef + 'Card.png'))

def uploadQR(visitorRef):
    bucket = storage.bucket()

    qrcodefile = visitorRef + '.png' 

    blob = bucket.blob('QRCodes/' + qrcodefile)
 
    blob.upload_from_filename('static/' + qrcodefile)

    blob.make_public()

    return blob

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

    # mask = colormasks.HorizontalGradiantColorMask(back_color=(255,255,255), left_color=(52, 148, 230), right_color=(236, 110, 173))

    img_1 = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
    img_1.save(os.path.join(BASE_DIR, 'static/' + visitorId + '.png'))

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
