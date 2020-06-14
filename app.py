from flask import Flask, request, make_response
import json
import os
from flask_cors import cross_origin
from SendEmail.sendEmail import EmailSender
from logger import logger
from email_templates import template_reader
import requests
import pandas as pd

app = Flask(__name__)
HEADERS = {
    'x-rapidapi-key': '4e9c28ea17mshfb6b7904c0cb238p13392cjsn8ac112c67f2a',
    'x-rapidapi-host': 'corona-virus-world-and-india-data.p.rapidapi.com'

}
API_URL = 'https://corona-virus-world-and-india-data.p.rapidapi.com/api_india'


# geting and sending response to dialogflow
@app.route('/webhook', methods=['POST'])
@cross_origin()
def webhook():
    req = request.get_json(silent=True, force=True)

    # print("Request:")
    # print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


# processing the request from dialogflow
def processRequest(req):
    log = logger.Log()

    sessionID = req.get('responseId')
    result = req.get("queryResult")
    user_says = result.get("queryText")
    log.write_log(sessionID, "User Says: " + user_says)
    parameters = result.get("parameters")
    r = requests.get(API_URL, headers=HEADERS)
    my_dict = r.json()
    # State and Ut list for which covid 19 confirmed cases are found
    my_list = ['Maharashtra', 'West Bengal', 'Kerala', 'Karnataka', 'Gujarat', 'Delhi', 'Rajasthan', 'Tamil Nadu',
               'Madhya Pradesh', 'Uttar Pradesh', 'Telangana', 'Andhra Pradesh', 'Jammu and Kashmir', 'Haryana',
               'Punjab', 'Bihar', 'Odisha', 'Jharkhand', 'Uttarakhand', 'Himachal Pradesh', 'Himachal Pradesh',
               'Chhattisgarh', 'Assam', 'Chandigarh', 'Ladakh', 'Andaman and Nicobar Islands', 'Meghalaya',
               'Puducherry', 'Goa', 'Manipur', 'Tripura', 'Mizoram', 'Arunachal Pradesh']
    pincode = parameters.get("pin_code")
    data = pd.read_csv('DistrictPinCodeMapping.csv')
    pincode_dict = {}
    j = 0
    # Since from the shape of the data we saw there are 18991 records so we would have max value of j as 18991
    # looping through the pincodes from the Dataframe(named Data)
    for i in data['Pincode']:
        if j < data.shape[0]:
            pincode_dict[i] = data['Districtname'][j]  # getting district names
            j = j + 1
    pincode = int(pincode)
    if len(str(pincode)) != 6:
        return {
            "fulfillmentText": "Invalid pin code"
        }
    #check if pincode is present
    pincode_set = set(pincode_dict.keys())
    if pincode not in pincode_set:
        return {
            "fulfillmentText": "Invalid pin code"
        }
    district = pincode_dict[pincode]
    district = district.title()
    print(district)
    confirmed_data = []
    status = 0
    # the number of active,confirmed,recovered and death cases in India
    active_india = my_dict['total_values']['active']
    confirmed_india = my_dict['total_values']['confirmed']
    recovered_india = my_dict['total_values']['recovered']
    deaths_india = my_dict['total_values']['deaths']
    # Here a is state_wise confirmed data and confirmed_data is confirmed cases list of states
    for i in my_list:
        a = my_dict['state_wise'][i]['district']
        confirmed_data.append(a)

    for i in range(0, len(confirmed_data)):
        a = confirmed_data[i]
        keyset = set(a.keys())
        if district in keyset:
            confirmed = confirmed_data[i][district]['confirmed']
            status = 1
            break
    if status == 0:
        return {
            "fulfillmentText": "District data not found"
        }
    cust_name = parameters.get("cust_name")
    print(cust_name)
    cust_contact = parameters.get("cust_contact")
    cust_email = parameters.get("cust_email")
    # sending email to the customer for the count of cases in district as well as in India
    email_sender = EmailSender()
    template = template_reader.TemplateReader()
    email_message = template.read_info_email_template()
    email_sender.send_email_to_customer(cust_email, email_message, str(confirmed), str(active_india),
                                       str(confirmed_india), str(recovered_india), str(deaths_india))
    return {
        "fulfillmentText": "The count of confirmed cases in your area is: " + str(
            confirmed) + ". We have send  you the count of covid cases in your area and India via Email. " +
                           "Do you have any further queries?"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=True, port=port, host='0.0.0.0')
    #app.run(debug=False, port=port, host='0.0.0.0')
