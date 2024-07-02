from datetime import datetime
from flask import Flask, render_template, request, jsonify,send_file
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
import driveAPI
import pandas as pd
from io import BytesIO
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
app=Flask(__name__)
CORS(app)



app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your email server
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'pradeepgeddada31@gmail.com'  # Replace with your email address
app.config['MAIL_PASSWORD'] = 'dkjtxrfbelenaebn'  # Replace with your email password
app.config['JWT_SECRET_KEY'] = 'hTaeMrRaKsHiThAsApNaIgOuThMsAsNkPrAdEeEp'  # Change this!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)  # Set token expiration time
jwt = JWTManager(app)
mail = Mail(app)



client = MongoClient('mongodb+srv://geddadavenkatapradeep:Pradeep%402003@cluster0.5cddnmy.mongodb.net/?retryWrites=true&w=majority')
# mongodb+srv://geddadavenkatapradeep:<password>@cluster0.5cddnmy.mongodb.net/?retryWrites=true&w=majority

db = client.jgspdb

CORS(app)


# Set the path for storing uploaded images
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']


# Use an absolute path to credentials.json
# credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

# creds = None
# if os.path.exists(credentials_path):
#     creds = Credentials.from_authorized_user_file(credentials_path)
    
    
def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Set up your own credentials file
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_to_google_drive(file_path, folder_id):
    drive_service = get_drive_service()
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id],
    }
    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    shareable_link = drive_service.files().get(fileId=file_id, fields='webViewLink').execute().get('webViewLink')
    return shareable_link



# collection = db.guidesstudents
# result = collection.update_many(
#     {},
#     {
#         "$push": {
#             "students": {"$each": []}  # Add an array of students (empty in this example)
#         }
#     }
# )
def generate_password():
    letters = string.ascii_letters
    numbers = string.digits
    special_characters = '!@#$%^&*()_+[]{}|;:,.<>?'
    password = random.choice(letters)  # Start with a random letter
    password += ''.join(random.choice(letters) for _ in range(5))
    password += random.choice(special_characters)
    password += ''.join(random.choice(numbers) for _ in range(4))
    return password


# collection1 = db.staffcredentials
# collection2 = db.allstaff
# for doc in collection2.find():
#     password = generate_password()
#     collection1.insert_one({"mailId" : doc['University EMAIL ID'], "password":password})
# collection=db.allstaff
# result = collection.update_many({}, {"$set": {"TOTAL BATCHES": 20}})

@app.route('/guidelist', methods=['GET'])
def get_Guide_List():
    collection = db.allstaff

    data = collection.find()  # Retrieve all documents from the collection

    result = []
    i=0  # Store the retrieved data
    for document in data:
        result.append({})
        result[i]["id"] = i+1
        result[i]["SL"] = document["SL"]["NO"]
        result[i]["NAME"] = document["NAME OF THE FACULTY"]
        result[i]["VACANCIES"] = document["TOTAL BATCHES"]
        result[i]["DESIGNATION"] = document["DESIGNATION"]
        result[i]["DOMAIN1"] = document["DOMAIN 1"]
        result[i]["DOMAIN2"] = document["DOMAIN 2"]
        result[i]["DOMAIN3"] = document["DOMAIN 3"]
        result[i]["UniversityEMAILID"] = document["University EMAIL ID"]
        result[i]['IMAGE'] = document["IMAGE"]
        result[i]['EMPID'] = document["EMP ID"]
        i+=1

    # print(result)
    return jsonify(result)



@app.route('/checkVacancies/<string:mail>', methods=['GET'])
def check_vacancies(mail):
    collection = db.allstaff
    filter = {'University EMAIL ID':mail}
    result = collection.find_one(filter)
    # print(result)
    return jsonify({"vacancies": result['TOTAL BATCHES']})


@app.route('/checkStudent/<string:mail>', methods=["GET"])
def checkStudentDuplicate(mail):
    collection = db.regstudents
    filter={'mailId':mail}
    result = collection.find_one(filter)
    # print(result)
    if result:
        return jsonify({"registered":True})
    else:
        return jsonify({"registered":False})
    

@app.route('/update_vacancies_data', methods=['PUT'])
def update_vacancies_data():
    data = request.json  # Assuming the request data is in JSON format
    # Extract data from the request JSON
    collection_name = data.get('collection_name')
    filter_data = data.get('filter_data')
    updated_data = data.get('updated_data')

    # print(filter_data, updated_data)

    # Update the data in the collection
    collection = db[collection_name]
    result = collection.update_one(filter_data, {'$set': updated_data})

    if result.modified_count > 0:
        return jsonify({"message": "Data updated successfully!"})
    else:
        return jsonify({"message": "No matching data found for update."}), 404



@app.route('/addNewStudent', methods=['PUT'])
def addNewStudent():
    data = request.json

    if 'messages' not in data:
        data['messages'] = []

    MailID = data["mailId"]
    password = f'{data["regNo"]}@{random.randint(1000,9999)}'


    collection = db.regstudents
    result = collection.insert_one(data)

    try:
        msg = Message(f'Mentor-Mentee-Selection-Portal',  # Email subject
                      sender='pradeepgeddada31@gmail.com',  # Replace with your email address
                      recipients=[MailID])  # Replace with the recipient's email address
        msg.html = f"""
        <html>
        <body>
            <p>Dear Student,</p>
            <p>You are successfully registered in Mentor-Mentor-Selection-Portal.</p>
            <p>Here are your login credentials:</p><br/>
            <ul>
            <li>User Mail ID: {data["mailId"]}</li>
            <li>Password: {password}</li>
            </ul><br/>
            <p>You can access the Mentor-Mentee-Selection-Portal with these credentials. Please don't share your credentials with anyone.</p><br/><br/><br/>
            <p>With Warm Regards,</p>
            <p>School of Computing,</p>
            <p>Sathyabama Institute of Science & Technology</p>
        </body>
        </html>
        """

        mail.send(msg)


        studentcredCollection = db.studentcredentials
        user={
            "MailID":MailID,
            "Password": password 
        }
        studentcredCollection.insert_one(user)
        # return jsonify({"message":"SENT", "OTP":otp})
    except Exception as e:
        print(e)
        return jsonify({"message":"NOT SENT"})

    




    if result:
        return jsonify({"status":"Added new Student"})
    else:
        return jsonify({"status":"Unable to add new student"})
    
@app.route('/updateGuidesStudentsData', methods=['PUT'])
def update_guides_students_data():
    collection = db.guidesstudents

    image = request.files.get('image')
    reg_no = request.form.get('regNo')
    mail_id = request.form.get('mailId')
    phone_no = request.form.get('phoneNo')
    name = request.form.get('name')
    guide_mail_id = request.form.get('GuideMailId')
    address = request.form.get("address")
    section = request.form.get("section")

    # Filter to find the document by GuideMailId
    filter_query = {"University EMAIL ID": guide_mail_id}

    # Save the image as a file on the server
    # Save the image as a file on the server
    if image:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image.filename))

        # Ensure the directory exists before saving the file
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        image.save(filename)

        try:
            # Upload the image to Google Drive and get the shareable link
            # folder_id = '1O3r9kS2dLr8D_tfJUF5fWX7dY0vB-wES'  # Replace with your actual Google Drive folder ID
            folder_id = '1uDPvi-PHyNtFDoDZZQDO0L8wMNGAZPea'  # Replace with your actual Google Drive folder ID
            google_drive_link = upload_to_google_drive(filename, folder_id)

            # Update the document by adding student_data to the students array
            update_query = {
                "$push": {
                    "students": {
                        "image": google_drive_link,
                        "regNo": reg_no,
                        "mailId": mail_id,
                        "phoneNo": phone_no,
                        "name": name,
                        "address": address,
                        "section": section
                    }
                }
            }

            # Use update_one to update the document based on the filter
            result = collection.update_one(filter_query, update_query)

            collection = db.regstudents
            filter = {"mailId":mail_id}
            res = collection.update_one(filter, {'$set': {"image":google_drive_link}})

            if result.modified_count > 0:
                # Delete the local image file after successful upload to Google Drive
                os.remove(filename)
                return jsonify({"message": "Updated Guides Students Data Successfully"})
            else:
                return jsonify({"error": "No document found for the given GuideMailId"}), 404

            



        except Exception as e:
            print(str(e))
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Image not provided"}), 400




