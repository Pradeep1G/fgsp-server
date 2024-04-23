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
    filter = {"mailId":mailid}
    result = collection.find_one(filter)
    print(result)
    if result:
        if result['password']==data['password']:
            print("----")
            return jsonify({"message" : "Valid Credentials"})
        else:
            return jsonify({"message" : "Invalid Credentials"})
    else:
        return jsonify({"message" : "Account not found!"})
    

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
            return jsonify({"message" : "Valid Credentials"})
        else:
            return jsonify({"message" : "Invalid Credentials"})
    else:
        return jsonify({"message" : "Account not found!"})
    
@app.route('/getStudentData', methods=["POST"])
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
def getGuideData():
    data = request.json
    filter = {"University EMAIL ID":data['GuideMailId']}

    result = {}

    collection = db.allstaff
    result1 = collection.find_one(filter)
    

    collection =db.guidesstudents
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

    # result['STUDENTS'] = result2['students']


    # print(result)
    return jsonify({"GuideDetails":result, "AllStudents":result2['students']})




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
    

@app.route("/sendMessage/<string:mailid>", methods=["POST"])
def sendMessage(mailid):

    data = request.json


    collection = db.regstudents
    filter_query = {"mailId":mailid}
    update_query = {
        "$push" : {
            "messages" : {
                data['date'] : data["message"]
            }
        }
    }
    result = collection.update_one(filter_query, update_query)


    if result.modified_count > 0:
        return jsonify({"message": "SENT"})
    else:
        return jsonify({"message":"NOT SENT"})
    

    
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

@app.route("/getStudentProfileData", methods=["POST"])
def getStudentProfileData():
    data = request.json
    print(data)

    filter = {"University EMAIL ID": data['guideMail']}

    result = {}

    collection = db.guidesstudents
    result2 = collection.find_one(filter)

    for doc in result2['students']:
        if int(doc['regNo'])==int(data['regNo']):
            print(doc)
            return jsonify({"StudentData":doc})
            
        
    return jsonify({"message": "Success"})


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
    events = data["collection"]
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



@app.route("/personalDetail", methods=["GET","POST"])
def get_personal_details():
    data = request.json
    regNo = data["regNo"]
    details = data["collection"]
    db = client.studentsdb
    collection = db.personalinfo
    filter = {"regNo": regNo}

    detailsData = list(collection.find(filter))
    personal_details = []
    parent_details = []
    address = []
    academic_details = []

    for doc in detailsData:
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
            dic["languages"] = pdet.get("languages", [])
            personal_details.append(dic)

        # Accessing parent_details
        if "parent_details" in doc:
            pdet = doc["parent_details"]
            dic = {}
            dic["fatherName"] = pdet.get("fatherName", "")
            dic["fatherMail"] = pdet.get("fatherMail", "")
            dic["fatherOcc"] = pdet.get("fatherOcc", "")
            dic["fatherNo"] = pdet.get("fatherNo", "")
            dic["motherName"] = pdet.get("motherName", "")
            dic["motherMail"] = pdet.get("motherMail", "")
            dic["motherOcc"] = pdet.get("motherOcc", "")
            dic["motherNo"] = pdet.get("motherNo", "")
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

    return jsonify({"personaldetails": personal_details, "parentdetails": parent_details, "address": address, "academicdetails": academic_details})





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
    regNo =  data["regNo"]
    result = data["collection"]
    db = client.studentsdb
    collection = db.results
    filter = {"regNo":regNo}

    results_details = []
    
    resultData = list(collection.find(filter))

    for doc in resultData:
            dic = {}
            dic["Semester 1"]= doc["Semester 1"]
            dic["Semester 2"]= doc["Semester 2"]
            dic["Semester 3"]= doc["Semester 3"]
            dic["Semester 4"]= doc["Semester 4"]
            dic["Semester 5"]= doc["Semester 5"]
            dic["Semester 6"]= doc["Semester 6"]
            dic["Semester 7"]= doc["Semester 7"]
            dic["Semester 8"]= doc["Semester 8"]
            results_details.append(dic)
    return ({"results":results_details})

@app.route("/insert_meeting", methods=["POST"])
def insert_meeting():
    data = request.json
    regNo = data["regNo"]
    mentor = data["Meeting"]
    db = client.studentsdb
    collection = db.MentorMeeting

    document = {
        "regNo": regNo,
        "Meeting": mentor
    }

    try:
        result = collection.insert_one(document)
        inserted_id = str(result.inserted_id)
        return jsonify({"message": "meeting data inserted successfully", "inserted_id": inserted_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route("/insert_remarks", methods=["POST"])
def insert_remarks():
    data = request.json
    regNo = data["regNo"]
    remarks = data["remarksInfo"]
    db = client.studentsdb
    collection = db.remarks

    document = {
        "regNo": regNo,
        "remarksInfo": remarks
    }

    try:
        result = collection.insert_one(document)
        inserted_id = str(result.inserted_id)
        return jsonify({"message": "Remarks data inserted successfully", "inserted_id": inserted_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/permissionDetail", methods = ["POST"])
def permissionDetail():
    data = request.json
    regNo = data["regNo"]
    result = data["collection"]
    db = client.studentsdb
    collection = db.permission
    filter = {"regNo":regNo}

    permission_details = []
    
    permissionData = list(collection.find(filter))

    for doc in permissionData:
            dic = {}
            dic["personalinfo"]= doc["personalinfo"]
            dic["eventsinfo"]= doc["eventsinfo"]
            dic["resultsinfo"]= doc["resultsinfo"]
            dic["additionalinfo"]= doc["additionalinfo"]
            permission_details.append(dic)
    return ({"permission":permission_details})








if __name__ == '__main__':
    app.debug = True
    authenticate()
    app.run()
