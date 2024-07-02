from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS
from flask_mail import Mail, Message
from pymongo.errors import InvalidOperation, DuplicateKeyError
import random
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
import os
from werkzeug.utils import secure_filename
import random
import string


app=Flask(__name__)
CORS(app)



app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your email server
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'pradeepgeddada31@gmail.com'  # Replace with your email address
app.config['MAIL_PASSWORD'] = 'dkjtxrfbelenaebn'  # Replace with your email password

mail = Mail(app)



client = MongoClient('mongodb+srv://geddadavenkatapradeep:Pradeep%402003@cluster0.5cddnmy.mongodb.net/?retryWrites=true&w=majority')
# mongodb+srv://geddadavenkatapradeep:<password>@cluster0.5cddnmy.mongodb.net/?retryWrites=true&w=majority

jgspdb = client.jgspdb

studentsdb = client.studentsdb


gs = jgspdb['guidesstudents']

pi = studentsdb["personalinfo"]

# count = 0
# gs_records = gs.find({})
# for i in gs_records:
#     if len(i["students"])>=20:
#         print(i["University EMAIL ID"])
#         count+=1
# print(gs_records)
# print(count)



# pradeeptempprofileinfo






jdb = client.jgspdb  # jgsp database
sdb = client.studentsdb  # students database

pi_collection = sdb.personalinfo
pe_collection = sdb.permissions

def copy_records():
    try:
        all_records = pi_collection.find()
        for record in all_records:
            new_record = {
                # "_id": record.get("_id"),
                "regNo": record.get("regNo", ""),
                "PermissionsForPersonalInfo": {
                    "EditPersonalDetail": True,
                    "EditParentDetail": True,
                    "EditAddress": True,
                    "EditAcademicDetail": True,
                }
            }
            print(new_record)
            pe_collection.insert_one(new_record)
    except Exception as e:
        print(f"An error occurred: {e}")
            
            # for student in record['students']:
    #             new_record = {
    #                 "guideName": record.get('NAME OF THE FACULTY', ''),
    #                 "guideMail": record.get('University EMAIL ID', ''),
    #                 "regNo": student.get('regNo', ''),
    #                 "personal_details": {
    #                     "name": student.get('name', ''),
    #                     "dep": student.get('dep', ''),
    #                     "section": student.get('section', ''),
    #                     "regNo": student.get('regNo', ''),
    #                     "religion": student.get('religion', ''),
    #                     "community": student.get('community', ''),
    #                     "lifeGoal": student.get('lifeGoal', ''),
    #                     "bloodGrp": student.get('bloodGrp', ''),
    #                     "languages": student.get('languages', []),
    #                 },
    #                 "parent_details": {
    #                     "fatherName": student.get('fatherName', ''),
    #                     "fatherMail": student.get('fatherMail', ''),
    #                     "fatherNo": student.get('fatherNo', ''),
    #                     "fatherOcc": student.get('fatherOcc', ''),
    #                     "motherName": student.get('motherName', ''),
    #                     "motherMail": student.get('motherMail', ''),
    #                     "motherNo": student.get('motherNo', ''),
    #                     "motherOcc": student.get('motherOcc', ''),
    #                     "guardianName": student.get('guardianName', ''),
    #                     "guardianMail": student.get('guardianMail', ''),
    #                     "guardianNo": student.get('guardianNo', ''),
    #                     "guardianOcc": student.get('guardianOcc', '')
    #                 },
    #                 "address": {
    #                     "permanentAdd": student.get('permanentAdd', ''),
    #                     "communicationAdd": student.get('communicationAdd', ''),
    #                     "phoneNo": student.get('phoneNo', ''),
    #                     "alterNo": student.get('alterNo', ''),
    #                     "hosteller": student.get('hosteller', False),
    #                     "hostelName": student.get('hostelName', ''),
    #                     "hostelNo": student.get('hostelNo', '')
    #                 },
    #                 "academic_details": {
    #                     "previousInst": student.get('previousInst', ''),
    #                     "tenthper": student.get('tenthper', ''),
    #                     "twelfthper": student.get('twelfthper', '')
    #                 }
    #             }
    #             pi_collection.insert_one(new_record)
    #             count += 1

# if _name_ == '_main_':
copy_records()  # Call the function directly to print records
# print(totalstu, ttalstaff)
