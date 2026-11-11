import openpyxl
import json

wb = openpyxl.load_workbook('dataset.xlsx')
ws_user = wb['User']
User_Management = 14
Schedule_Management = 15
Vendor_Management = 16
Materials_Management = 17
Warehouse_and_inventory =18
Purchasing =19
Customer_Management =20
Online_transection = 21

email = 5
Id = 1
user = []
# print(ws_user.title)
for i in range(2, 101 + 1):
    user_application = []
    user_id = ws_user.cell(row = i, column = Id).value
    user_email = ws_user.cell(row = i, column = email).value
    # print(ws_user.cell(row = i, column = User_Management).value)
    if(ws_user.cell(row = i, column = User_Management).value==True):
        user_application.append('User Management')
    if(ws_user.cell(row = i, column = Schedule_Management).value==True):
        user_application.append('Schedule Management')
    if(ws_user.cell(row = i, column = Vendor_Management).value==True):
        user_application.append('Vendor Management')
    if(ws_user.cell(row = i, column = Materials_Management).value==True):
        user_application.append('Materials Management')
    if(ws_user.cell(row = i, column = Warehouse_and_inventory).value==True):
        user_application.append('Warehouse and inventory')
    if(ws_user.cell(row = i, column = Purchasing).value==True):
        user_application.append('Purchasing')
    if(ws_user.cell(row = i, column = Customer_Management).value==True):
        user_application.append('Customer Management')
    if(ws_user.cell(row = i, column = Online_transection).value==True):
        user_application.append('Online transection')
    
    # print(user_id.value)
    # print(user_application)
    person = { "id": user_id, "email": user_email, "applications": user_application }
    person_json = json.dumps(person)
    # print(person_json)
    # y = json.loads(person_json)
    # print(y["id"])
    user.append(person_json)
print(user)




wb.create_sheet("user_applications")
ws_user_applications = wb['user_applications']
# //////////////////////////////////////////////////
user_applications_id = 1
user_applications_email = 2
user_applications_application = 3
user_applications_type_application = 4
user_applications_row = 1
# /////////////////////////////////////////////////
ws_user_applications.cell(row = user_applications_row, column = user_applications_id).value = "id"
ws_user_applications.cell(row = user_applications_row, column = user_applications_email).value = "email"
ws_user_applications.cell(row = user_applications_row, column = user_applications_application).value = "application"
ws_user_applications.cell(row = user_applications_row, column = user_applications_type_application).value = "type"
for i in user:
    person_json = json.loads(i)
    for j in person_json["applications"]:
        user_applications_row = user_applications_row+1
        ws_user_applications.cell(row = user_applications_row, column = user_applications_id).value = person_json["id"]
        ws_user_applications.cell(row = user_applications_row, column = user_applications_email).value = person_json["email"]
        ws_user_applications.cell(row = user_applications_row, column = user_applications_application).value = j
        if(j == "Customer Management" or j == "Online transection"):
            ws_user_applications.cell(row = user_applications_row, column = user_applications_type_application).value = "front"
        elif(j == "User Management" or j == "Schedule Management" or j == "Vendor Management" or j == "Materials Management" or j == "Warehouse and inventory" or j == "Purchasing"):
            ws_user_applications.cell(row = user_applications_row, column = user_applications_type_application).value = "back"


wb.save("dataset_test.xlsx")


# for i in wb:
#     print(i.title)
#     print(i['A1'].value)
# print(wb2['Location'])
