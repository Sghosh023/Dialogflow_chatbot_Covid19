class TemplateReader:
    def __init__(self):
        pass

    def read_info_email_template(self):
        try:
            email_file = open("email_templates/Covid_19_Info_Template.html", "r")
            email_message = email_file.read()
            #email_message.replace('confirmed', confirmed)
            return email_message
        except Exception as e:
            print('The exception is '+str(e))