@app.route('/stafflogin/<string:mailid>', methods=['POST'])
def staffLogin(mailid):
    collection = db.staffcredentials
    data = request.json
    print(data)
    filter = {"mailId": mailid}
    result = collection.find_one(filter)
    print(result)
    if result:
        if result['password'] == data['password']:
            access_token = create_access_token(identity=mailid)
            print('token broo --- ',access_token)
            return jsonify({"message": "Valid Credentials", "access_token": access_token})
        else:
            return jsonify({"message": "Invalid Credentials"})
    else:
        return jsonify({"message": "Account not found!"})
    

@app.route('/studentlogin/<string:mailid>', methods=['POST'])
def studnetLogin(mailid):
    collection = db.studentcredentials
    data = request.json
    print(data)
    filter = {"MailID":mailid}
    result = collection.find_one(filter)
    print(result)
    if result:
        if result['Password']==data['password']:
            print("----")
            access_token_student = create_access_token(identity=mailid)
            print("----" ,access_token_student)
            return jsonify({"message" : "Valid Credentials","access_token_student":access_token_student})
        else:
            return jsonify({"message" : "Invalid Credentials"})
    else:
        return jsonify({"message" : "Account not found!"})
    
@app.route('/getStudentData', methods=["POST"])
@jwt_required()
def getStudentData():
    data = request.json
    print(data)

    if data["mailId"]:
        studentCollection = db.regstudents
        studentDetails = studentCollection.find_one({"mailId":data["mailId"]})

        data = {
            "name":studentDetails["name"],
            "regNo":studentDetails["regNo"],
            "phoneNo":studentDetails["phoneNo"],
            "MentorName":studentDetails["selectedGuide"],
            "section":studentDetails["section"],
            "image":studentDetails["image"]
        }
        if studentDetails["messages"]:
            LatestMessage= studentDetails["messages"][-1]
        else:
            LatestMessage = None
        OldMessages=studentDetails["messages"][-2::-1]
        

        return jsonify({"message":"SUCCESS", "StudentData":data, "LatestMessage":LatestMessage, "OldMessages":OldMessages})

    else:

        return jsonify({"message":"Something went wrong."})




@app.route("/getGuideData", methods=["POST"])
@jwt_required()
def getGuideData():
    current_user = get_jwt_identity()
    data = request.json
    filter = {"University EMAIL ID": data['GuideMailId']}
    result = {}
    collection = db.allstaff
    result1 = collection.find_one(filter)
    
    collection = db.guidesstudents
    result2 = collection.find_one(filter)
    result["id"] = 1
    result["NAME"] = result1["NAME OF THE FACULTY"]
    result["VACANCIES"] = result1["TOTAL BATCHES"]
    result["DESIGNATION"] = result1["DESIGNATION"]
    result["DOMAIN1"] = result1["DOMAIN 1"]
    result["DOMAIN2"] = result1["DOMAIN 2"]
    result["DOMAIN3"] = result1["DOMAIN 3"]
    result["UniversityEMAILID"] = result1["University EMAIL ID"]
    result['IMAGE'] = result1["IMAGE"]
    result['EMPID'] = result1["EMP ID"]

    return jsonify({"GuideDetails": result, "AllStudents": result2['students']})




@app.route('/checkMail/<string:mailid>', methods=['GET'])
def Send_otp(mailid):
    # Get the update data from the request
    # data = request.get_json()

    otp = random.randint(100000,999999)

    try:
        msg = Message(f'Your OTP is {otp}',  # Email subject
                      sender='pradeepgeddada31@gmail.com',  # Replace with your email address
                      recipients=[mailid])  # Replace with the recipient's email address
        msg.body = 'This is a test email sent from Flask-Mail'  # Email body

        mail.send(msg)
        return jsonify({"message":"SENT", "OTP":otp})
    except Exception as e:
        print(e)
        return jsonify({"message":"NOT SENT"})
   
    
