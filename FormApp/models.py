from django.db import models

# Create your models here.

class Event():
    def __init__(self, name, desc, time, isName, isNumber, isEmail, isAddress, admin, invitedBy, address, scans):
        self.name = name
        self.desc = desc
        self.time = time
        self.isName = isName
        self.isNumber = isNumber
        self.isEmail = isEmail
        self.isAddress = isAddress  
        self.admin = admin
        self.invitedBy = invitedBy
        self.address = address
        self.scans = scans

    
        
