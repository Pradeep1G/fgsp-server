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



import openpyxl

def get_entire_row(file_path, sheet_name, row_number):
    try:
        # Load the Excel workbook
        workbook = openpyxl.load_workbook(file_path)

        # Select the desired sheet
        sheet = workbook[sheet_name]

        # Get the values in the specified row
        row_data = sheet[row_number]

        headers = [cell.value for cell in sheet[1]]

        # Print the values in the row
        row_dict = dict(zip(headers, [cell.value for cell in row_data]))

        print(row_dict)
        # print(row_data)
        # row_data["REGISTER NUMBER"]

        # Close the workbook
        workbook.close()
        return row_dict

    except Exception as e:
        print(f"An error occurred: {e}")



def get_google_drive_link(service, regNo):
    folder_name="B.E_COMPUTER SCIENCE AND ENGINEERING"
    file_name=str(regNo)+".jpg"

    # Get the folder ID by searching for the folder by name
    folder_results = service.files().list(q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'", fields="files(id)").execute()
    folders = folder_results.get('files', [])

    if not folders:
        print(f"No folder found with the name '{folder_name}'.")
        return None

    folder_id = folders[0]['id']

    # Search for the file by name and in the specified folder
    results = service.files().list(q=f"name='{file_name}' and '{folder_id}' in parents", fields="files(id,webViewLink)").execute()
    files = results.get('files', [])

    if not files:
        print(f"No file found with the name '{file_name}' in the folder '{folder_name}'.")
        return None

    file_id = files[0]['id']
    web_view_link = files[0]['webViewLink']

    # print(f"Shareable link for '{file_name}' in folder '{folder_name}': {web_view_link}")
    return web_view_link


# creds = authenticate()
# service = build('drive', 'v3', credentials=creds)
# google_drive_link = get_google_drive_link(service, 41111354)
# print(google_drive_link)


def update_guides_students_data(stData, stMentorData):

    reg_no = stData.get('REGISTER NUMBER')
    name = stData.get('NAME')
    gender = stData.get('GENDER')
    father_name = stData.get("FATHER NAME")
    mother_name = stData.get("MOTHER NAME")
    dob = stData.get("BIRTH DATE")
    full_address = stData.get("ADDRESS")

    mail_id = stData.get('EMAIL')
    phone_no = stData.get('PHONE')

    guide_mail_id = stMentorData.get('Mentor Mail Id')
    # address = request.form.get("address")
    # section = request.form.get("section")

    nationality = stData.get("NATIONALITY")
    religion = stData.get("RELIGION")
    community = stData.get("COMMUNITY")
    aadhar = stData.get("AADHAR")

    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    google_drive_link = get_google_drive_link(service, stData["REGISTER NUMBER"])

    # Filter to find the document by GuideMailId
    filter_query = {"University EMAIL ID": guide_mail_id}

    try:


        # Update the document by adding student_data to the students array
        update_query = {
            "$push": {
                "students": {
                    "image": google_drive_link,
                    "regNo": reg_no,
                    "mailId": mail_id,
                    "phoneNo": phone_no,
                    "name": name,
                    "fullAddress": full_address,
                    "gender":gender,
                    "fatherName":father_name,
                    "motherName":mother_name,
                    "dob":dob,
                    "nationality":nationality,
                    "religion":religion,
                    "community":community,
                    "aadhar":aadhar       
                }
            }
        }

        collection = db.guidesstudents
        # Use update_one to update the document based on the filter
        result = collection.update_one(filter_query, update_query)

        collection = db.regstudents
        filter = {"mailId":mail_id}
        res = collection.update_one(filter, {'$set': {"image":google_drive_link}})
        print(res)
        print("\n\n",result)
        # if result.modified_count > 0:
        #     # Delete the local image file after successful upload to Google Drive
        #     # os.remove(filename)
        #     return jsonify({"message": "Updated Guides Students Data Successfully"})
        # else:
        #     # return jsonify({"error": "No document found for the given GuideMailId"}), 404

        



    except Exception as e:
        print(str(e))
        # return jsonify({"error": str(e)}), 500

    # return jsonify({"error": "Image not provided"}), 400


# Example usage
# file_path = 'AllStudentsData.xlsx'
# sheet_name = 'Students_Data'  # Change this to the actual sheet name
# for i in range(82,101):
#     row_number = i  # Change this to the desired row number

#     stData = get_entire_row(file_path, sheet_name, row_number)
#     stMentorData = get_entire_row('Mentor Mentee.xlsx', sheet_name, row_number)

#     update_guides_students_data(stData, stMentorData)
