#run_result
import openpyxl
import json

wc_result_time = 1
wc_result_date = 2
wc_result_day = 3
wc_result_user_id = 4
wc_result_email = 5
wc_result_password = 6
wc_result_model = 7
wc_result_application = 8
wc_result_location = 9
wc_result_mac_address = 10
wc_result_street_address = 11
wc_result_postal = 12
wc_result_country = 13
wc_result_state = 14
wc_result_latitude = 15
wc_result_longtitude = 16
wc_result_app_type = 17
wc_result_result = 18
row = 1

wb_user = openpyxl.load_workbook('dataset.xlsx')
ws_user = wb_user['User']
wb_result = openpyxl.load_workbook('result.xlsx')
ws_result = wb_result['result']

wb_data_for_train = openpyxl.load_workbook('data_for_train.xlsx')
ws_data_for_train = wb_data_for_train['data_for_train']

ws_device_location = wb_user['device_location']
ws_portable = wb_user['Portable MAC address']
ws_non_portable = wb_user['Non-Portable MAC address']


wc_data_for_train_time = 1
wc_data_for_train_date = 2
wc_data_for_train_day = 3
wc_data_for_train_user_id = 4
wc_data_for_train_check_user_location = 5
wc_data_for_train_check_model = 6
wc_data_for_train_check_MAC_address  = 7
wc_data_for_train_check_MAC_address_exists = 8
wc_data_for_train_check_device_location = 9
wc_data_for_train_check_device_location_exists = 10
wc_data_for_train_result = 11


def check_model(ar):
    wc_user_model = 7
    user_model = ws_user.cell(row = ar["user_id"] +1 , column = wc_user_model).value
    if(ar["model"] == user_model):
        return True
    else :
        return False

def check_MAC_address(ar):
    wc_user_mac_address = 8
    wc_device_location_mac_address = 8
    wc_device_location_app = 8
    wc_device_location_branch = 4
    if(ar["model"] == "portable"):
        user_mac = ws_user.cell(row = ar["user_id"] +1 , column = wc_user_mac_address).value
        if(ar["mac_address"] == user_mac):
            return True
        else :
            return False
    else :
        for mac in range(ws_device_location.min_row+1, ws_device_location.max_row+1):
            mac_address = ws_device_location.cell(row = mac, column = wc_device_location_mac_address).value
            if ar["mac_address"] == mac_address : 
                device_location = ws_device_location.cell(row = mac, column = wc_device_location_branch).value
                app = ws_device_location.cell(row = mac, column = wc_device_location_branch).value
                if(ar["location"] == device_location and ar["app_type"] == app):
                    return True
                else :
                    return False
        return False

def check_MAC_address_exists(ar):
    if(ar["model"] == "portable"):
        for mac in range(ws_portable.min_row, ws_portable.max_row+1):
            mac_address = ws_portable.cell(row = mac, column = 1).value
            if ar["mac_address"] == mac_address :
                return True
        return False
    else :
        for mac in range(ws_non_portable.min_row, ws_non_portable.max_row+1):
            mac_address = ws_non_portable.cell(row = mac, column = 1).value
            if ar["mac_address"] == mac_address :
                return True
        return False


def check_user_location(ar):
    Monday = 9
    Tuesday = 10 
    Wednesday = 11
    Thursday = 12
    Friday = 13
    if(ar["day"] == "Monday"):
        user_location = ws_user.cell(row = ar["user_id"] +1 , column = Monday).value
    elif(ar["day"] == "Tuesday"):
        user_location = ws_user.cell(row = ar["user_id"] +1 , column = Tuesday).value
    elif(ar["day"] == "Wednesday"):
        user_location = ws_user.cell(row = ar["user_id"] +1 , column = Wednesday).value
    elif(ar["day"] == "Thursday"):
        user_location = ws_user.cell(row = ar["user_id"] +1 , column = Thursday).value
    elif(ar["day"] == "Friday"):
        user_location = ws_user.cell(row = ar["user_id"] +1 , column = Friday).value
    if(ar["location"] == user_location):
        return True
    else :
        return False

def check_device_location(ar):
    wc_device_location_mac_address = 8
    wc_device_location_branch = 4
    for mac in range(ws_device_location.min_row+1, ws_device_location.max_row+1):
        mac_address = ws_device_location.cell(row = mac, column = wc_device_location_mac_address).value
        if ar["mac_address"] == mac_address : 
            device_location = ws_device_location.cell(row = mac, column = wc_device_location_branch).value
            if(ar["location"] == device_location):
                return True
            else :
                return False
    return False

def check_device_location_exists(ar):
    wc_device_location_mac_address = 8
    wc_device_location_branch = 4
    for mac in range(ws_device_location.min_row+1, ws_device_location.max_row+1):
        mac_address = ws_device_location.cell(row = mac, column = wc_device_location_mac_address).value
        if ar["mac_address"] == mac_address : 
            return True
    return False