@app.route("/sendMessage/<mailId>", methods=["POST"])
def sendMessage(mailId):
    sdb = client.studentsdb  # Connect to the database
    collection = sdb.DupMessages
    print(mailId)
    try:
        data = request.json
        if not data or "message" not in data or "date" not in data:
            return jsonify({"error": "Invalid message data format"}), 400
        print(data)
        # Extract the date and time
        date_str = data["date"]
        print(date_str)
        time_str = datetime.now().strftime('%H:%M:%S')
        print(time_str)
        # Prepare message data
        message = data["message"]
        print("hello")
        # Define the filter and update queries
        filter_query = {"mailId": mailId}
        update_query = {
            "$set": {f"messages.{date_str}.{time_str}": message}
        }
        
        # Update the document in MongoDB
        result = collection.update_one(filter_query, update_query, upsert=True)

        if result.modified_count > 0 or result.upserted_id:
            return jsonify({"message": "SENT"})
        else:
            return jsonify({"message": "NOT SENT"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sendParentMessage/<mailId>", methods=["POST"])
def sendParentMessage(mailId):
    sdb = client.studentsdb  # Connect to the database
    collection = sdb.DupParentMessages
    print(mailId)
    try:
        data = request.json
        if not data or "message" not in data or "date" not in data:
            return jsonify({"error": "Invalid message data format"}), 400
        
        # Extract the date and time
        date_str = data["date"]
        time_str = datetime.now().strftime('%H:%M:%S')
        
        # Prepare message data
        Parentmessages = data["message"]
        
        # Define the filter and update queries
        filter_query = {"mailId": mailId}
        update_query = {
            "$set": {f"Parentmessages.{date_str}.{time_str}": Parentmessages}
        }
        
        # Update the document in MongoDB
        result = collection.update_one(filter_query, update_query, upsert=True)

        if result.modified_count > 0 or result.upserted_id:
            return jsonify({"message": "SENT"})
        else:
            return jsonify({"message": "NOT SENT"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/sendMessageToAll", methods=["POST"])
def sendMessageToAll():

    data = request.json



    collection = db.regstudents
    # filter_query = {"mailId":mailid}
    update_query = {
        "$push" : {
            "messages" : {
                data['date'] : data["message"]
            }
        }
    }
    # result = collection.update_one(filter_query, update_query)

    for doc in data['mailIds']:
        print(doc["mailId"])
        filter_query = {"mailId":doc["mailId"]}
        result = collection.update_one(filter_query, update_query)
        



    print(data)


    if result.modified_count > 0:
        return jsonify({"message": "SENT"})
    else:
        return jsonify({"message":"NOT SENT"})

# @app.route("/getStudentProfileData", methods=["POST"])
# def getStudentProfileData():
#     data = request.json
#     print(data)

#     filter = {"University EMAIL ID": data['guideMail']}

#     result = {}

#     collection = db.guidesstudents
#     result2 = collection.find_one(filter)

#     for doc in result2['students']:
#         if int(doc['regNo'])==int(data['regNo']):
#             print(doc)
#             return jsonify({"StudentData":doc})
            
        
#     return jsonify({"message": "Success"})


def authenticate():
    creds = None
    token_file = 'token.json'

    # The file token.json stores the user's access and refresh tokens and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/drive']
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return creds 



















# 23-4-2024 merged code form rakshitha

@app.route("/events",methods=["POST"])
def events():
    data = request.json
    regNo =  data["regNo"]
    db = client.studentsdb
    collection = db.events

    filter = {"regNo":regNo}
    eventsData = list(collection.find(filter))
    

    events_conducted = {}

    events_attended  = {}

    for doc in eventsData:
        for i in range(1,9):
            semester = f'semester{i}'
            events_conducted[semester] = []
            for ev in doc["events_conducted"][semester]:
                dic = {}
                dic["eventName"] = ev["eventName"]
                dic["eventType"] = ev["eventType"]
                dic["eventSummary"] = ev["eventSummary"]
                dic["bfileURL"] = ev["Brouchure"]["bfileURL"]
                dic["bfileName"] = ev["Brouchure"]["bfileName"]
                dic["brouchureURL"] = ev["Brouchure"]["brouchureURL"]
                dic["fileURL"] = ev["certificate"]["fileURL"]
                dic["fileName"] = ev["certificate"]["fileName"]
                dic["certificateURL"] = ev["certificate"]["certificateURL"]
                events_conducted[semester].append(dic)
    for doc in eventsData:
        for i in range(1,9):
            semester = f'semester{i}'
            events_attended[semester] = []
            for evatt in doc["events_attended"][semester]:
                dic = {}
                dic["eventName"] = evatt["eventName"]
                dic["eventType"] = evatt["eventType"]
                dic["eventSummary"] = evatt["eventSummary"]
                dic["bfileURL"] = evatt["Brouchure"]["bfileURL"]
                dic["bfileName"] = evatt["Brouchure"]["bfileName"]
                dic["brouchureURL"] = evatt["Brouchure"]["brouchureURL"]
                dic["fileURL"] = evatt["certificate"]["fileURL"]
                dic["fileName"] = evatt["certificate"]["fileName"]
                dic["certificateURL"] = evatt["certificate"]["certificateURL"]
                events_attended[semester].append(dic)


    return jsonify({"message": "Success","eventsconducted":events_conducted,"eventsattended":events_attended})



@app.route("/eventsData", methods=["POST"])
def events_data():
    data = request.json
    regNo = data["regNo"]  # Corrected to use "regNo"
    db = client.studentsdb
    collection = db.events
    print(regNo)
    filter = {"regNo": regNo}
    eventsData = list(collection.find(filter))

    events_conducted = {}
    events_attended = {}

    for doc in eventsData:
        for i in range(1, 9):
            semester = f'semester{i}'
            events_conducted[semester] = []
            if doc["events_conducted"].get(semester, 0)==0:
                continue
            for ev in doc["events_conducted"][semester]:
                dic = {
                    "eventName": ev["eventName"],
                    "eventType": ev["eventType"],
                    "eventSummary": ev["eventSummary"],
                    "bfileURL": ev["Brouchure"]["bfileURL"],
                    "bfileName": ev["Brouchure"]["bfileName"],
                    "brouchureURL": ev["Brouchure"]["brouchureURL"],
                    "fileURL": ev["certificate"]["fileURL"],
                    "fileName": ev["certificate"]["fileName"],
                    "certificateURL": ev["certificate"]["certificateURL"]
                }
                events_conducted[semester].append(dic)
    print('events_conducted -- - ',events_conducted)
    for doc in eventsData:
        for i in range(1, 9):
            semester = f'semester{i}'
            events_attended[semester] = []
            if doc["events_attended"].get(semester, 0)==0:
                continue
            for evatt in doc["events_attended"][semester]:
                dic = {
                    "eventName": evatt["eventName"],
                    "eventType": evatt["eventType"],
                    "eventSummary": evatt["eventSummary"],
                    "bfileURL": evatt["Brouchure"]["bfileURL"],
                    "bfileName": evatt["Brouchure"]["bfileName"],
                    "brouchureURL": evatt["Brouchure"]["brouchureURL"],
                    "fileURL": evatt["certificate"]["fileURL"],
                    "fileName": evatt["certificate"]["fileName"],
                    "certificateURL": evatt["certificate"]["certificateURL"]
                }
                events_attended[semester].append(dic)
    print('events_attented -- - ',events_attended)
    return jsonify({"message": "Success", "eventsconducted": events_conducted, "eventsattended": events_attended})

# @app.route("/personalDetail", methods=["GET","POST"])
# def get_personal_details():
#     data = request.json
#     regNo = data["regNo"]
#     details = data["collection"]
#     db = client.studentsdb
#     collection = db.personalinfo
#     filter = {"regNo": regNo}

#     detailsData = list(collection.find(filter))
#     personal_details = []
#     parent_details = []
#     address = []
#     academic_details = []

#     for doc in detailsData:
#         # Accessing personal_details
#         if "personal_details" in doc:
#             pdet = doc["personal_details"]
#             dic = {}
#             dic["name"] = pdet.get("name", "")
#             dic["dep"] = pdet.get("dep", "")
#             dic["section"] = pdet.get("section", "")
#             dic["regNo"] = pdet.get("regNo", "")
#             dic["religion"] = pdet.get("religion", "")
#             dic["community"] = pdet.get("community", "")
#             dic["lifeGoal"] = pdet.get("lifeGoal", "")
#             dic["bloodGrp"] = pdet.get("bloodGrp", "")
#             dic["languages"] = pdet.get("languages", [])
#             personal_details.append(dic)

#         # Accessing parent_details
#         if "parent_details" in doc:
#             pdet = doc["parent_details"]
#             dic = {}
#             dic["fatherName"] = pdet.get("fatherName", "")
#             dic["fatherMail"] = pdet.get("fatherMail", "")
#             dic["fatherOcc"] = pdet.get("fatherOcc", "")
#             dic["fatherNo"] = pdet.get("fatherNo", "")
#             dic["motherName"] = pdet.get("motherName", "")
#             dic["motherMail"] = pdet.get("motherMail", "")
#             dic["motherOcc"] = pdet.get("motherOcc", "")
#             dic["motherNo"] = pdet.get("motherNo", "")
#             dic["guardianName"] = pdet.get("guardianName", "")
#             dic["guardianMail"] = pdet.get("guardianMail", "")
#             dic["guardianOcc"] = pdet.get("guardianOcc", "")
#             dic["guardianNo"] = pdet.get("guardianNo", "")
#             parent_details.append(dic)

#         # Accessing address
#         if "address" in doc:
#             pdet = doc["address"]
#             dic = {}
#             dic["permanentAdd"] = pdet.get("permanentAdd", "")
#             dic["communicationAdd"] = pdet.get("communicationAdd", "")
#             dic["phoneNo"] = pdet.get("phoneNo", "")
#             dic["alterNo"] = pdet.get("alterNo", "")
#             if "hosteller" in pdet and pdet["hosteller"]:
#                 dic["hostelName"] = pdet.get("hostelName", "")
#                 dic["hostelNo"] = pdet.get("hostelNo", "")
#             address.append(dic)

#         # Accessing academic_details
#         if "academic_details" in doc:
#             pdet = doc["academic_details"]
#             dic = {}
#             dic["previousInst"] = pdet.get("previousInst", "")
#             dic["tenthper"] = pdet.get("tenthper", "")
#             dic["twelfthper"] = pdet.get("twelfthper", "")
#             academic_details.append(dic)

#     return jsonify({"personaldetails": personal_details, "parentdetails": parent_details, "address": address, "academicdetails": academic_details})





@app.route("/additionalCredDetail", methods=["POST"])
def additionalCredDetail():
    data = request.json
    regNo = data["regNo"]
    additionCred = data["collection"]
    db = client.studentsdb
    collection = db.additionalCred

    curricular_details = {}
    cocurricular_details = {}
    extra_details = []
    achievements_details = []
    filter = {"regNo": regNo}

    additionCredData = list(collection.find(filter))

    for doc in additionCredData:
        for i in range(1, 9):
            semester = f'semester{i}'
            curricular_details[semester] = []
            for act in doc["curricular"][semester]:
                dic = {}
                dic["activityName"] = act["activityName"]
                dic["activityType"] = act["activityType"]
                dic["ifOther"] = act["ifOther"]
                dic["bfileName"] = act["brouchure"]["bfileName"]
                dic["fileName"] = act["Report"]["fileName"]
                curricular_details[semester].append(dic)

    for doc in additionCredData:
        for i in range(1, 9):
            semester = f'semester{i}'
            cocurricular_details[semester] = []
            for act in doc["coCurricular"][semester]:
                dic = {}
                dic["activityName"] = act["activityName"]
                dic["activityType"] = act["activityType"]
                dic["ifOther"] = act["ifOther"]
                dic["bfileName"] = act["brouchure"]["bfileName"]
                dic["fileName"] = act["Report"]["fileName"]
                cocurricular_details[semester].append(dic)

    for doc in additionCredData:
        for event in doc["extraCredits"]:
            dic = {}
            dic["sNo"] = event["sNo"]
            dic["orgName"] = event["orgName"]
            dic["courseName"] = event["courseName"]
            dic["year"] = event["year"]
            dic["duration"] = event["duration"]
            dic["fileName"] = event["certificate"]["fileName"]
            extra_details.append(dic)

    for doc in additionCredData:
        for ach in doc["achievements"]:
            dic = {}
            dic["typeOfAch"] = ach["typeOfAch"]
            dic["description"] = ach["description"]
            achievements_details.append(dic)


    return jsonify({"message": "Success", "curricular": curricular_details, "cocurricular": cocurricular_details, "extracredits": extra_details, "achievements": achievements_details})



@app.route("/resultDetail", methods = ["POST"])
def resultDetail():
    data = request.json
    print("Dataxx  -  ",data)
    regNo =  data.get("regNo",0)
    # result = data["collection"]
    db = client.studentsdb
    collection = db.results
    filter = {"regNo":str(regNo)}
    print(filter)

    results_details = []
    
    resultData = list(collection.find(filter))
    print("ResultData - ", resultData)

    for doc in resultData:
            dic = {}
            dic["Semester 1"]= doc.get("Semester 1","")
            dic["Semester 2"]= doc.get("Semester 2","")
            dic["Semester 3"]= doc.get("Semester 3","")
            dic["Semester 4"]= doc.get("Semester 4","")
            dic["Semester 5"]= doc.get("Semester 5","")
            dic["Semester 6"]= doc.get("Semester 6","")
            dic["Semester 7"]= doc.get("Semester 7","")
            dic["Semester 8"]= doc.get("Semester 8","")
            results_details.append(dic)
    return ({"results":results_details})

# @app.route("/insert_meeting", methods=["POST"])
# def insert_meeting():
#     data = request.json
#     regNo = data["regNo"]
#     mentor = data["Meeting"]
#     db = client.studentsdb
#     collection = db.MentorMeeting

#     document = {
#         "regNo": regNo,
#         "Meeting": mentor
#     }

#     try:
#         result = collection.insert_one(document)
#         inserted_id = str(result.inserted_id)
#         return jsonify({"message": "meeting data inserted successfully", "inserted_id": inserted_id}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400
    

# @app.route("/insert_remarks", methods=["POST"])
# def insert_remarks():
#     data = request.json
#     regNo = data["regNo"]
#     remarks = data["remarksInfo"]
#     db = client.studentsdb
#     collection = db.remarks

#     document = {
#         "regNo": regNo,
#         "remarksInfo": remarks
#     }

#     try:
#         result = collection.insert_one(document)
#         inserted_id = str(result.inserted_id)
#         return jsonify({"message": "Remarks data inserted successfully", "inserted_id": inserted_id}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400


@app.route("/permissionDetail", methods = ["POST"])
def permissionDetail():
    data = request.json
    regNo = int(data["regNo"])
    # result = data["collection"]
    db = client.studentsdb
    collection = db.permissions
    filter = {"regNo":regNo}

    permission_details = []
    
    permissionData = list(collection.find(filter))
    print(permissionData)

    doc = permissionData[0]["PermissionsForPersonalInfo"]
    dic = {}
    dic["personalinfo"]= doc["EditPersonalDetail"]
    dic["parentinfo"]= doc["EditParentDetail"]
    dic["accademicinfo"]= doc["EditAddress"]
    dic["addressinfo"]= doc["EditAcademicDetail"]
    permission_details.append(dic)
    return ({"permission":permission_details})


@app.route("/updatePermission", methods=["POST"])
def updatePermission():
    data = request.json
    regNo = int(data["regNo"])
    permissionType = data["permissionType"]
    newValue = data["newValue"]

    db = client.studentsdb
    collection = db.permissions
    filter = {"regNo": regNo}

    

    # Map the permissionType to the corresponding field in the document
    permissionFieldMap = {
        "personalinfo": "PermissionsForPersonalInfo.EditPersonalDetail",
        "parentinfo": "PermissionsForPersonalInfo.EditParentDetail",
        "accademicinfo": "PermissionsForPersonalInfo.EditAddress",
        "addressinfo": "PermissionsForPersonalInfo.EditAcademicDetail"
    }

    # Get the corresponding field path in the document
    fieldPath = permissionFieldMap.get(permissionType)

    if fieldPath:
        # Use the $set operator to update the specific field
        update = {"$set": {fieldPath: newValue}}
        result = collection.update_one(filter, update)

        if result.modified_count > 0:
            return {"message": "Permission updated successfully"}, 200
        else:
            return {"message": "No document found or permission already set to the same value"}, 404
    else:
        return {"message": "Invalid permission type"}, 400









# NEW ROUTES BY PRADEEP

@app.route("/studentDashboard/studentPersonalInfoPage/getPermissionData", methods=["POST"])
def getPermissionData():
    data = request.json
    regNo = int(data["regNo"])

    db = client["studentsdb"]
    PermissionInfoCollection = db["permissions"]
    permissionData = PermissionInfoCollection.find({"regNo":regNo})
    print(permissionData[0])
    return jsonify({"message":"success", "permissions":permissionData[0]["PermissionsForPersonalInfo"]})



# Google Drive API credentials
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'Credentials.json'

# Set the path for storing uploaded images
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

upload_dir = os.path.join(app.root_path, UPLOAD_FOLDER)
os.makedirs(upload_dir, exist_ok=True)


# Specify the folder ID where you want to upload the file
FOLDER_ID = '11aTPM9aw5aRfBEl3xkZnUPjE3-UjvTYQ'
@app.route("/student/insertSemResult", methods=["POST"])
def insert_sem_result():
    db = client.studentsdb
    result_collection = db.results
    try:
        data = request.json
        print(data)
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']
        regNo = request.form.get('regNo')
        print("regNo - ",regNo)
        semester = request.form.get('semester')
        name = request.form.get('name')
        print("semester - ",semester)

        if file.filename == '':
            return jsonify({"error": "No file selected for uploading"}), 400

        # if not regNo or not semester:
        #     return jsonify({"error": "Registration number and semester are required"}), 400

        # Save file to temporary location
        file_path = os.path.join(upload_dir, secure_filename(file.filename))
        file.save(file_path)

        try:
            # Upload file to Google Drive
            file_id = driveAPI.upload_file_to_drive(file_path, f'{regNo}-{name}-{semester}', FOLDER_ID, SCOPES, SERVICE_ACCOUNT_FILE)
            file_link = f'https://drive.google.com/file/d/{file_id}'
            print(file_id)
            print(file_link)

            # Update MongoDB with file link, semester number, and registration number
            # results_collection = db.results
            # regNo = '4111104';
        
            result_collection.update_one(
                {"regNo": regNo},
                {"$set": {f'{semester}': file_link}},
                upsert=True
            )

            return jsonify({"success": True, "fileLink": file_link}), 200
        except Exception as e:
            print(e)
            # traceback.print_exc()  # Print traceback for detailed error analysis
            return jsonify({"error": str(e)}), 500
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)

    except Exception as e:
        print(e)
        # traceback.print_exc()  # Print traceback for detailed error analysis
        return jsonify({"error": str(e)}), 500

@app.route('/StudentMenuPage/getLeftSideBarData', methods=["POST"])
@jwt_required()
def getLeftSideBarData():
    data = request.json
    print("Data - ",data)
    
    # Check if 'mailId' is present in the request data
    if "mailId" in data:
        mailId = data["mailId"]  # Extract mailId from request data
        filter = {"mailId": mailId}
        print(f"Filter used for query: {filter}")

        studentCollection = db.regstudents
        studentDetails = studentCollection.find_one(filter)

        if studentDetails:
            student_data = {
                "name": studentDetails.get("name", ""),
                "regNo": studentDetails.get("regNo", ""),
                "phoneNo": studentDetails.get("phoneNo", ""),
                "mailId": studentDetails.get("mailId", ""),
                "MentorName": studentDetails.get("selectedGuide", ""),
                "section": studentDetails.get("section", ""),
                "image": studentDetails.get("image", "")
            }

            # Get latest message if messages exist
            latest_message = studentDetails["messages"][-1] if studentDetails.get("messages") else None
            # Get old messages in reverse order, excluding the last one (latest)
            old_messages = studentDetails["messages"][-2::-1] if studentDetails.get("messages") else []

            return jsonify({
                "message": "SUCCESS",
                "StudentData": student_data,
                "LatestMessage": latest_message,
                "OldMessages": old_messages
            })
        else:
            return jsonify({"message": "Student not found."})
    else:
        return jsonify({"message": "mailId not provided in the request."})



@app.route("/get_remarks/<string:reg_no>", methods=["GET"])
def get_remarks(reg_no):
    print("Fetching remarks for Register Number:", reg_no)  # Additional debug output
    
    # Ensure correct database and collection
    db = client.studentsdb
    remarks_collection = db.remarks
    
    try:
        # Find the document with the given registration number
        document = remarks_collection.find_one({"regNo": str(reg_no)}, {"_id": 0, "remarksInfo": 1})
        
        if not document:  # Check if no document found
            print("No remarks found for Register Number:", reg_no)  # Debugging output
            return jsonify({"message": "No remarks found for this registration number"}), 404
        
        # Extract remarksInfo
        remarks_info = document.get("remarksInfo", [])
        
        return jsonify({
            "regNo": reg_no,
            "remarksInfo": remarks_info
        }), 200

    except Exception as e:
        print("Error fetching remarks:", e)  # Error output
        return jsonify({"error": str(e)}), 500


@app.route("/insert_remarks", methods=["POST"])
def insert_remarks():
    data = request.json
    regNo = data["regNo"]
    new_remark = data["remarksInfo"][0]
    db = client.studentsdb
    collection = db.remarks

    try:
        # Find the document by regNo
        document = collection.find_one({"regNo": regNo})

        if document:
            # If the document exists, append the new remark to the existing remarksInfo array
            collection.update_one(
                {"regNo": regNo},
                {"$push": {"remarksInfo": new_remark}}
            )
            message = "Remarks data updated successfully"
        else:
            # If the document does not exist, create a new document
            new_document = {
                "regNo": regNo,
                "remarksInfo": [new_remark]
            }
            result = collection.insert_one(new_document)
            message = "Remarks data inserted successfully"
            inserted_id = str(result.inserted_id)

        return jsonify({"message": message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# get the meeetings
@app.route("/get_meetings/<string:reg_no>", methods=["GET"])
def get_meetings_by_reg_no(reg_no):
    db = client.studentsdb
    collection = db.MentorMeeting
    try:
        # Query the collection for the document with the matching regNo
        meeting_data = collection.find_one({"regNo": str(reg_no)})

        if meeting_data:
            print("meetings:",meeting_data)
            return jsonify({"meetings": meeting_data.get("meetings", [])}), 200
        else:
            return jsonify({"message": "No meetings found for the given registration number"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/insert_meeting", methods=["POST"])
def insert_meeting():
    data = request.json
    regNo = data["regNo"]
    new_meeting = data["Meeting"]
    db = client.studentsdb
    collection = db.MentorMeeting

    try:
        # Find the document by regNo
        document = collection.find_one({"regNo": regNo})

        if document:
            # If the document exists, append the new meeting to the existing meetings array
            collection.update_one(
                {"regNo": regNo},
                {"$push": {"meetings": new_meeting}}
            )
            message = "Meeting data updated successfully"
        else:
            # If the document does not exist, create a new document
            new_document = {
                "regNo": regNo,
                "meetings": [new_meeting]
            }
            result = collection.insert_one(new_document)
            message = "Meeting data inserted successfully"
            inserted_id = str(result.inserted_id)

        return jsonify({"message": message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
@app.route('/getMessages', methods=['POST'])
def get_messages():
    data = request.json
    mail_id = data.get('mailId')
    db = client.studentsdb 
    collection = db.DupMessages
    student_data = collection.find_one({'mailId': mail_id})

    if student_data:
        messages = []
        for date, times in student_data.get('messages', {}).items():
            for time, message in times.items():
                messages.append({
                    'date': date,
                    'time': time,
                    'message': message
                })

        return jsonify({'messages': messages})
    else:
        return jsonify({'messages': []}), 404
    


@app.route('/getParentMessages', methods=['POST'])
def getParentmessages():
    data = request.json
    mail_id = data.get('mailId')
    db = client.studentsdb 
  
    collection = db.DupParentMessages
    student_data = collection.find_one({'mailId': mail_id})

    if student_data:
        Parentmessages = []
        for date, times in student_data.get('Parentmessages', {}).items():
            for time, message in times.items():
                Parentmessages.append({
                    'date': date,
                    'time': time,
                    'Parentmessages': message
                })
        print(Parentmessages)
        return jsonify({'messages': Parentmessages})
    else:
        return jsonify({'messages': []}), 





@app.route("/personalDetail", methods=["POST"])
def get_personal_details():
    data = request.json
    print(data)
    regNo = int(data.get("regNo"))
    
    
    details = data["collection"]
    db = client.studentsdb
    collection = db.personalinfo
    filter = {"regNo": regNo}
    print(f"Filter used for query: {filter}")

    detailsData = list(collection.find(filter))
    personal_details = []
    parent_details = []
    address = []
    academic_details = []
    if not detailsData:
            print(f"No documents found for regNo: {regNo}")

    for doc in detailsData:
        print(f"Fetched document: {doc}")
        # Accessing personal_details
        if "personal_details" in doc:
            pdet = doc["personal_details"]
            dic = {}
            dic["name"] = pdet.get("name", "")
            dic["dep"] = pdet.get("dep", "")
            dic["section"] = pdet.get("section", "")
            dic["regNo"] = pdet.get("regNo", "")
            dic["religion"] = pdet.get("religion", "")
            dic["community"] = pdet.get("community", "")
            dic["lifeGoal"] = pdet.get("lifeGoal", "")
            dic["bloodGrp"] = pdet.get("bloodGrp", "")
            dic["languages"] = ", ".join(pdet.get("languages", []))
            personal_details.append(dic)

        # Accessing parent_details
        if "parent_details" in doc:
            pdet = doc["parent_details"]
            dic = {}
            dic["fatherPic"] = pdet.get("fatherPic","https://drive.google.com/file/d/1mPHC_7jlyWOKhhf095W5EugggRuVd6_l/view?usp=sharing")
            dic["fatherName"] = pdet.get("fatherName", "")
            dic["fatherMail"] = pdet.get("fatherMail", "")
            dic["fatherOcc"] = pdet.get("fatherOcc", "")
            dic["fatherNo"] = pdet.get("fatherNo", "")
            dic["motherPic"] = pdet.get("motherPic",'https://drive.google.com/file/d/1mPHC_7jlyWOKhhf095W5EugggRuVd6_l/view?usp=sharing')
            dic["motherName"] = pdet.get("motherName", "")
            dic["motherMail"] = pdet.get("motherMail", "")
            dic["motherOcc"] = pdet.get("motherOcc", "")
            dic["motherNo"] = pdet.get("motherNo", "")
            dic["guardianPic"] = pdet.get("guardianPic","https://drive.google.com/file/d/1mPHC_7jlyWOKhhf095W5EugggRuVd6_l/view?usp=sharing")
            dic["guardianName"] = pdet.get("guardianName", "")
            dic["guardianMail"] = pdet.get("guardianMail", "")
            dic["guardianOcc"] = pdet.get("guardianOcc", "")
            dic["guardianNo"] = pdet.get("guardianNo", "")
            parent_details.append(dic)

        # Accessing address
        if "address" in doc:
            pdet = doc["address"]
            dic = {}
            dic["permanentAdd"] = pdet.get("permanentAdd", "")
            dic["communicationAdd"] = pdet.get("communicationAdd", "")
            dic["phoneNo"] = pdet.get("phoneNo", "")
            dic["alterNo"] = pdet.get("alterNo", "")
            if "hosteller" in pdet and pdet["hosteller"]:
                dic["hostelName"] = pdet.get("hostelName", "")
                dic["hostelNo"] = pdet.get("hostelNo", "")
            address.append(dic)

        # Accessing academic_details
        if "academic_details" in doc:
            pdet = doc["academic_details"]
            dic = {}
            dic["previousInst"] = pdet.get("previousInst", "")
            dic["tenthper"] = pdet.get("tenthper", "")
            dic["twelfthper"] = pdet.get("twelfthper", "")
            academic_details.append(dic)

        print(f"Extracted personal_details: {personal_details}")
        print(f"Extracted parent_details: {parent_details}")
        print(f"Extracted address: {address}")
        print(f"Extracted academic_details: {academic_details}")

    return jsonify({"personaldetails": personal_details, "parentdetails": parent_details, "address": address, "academicdetails": academic_details})


from flask import jsonify

@app.route("/studentDashboard/studentPersonalInfoPage/editPersonalDetails", methods=["POST"])
def editPersonalDetails():
    try:
        data = request.json
        print("data gljeeeeeeeeeeeeeeeeeeeeeee")
        regNo = int(data["regNo"])

        updated_data = data["personalDetails"]
        print(updated_data)
        db = client["studentsdb"]
        personalInfoCollection = db["personalinfo"]
        studentPersonalInfo = list(personalInfoCollection.find({"regNo": regNo}))
        
        # Print for debugging
       # print("ssssssssssssssssssssss")
       

        # Prepare update query
        update = {
            '$set': {
                'personal_details': {
                    'name': studentPersonalInfo[0]["personal_details"]["name"],
                    'dep': studentPersonalInfo[0]["personal_details"]["dep"],
                    'section': updated_data.get("section", ""),
                    'regNo': studentPersonalInfo[0]["personal_details"]["regNo"],
                    'religion': updated_data.get("religion", ""),
                    'community': updated_data.get("community", ""),
                    'lifeGoal': updated_data.get("lifeGoal", ""),
                    'bloodGrp': updated_data.get("bloodGrp", ""),
                    'languages':  list(" ".join(updated_data.get("languages", "").split(",")).split())#list(" ".join(updated_data.get("languages", "").split(",")).split(" "))
                }
            }
        }
        print("ssssssssssssssssssssss",studentPersonalInfo[0])
        # Update personal details in the database
        personalInfoCollection.update_one({"regNo": regNo}, update)
        print("hii")

        # Update permissions to mark EditPersonalDetail as False
        permissionCollection = db["permissions"]
        studentPermissionInfo = permissionCollection.find({"regNo": regNo})
        permission_update_data = {
            '$set': {
                "PermissionsForPersonalInfo": {
                    "EditPersonalDetail": False,
                    "EditParentDetail": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditParentDetail", False),
                    "EditAddress": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditAddress", False),
                    "EditAcademicDetail": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditAcademicDetail", False)
                }
            }
        }

        permissionCollection.update_one({"regNo": regNo}, permission_update_data)

        # Return success message
        return jsonify({"message": "Personal details updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)})


# Google Drive API credentials
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'Credentials.json'

# Set the path for storing uploaded images
UPLOAD_FOLDER2 = 'uploads2'
app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2

upload_dir2 = os.path.join(app.root_path, UPLOAD_FOLDER2)
os.makedirs(upload_dir2, exist_ok=True)

FOLDER_ID = '1gd6Pr-0JAbsthamgFmviYXPxaoVPg9Fn'
@app.route("/studentDashboard/studentPersonalInfoPage/editParentDetails", methods=["POST"])
def editParentDetails():
    db = client.studentsdb
    personalInfoCollection = db.personalinfo
    permissionCollection = db.permissions
    
    try:
        regNo = int(request.form.get('regNo'))
        name = request.form.get('name')
        if not regNo:
            return jsonify({"error": "Registration number is required","success":"false"}), 400
        
        # Handle file uploads individually
        file_links = {}
        file_ids = {}
        
        father_image_file = request.files.get('fatherImage')
        mother_image_file = request.files.get('motherImage')
        guardian_image_file = request.files.get('guardianImage')
        
        if father_image_file and father_image_file.filename != '':
            father_image_path = os.path.join(upload_dir2, secure_filename(father_image_file.filename))
            father_image_file.save(father_image_path)
            try:
                father_file_id = driveAPI.upload_img_to_drive(father_image_path, f'{regNo}-{name}-fatherImage', FOLDER_ID, SCOPES, SERVICE_ACCOUNT_FILE)
                father_file_link = f'https://drive.google.com/file/d/{father_file_id}'
                file_links['fatherImage'] = father_file_link
                file_ids['fatherImage'] = father_file_id
            finally:
                if os.path.exists(father_image_path):
                    os.remove(father_image_path)
        
        if mother_image_file and mother_image_file.filename != '':
            mother_image_path = os.path.join(upload_dir2, secure_filename(mother_image_file.filename))
            mother_image_file.save(mother_image_path)
            try:
                mother_file_id = driveAPI.upload_img_to_drive(mother_image_path, f'{regNo}-{name}-motherImage', FOLDER_ID, SCOPES, SERVICE_ACCOUNT_FILE)
                mother_file_link = f'https://drive.google.com/file/d/{mother_file_id}'
                file_links['motherImage'] = mother_file_link
                file_ids['motherImage'] = mother_file_id
            finally:
                if os.path.exists(mother_image_path):
                    os.remove(mother_image_path)
        
        if guardian_image_file and guardian_image_file.filename != '':
            guardian_image_path = os.path.join(upload_dir2, secure_filename(guardian_image_file.filename))
            guardian_image_file.save(guardian_image_path)
            try:
                guardian_file_id = driveAPI.upload_img_to_drive(guardian_image_path, f'{regNo}-{name}-guardianImage', FOLDER_ID, SCOPES, SERVICE_ACCOUNT_FILE)
                guardian_file_link = f'https://drive.google.com/file/d/{guardian_file_id}'
                file_links['guardianImage'] = guardian_file_link
                file_ids['guardianImage'] = guardian_file_id
            finally:
                if os.path.exists(guardian_image_path):
                    os.remove(guardian_image_path)
        
        # Fetch current personal info
        studentPersonalInfo = personalInfoCollection.find_one({"regNo": regNo})
        if not studentPersonalInfo:
            return jsonify({"error": "Student not found","success":"false"}), 404

        # Get other parent details from the form
        updated_data = request.form
        
        # Update MongoDB with new parent details and file links
        update_fields = {
            'parent_details.fatherPic': file_links.get('fatherImage', studentPersonalInfo["parent_details"].get("fatherPic", "")),
            'parent_details.fatherName': updated_data.get("fatherName", studentPersonalInfo["parent_details"].get("fatherName", "")),
            'parent_details.fatherMail': updated_data.get("fatherMail", studentPersonalInfo["parent_details"].get("fatherMail", "")),
            'parent_details.fatherNo': updated_data.get("fatherNo", studentPersonalInfo["parent_details"].get("fatherNo", "")),
            'parent_details.fatherOcc': updated_data.get("fatherOcc", studentPersonalInfo["parent_details"].get("fatherOcc", "")),
            'parent_details.motherPic': file_links.get('motherImage', studentPersonalInfo["parent_details"].get("motherPic", "")),
            'parent_details.motherName': updated_data.get("motherName", studentPersonalInfo["parent_details"].get("motherName", "")),
            'parent_details.motherMail': updated_data.get("motherMail", studentPersonalInfo["parent_details"].get("motherMail", "")),
            'parent_details.motherNo': updated_data.get("motherNo", studentPersonalInfo["parent_details"].get("motherNo", "")),
            'parent_details.motherOcc': updated_data.get("motherOcc", studentPersonalInfo["parent_details"].get("motherOcc", "")),
            'parent_details.guardianPic': file_links.get('guardianImage', studentPersonalInfo["parent_details"].get("guardianPic", "")),
            'parent_details.guardianName': updated_data.get("guardianName", studentPersonalInfo["parent_details"].get("guardianName", "")),
            'parent_details.guardianMail': updated_data.get("guardianMail", studentPersonalInfo["parent_details"].get("guardianMail", "")),
            'parent_details.guardianNo': updated_data.get("guardianNo", studentPersonalInfo["parent_details"].get("guardianNo", "")),
            'parent_details.guardianOcc': updated_data.get("guardianOcc", studentPersonalInfo["parent_details"].get("guardianOcc", "")),
        }
        
        personalInfoCollection.update_one({"regNo": regNo}, {'$set': update_fields}, upsert=True)

        # Update permissions to mark EditParentDetail as False
        studentPermissionInfo = permissionCollection.find_one({"regNo": regNo})
        if studentPermissionInfo:
            permission_update_data = {
                '$set': {
                    "PermissionsForPersonalInfo": {
                        "EditPersonalDetail": studentPermissionInfo["PermissionsForPersonalInfo"].get("EditPersonalDetail", False),
                        "EditParentDetail": False,
                        "EditAddress": studentPermissionInfo["PermissionsForPersonalInfo"].get("EditAddress", False),
                        "EditAcademicDetail": studentPermissionInfo["PermissionsForPersonalInfo"].get("EditAcademicDetail", False)
                    }
                }
            }
            permissionCollection.update_one({"regNo": regNo}, permission_update_data)

        return jsonify({"success": "true", "fileLinks": file_links, "fileIds": file_ids})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e),"success":"false"}), 500


       

@app.route("/studentDashboard/studentPersonalInfoPage/editAddress", methods=["POST"])
def editAddress():
    data = request.json
    regNo = int(data["regNo"])

    updated_data = data["address"]
    db = client["studentsdb"]
    personalInfoCollection = db["personalinfo"]
    
    # Fetching student's personal information
    studentPersonalInfo = personalInfoCollection.find({"regNo": regNo})
    print(studentPersonalInfo[0])

    # Update academic details
    update = {
        '$set': {
             'address': {
               'permanentAdd': updated_data.get("permanentAdd", ""),
               'communicationAdd': updated_data.get("communicationAdd", "") ,
               'phoneNo': updated_data.get("phoneNo",""),
               'alterNo': updated_data.get("alterNo",""),
               'hosteller':updated_data.get("hosteller",False),
               'hostelName': updated_data.get("hostelName",""),
               'hostelNo': updated_data.get("hostelNo",""),
               }
            }
        }

    # Update permissions for academic details editing
    permissionCollection = db["permissions"]
    studentPermissionInfo = permissionCollection.find({"regNo": regNo})
    permission_update_data = {
        '$set': {
            "PermissionsForPersonalInfo": {
                "EditPersonalDetail": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditPersonalDetail", False),
                "EditParentDetail": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditParentDetail", False),
                "EditAddress": False,
                "EditAcademicDetail": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditAcademicDetail", False)
            }
        }
    }

    # Perform updates in the database
    permissionUpdatedResult = permissionCollection.update_one({"regNo": regNo}, permission_update_data)
    updatedResult = personalInfoCollection.update_one({"regNo": regNo}, update)

    return jsonify({"message": "Success"})




@app.route("/studentDashboard/studentPersonalInfoPage/editAcademicDetails", methods=["POST"])
def editAcademicDetails():
    data = request.json
    regNo = int(data["regNo"])

    updated_data = data["academicDetails"]
    db = client["studentsdb"]
    personalInfoCollection = db["personalinfo"]
    
    # Fetching student's personal information
    studentPersonalInfo = personalInfoCollection.find({"regNo": regNo})
    print(studentPersonalInfo[0])

    # Update academic details
    update = {
        '$set': {
            'academic_details': {
                'previousInst': updated_data.get("previousInst", ""),
                'tenthper': updated_data.get("tenthper", ""),
                'twelfthper': updated_data.get("twelfthper", "")
            }
        }
    }

    # Update permissions for academic details editing
    permissionCollection = db["permissions"]
    studentPermissionInfo = permissionCollection.find({"regNo": regNo})
    permission_update_data = {
        '$set': {
            "PermissionsForPersonalInfo": {
                "EditPersonalDetail": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditPersonalDetail", False),
                "EditParentDetail": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditParentDetail", False),
                "EditAddress": studentPermissionInfo[0]["PermissionsForPersonalInfo"].get("EditAddress", False),
                "EditAcademicDetail": False
            }
        }
    }

    # Perform updates in the database
    permissionUpdatedResult = permissionCollection.update_one({"regNo": regNo}, permission_update_data)
    updatedResult = personalInfoCollection.update_one({"regNo": regNo}, update)

    return jsonify({"message": "Success"})




# Google Drive API credentials
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'Credentials.json'

# Specify the folder ID where you want to upload the file
FOLDER_ID_CONDUCTED = '1dxxdq_5_KBzM06QuN2OkV5GZhe5Pg84h'
FOLDER_ID_ATTENTED = '1j-BxGZqy4A4ZOqezAtKxLcralIucr9ol'

@app.route('/studentdashboard/<string:studentId>/AddEvents', methods=['POST'])
def add_event(studentId):
    db = client.studentsdb
    collection = db.events
    brouchere_path = None
    certificate_path = None
    try:
        event_name = request.form['eventName']
        event_type = request.form['eventType']
        event_summary = request.form['eventSummary']
        semester = request.form['semester']
        conducted_or_attended = request.form['conductedOrAttended']
        studentName = request.form['studentName']
        # Handle file uploads
        brouchure = request.files.get('brouchure')
        certificate = request.files.get('certificate')
        
        brouchure_link = ""
        certificate_link = ""
        print(conducted_or_attended)
        if brouchure:
            brouchere_path = os.path.join(upload_dir, secure_filename(brouchure.filename))
            brouchure.save(brouchere_path)
            brouchure_id = driveAPI.upload_file_to_drive(
                brouchere_path,  f'{studentId}-{studentName}-Semester{semester}',
                FOLDER_ID_CONDUCTED if conducted_or_attended == 'events_conducted' else FOLDER_ID_ATTENTED,
                SCOPES, SERVICE_ACCOUNT_FILE
            )
            brouchure_link = f'https://drive.google.com/file/d/{brouchure_id}'
            brouchure_info = {
                    'bfileURL': f'https://drive.google.com/file/d/{brouchure_id}',
                    'bfileName': brouchure.filename,
                    'brouchureURL': f'https://drive.google.com/file/d/{brouchure_id}'
                }
        if certificate:
            certificate_path = os.path.join(upload_dir, secure_filename(certificate.filename))
            certificate.save(certificate_path)
            certificate_id = driveAPI.upload_file_to_drive(
                certificate_path, f'{studentId}-{studentName}-Semester{semester}',
                FOLDER_ID_CONDUCTED if conducted_or_attended == 'events_conducted' else FOLDER_ID_ATTENTED,
                SCOPES, SERVICE_ACCOUNT_FILE
            )
            certificate_link = f'https://drive.google.com/file/d/{certificate_id}'
            certificate_info = {
            'fileURL': f'https://drive.google.com/file/d/{certificate_id}',
            'fileName': certificate.filename,
            'certificateURL': f'https://drive.google.com/file/d/{certificate_id}'
            }   
        # Prepare event data
        event_data = {
            'eventName': event_name,
            'eventType': event_type,
            'eventSummary': event_summary,
            'Brouchure': brouchure_info,
            'certificate': certificate_info
        }

        # Update MongoDB
        update_query = {
            '$push': {
                f'{conducted_or_attended}.semester{semester}': event_data
            }
        }

        result = collection.update_one({'regNo': studentId}, update_query, upsert=True)

        if result.modified_count > 0 or result.upserted_id:
            return jsonify({'success': True, 'message': 'Event added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add event'})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Error adding event'}), 500
    finally:
        if brouchere_path and os.path.exists(brouchere_path):
            os.remove(brouchere_path)
        if certificate_path and os.path.exists(certificate_path):
            os.remove(certificate_path)

# get_student_register_numbers_by_email
register_events_cache = {}  # Shared dictionary to store register events counts

@app.route('/get_student_register_numbers_by_email', methods=['GET'])
@jwt_required()
def get_student_register_numbers_by_email():
    try:
        university_email = request.args.get('university_email')
        db = client.jgspdb
        collection = db.guidesstudents
        db1 = client.studentsdb
        events_collection = db1.events
        
        document = collection.find_one({'University EMAIL ID': university_email})
        register_numbers_for_Events = []
        
        if document and 'students' in document:
            register_numbers_for_Events = [student['regNo'] for student in document['students']]
            print('Events list:', register_numbers_for_Events)
        
        total_events_attended_count = 0
        total_events_conducted_count = 0
        register_events_counts = {}
        
        for reg_no in register_numbers_for_Events:
            attended = events_collection.find_one({'regNo': str(reg_no)}, {'events_attended': 1})
            conducted = events_collection.find_one({'regNo': str(reg_no)}, {'events_conducted': 1})
            
            attended_count = 0
            conducted_count = 0
            
            if attended and 'events_attended' in attended:
                for semester, events in attended['events_attended'].items():
                    attended_count += len(events)
                    total_events_attended_count += len(events)
            
            if conducted and 'events_conducted' in conducted:
                for semester, events in conducted['events_conducted'].items():
                    conducted_count += len(events)
                    total_events_conducted_count += len(events)
            
            register_events_counts[str(reg_no)] = {
                'attended_count': attended_count,
                'conducted_count': conducted_count
            }
        
        # Store the register events counts in the shared dictionary
        register_events_cache[university_email] = register_events_counts

        print('Total Events Attended Count:', total_events_attended_count)
        print('Total Events Conducted Count:', total_events_conducted_count)
        
        return jsonify({
            'total_events_attended_count': total_events_attended_count,
            'total_events_conducted_count': total_events_conducted_count,
            'register_events_counts': register_events_counts
        }), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    



#  dowload button 
@app.route('/downloadEvents', methods=['GET'])
def download_events():
    try:
        university_email = request.args.get('university_email')
        db = client.jgspdb
        collection = db.guidesstudents
        db1 = client.studentsdb
        events_collection = db1.events
        student_collection = db.regstudents

        document = collection.find_one({'University EMAIL ID': university_email})
        register_numbers_for_Events = []

        if document and 'students' in document:
            register_numbers_for_Events = [student['regNo'] for student in document['students']]
            print('events list ---', register_numbers_for_Events)

        events_attended_data = []
        events_conducted_data = []

        for reg_no in register_numbers_for_Events:
            attended = events_collection.find_one({'regNo': str(reg_no)}, {'events_attended': 1})
            conducted = events_collection.find_one({'regNo': str(reg_no)}, {'events_conducted': 1})

            student_info = student_collection.find_one({'regNo': reg_no}, {'_id': 0, 'mailId': 1, 'name': 1})
            # print(student_info)
            if attended and 'events_attended' in attended:
                for semester, events in attended['events_attended'].items():
                    for event in events:
                        brouchureURL = event['Brouchure'].get('brouchureURL', '') if 'Brouchure' in event else ''
                        certificateURL = event['certificate'].get('certificateURL', '') if 'certificate' in event else ''
                        event_data = {
                            'semester': semester,
                            'regNo': str(reg_no),
                            'eventName': event['eventName'],
                            'eventType': event['eventType'],
                            'eventSummary': event['eventSummary'],
                            'Brouchure_brouchureURL': brouchureURL,
                            'certificate_certificateURL': certificateURL
                        }
                        if student_info:
                            event_data.update(student_info)
                        events_attended_data.append(event_data)

            if conducted and 'events_conducted' in conducted:
                for semester, events in conducted['events_conducted'].items():
                    for event in events:
                        brouchureURL = event['Brouchure'].get('brouchureURL', '') if 'Brouchure' in event else ''
                        certificateURL = event['certificate'].get('certificateURL', '') if 'certificate' in event else ''
                        event_data = {
                            'semester': semester,
                            'regNo': str(reg_no),
                            'eventName': event['eventName'],
                            'eventType': event['eventType'],
                            'eventSummary': event['eventSummary'],
                            'Brouchure_brouchureURL': brouchureURL,
                            'certificate_certificateURL': certificateURL
                        }
                        if student_info:
                            event_data.update(student_info)
                        events_conducted_data.append(event_data)

        df_attended = pd.DataFrame(events_attended_data)
        df_conducted = pd.DataFrame(events_conducted_data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_attended.to_excel(writer, index=False, sheet_name='Events Attended')
            df_conducted.to_excel(writer, index=False, sheet_name='Events Conducted')
        output.seek(0)

        return send_file(output, download_name='student_events_data.xlsx', as_attachment=True)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route("/getStudentProfileData", methods=["POST"])
@jwt_required()
def getStudentProfileData():
    data = request.json
    print("data from frontend", data)

    filter = {"University EMAIL ID": data['guideMail']}

    collection = client.jgspdb.guidesstudents
    result2 = collection.find_one(filter)

    student_data = None
    for doc in result2['students']:
        if int(doc['regNo']) == int(data['regNo']):
            student_data = doc
            break

    if student_data:
        # Retrieve the register events counts from the shared dictionary
        register_events_counts = register_events_cache.get(data['guideMail'], {})
        student_reg_no = str(data['regNo'])
        student_events_counts = register_events_counts.get(student_reg_no, {})
        print('events Count:',student_events_counts)
        # print(type(student_events_counts.conducted_count))
        return jsonify({
            "StudentData": student_data,
            "StudentEventsCounts": student_events_counts
        })
    
    return jsonify({"message": "Success"})




if __name__ == '__main__':
    app.debug = True
    authenticate()
    app.run()