def authentication_location_base():
    ws_result.cell(row = row, column = wc_result_result).value = "result"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_time).value = "time"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_date).value = "date"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_day).value = "day"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_user_id).value = "user_id"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_check_user_location).value = "result_check_user_location"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_check_model).value = "result_check_model"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_check_MAC_address ).value = "result_check_MAC_address "
    ws_data_for_train.cell(row = row , column = wc_data_for_train_check_MAC_address_exists).value = "result_check_MAC_address_exists"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_check_device_location).value = "result_check_device_location"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_check_device_location_exists).value = "result_check_device_location_exists"
    ws_data_for_train.cell(row = row , column = wc_data_for_train_result).value = "result"
    for i in range (ws_result.min_row+1,ws_result.max_row+1):
        print(i)
        time = ws_result.cell(row = i , column = wc_result_time).value
        date = ws_result.cell(row = i , column = wc_result_date).value
        day = ws_result.cell(row = i , column = wc_result_day).value
        user_id = ws_result.cell(row = i , column = wc_result_user_id).value
        email = ws_result.cell(row = i , column = wc_result_email).value
        password = ws_result.cell(row = i , column = wc_result_password).value
        model = ws_result.cell(row = i , column = wc_result_model).value
        application = ws_result.cell(row = i , column = wc_result_application).value
        location = ws_result.cell(row = i , column = wc_result_location).value
        mac_address = ws_result.cell(row = i , column = wc_result_mac_address).value
        street_address = ws_result.cell(row = i , column = wc_result_street_address).value
        postal = ws_result.cell(row = i , column = wc_result_postal).value
        country = ws_result.cell(row = i , column = wc_result_country).value
        state = ws_result.cell(row = i , column = wc_result_state).value
        latitude = ws_result.cell(row = i , column = wc_result_latitude).value
        longtitude = ws_result.cell(row = i , column = wc_result_longtitude).value
        app_type = ws_result.cell(row = i , column = wc_result_app_type).value
        authentication_request = {
            "time" : time,
            "date" : date,
            "day" : day,
            "user_id" : user_id,
            "email" : email,
            "password" : password,
            "model" : model,
            "application" : application,
            "location" : location,
            "mac_address" : mac_address,
            "street_address" : street_address,
            "postal" : postal,
            "country" : country,
            "state" : state,
            "latitude" : latitude,
            "longtitude" : longtitude,
            "app_type" : app_type
        }
        a_r = json.dumps(authentication_request)
        ar = json.loads(a_r)
        result_check_user_location = check_user_location(ar)
        result_check_model = check_model(ar)
        result_check_MAC_address  = check_MAC_address(ar) 
        result_check_MAC_address_exists = check_MAC_address_exists(ar)
        result_check_device_location = check_device_location(ar)
        result_check_device_location_exists = check_device_location_exists(ar)

        ws_data_for_train.cell(row = i , column = wc_data_for_train_time).value = time
        ws_data_for_train.cell(row = i , column = wc_data_for_train_date).value = date
        ws_data_for_train.cell(row = i , column = wc_data_for_train_day).value = day
        ws_data_for_train.cell(row = i , column = wc_data_for_train_user_id).value = user_id
        ws_data_for_train.cell(row = i , column = wc_data_for_train_check_user_location).value = result_check_user_location
        ws_data_for_train.cell(row = i , column = wc_data_for_train_check_model).value = result_check_model
        ws_data_for_train.cell(row = i , column = wc_data_for_train_check_MAC_address ).value = result_check_MAC_address 
        ws_data_for_train.cell(row = i , column = wc_data_for_train_check_MAC_address_exists).value = result_check_MAC_address_exists
        ws_data_for_train.cell(row = i , column = wc_data_for_train_check_device_location).value = result_check_device_location
        ws_data_for_train.cell(row = i , column = wc_data_for_train_check_device_location_exists).value = result_check_device_location_exists
        result_temp = ""
        if result_check_user_location:
            if result_check_model:
                if ar["model"] == "portable" :
                    if result_check_MAC_address and result_check_MAC_address_exists :
                        result_temp = "Allow"
                    elif result_check_MAC_address_exists :
                        result_temp = "Allow with condition"
                    else :
                        result_temp = "Deny"
                else :
                    if result_check_MAC_address and result_check_MAC_address_exists :
                        if result_check_device_location and result_check_device_location_exists :
                            result_temp = "Allow"
                        elif result_check_device_location_exists :
                            result_temp = "Allow with condition"
                        else :
                            result_temp = "Deny"
                    elif result_check_MAC_address_exists :
                        result_temp = "Allow with condition"
                    else :
                        result_temp = "Deny"
            else :
                result_temp = "Deny"
        else :
            result_temp = "Deny"
        ws_result.cell(row = i , column = wc_result_result).value = result_temp
        ws_data_for_train.cell(row = i , column = wc_data_for_train_result).value = result_temp
    wb_result.save("result_test.xlsx")
    wb_data_for_train.save("data_for_train.xlsx")

if __name__ == '__main__':
    authentication_location_base()




