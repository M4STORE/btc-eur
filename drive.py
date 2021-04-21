import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import json
import time

class GoogleDriveClass:
    def __init__(self, *args):
        self.drive = None
        self.all_data = ""
        self.check_result = False
        self.teleg_alerts_dict = {}

        self.authentication()

    def authentication(self):
        gauth = GoogleAuth()
        # Try to load saved client credentials
        gauth.LoadCredentialsFile("mycreds.txt")
        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()
        # Save the current credentials to a file
        gauth.SaveCredentialsFile("mycreds.txt")

        self.drive = GoogleDrive(gauth)

    def upload_file_to_root_dir(self, filename):
        to_upload = self.drive.CreateFile()
        to_upload.SetContentFile(filename)   # local file to be uploaded
        to_upload.Upload()


    def search_file(self, name, folder_id = None, is_folder = None):
        name = str(name)
        if is_folder == None:
            is_folder = False

        if folder_id == None:
            folder_id = "root"

        if is_folder == False and ".txt" not in name:
            name += ".txt"
        else:
            pass

        try:
            file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

            for file1 in file_list:
                # print('title: %s, id: %s' % (file1['title'], file1['id']))
                if file1['title'] == name:
                    return file1['id']

            for file1 in file_list:
                if file1['mimeType'] == 'application/vnd.google-apps.folder':
                    if self.search_file(name, file1['id'], is_folder) != None:
                        return self.search_file(name, file1['id'], is_folder)

            return None  # if file is not found and there are no more folders
        except:
            # print("Error while searching file")
            return None  #if there is an error
            pass

    def search_file_name(self, file_id, folder_id = None, is_folder = None):
        file_id = str(file_id)
        if is_folder == None:
            is_folder = False

        if folder_id == None:
            folder_id = "root"
        try:
            file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

            for file1 in file_list:
                # print('title: %s, id: %s' % (file1['title'], file1['id']))
                if file1['id'] == file_id:
                    return file1['title']

            for file1 in file_list:
                if file1['mimeType'] == 'application/vnd.google-apps.folder':
                    if self.search_file_name(file_id, file1['id'], is_folder) != None:
                        return self.search_file_name(file_id, file1['id'], is_folder)

            return None  # if file is not found and there are no more folders
        except:
            # print("Error while searching file")
            return None
            pass

    def read_file(self, filename):  # just like a download but it only opens it
        try:
            file_id = self.search_file(filename)  # not a folder

            gfile = self.drive.CreateFile({'id': file_id})
            gfile.GetContentFile(file_id)

            return gfile.GetContentString()
        except:
            # print("Couldn't read file or file doesn't exist")
            return None
            pass

    def delete_file(self, filename, folder_id = None):

        id_to_delete = self.search_file(filename, folder_id)
        folder = False

        if id_to_delete == None:  # might be a folder
            id_to_delete = self.search_file(filename, folder_id, True)
            folder = True
            if id_to_delete == None:
                return "Couldn't find file or folder with that name"

        to_delete = self.drive.CreateFile({'id': id_to_delete})

        to_delete.Trash()  # not permanently

        if folder == True:
            return "Folder deleted"
        return "File deleted"

    def create_new_folder(self, chat_id, folder_name = None):
        if folder_name == None:
            folder_name = chat_id

        folder = self.drive.CreateFile({'title': f"{folder_name}", 'mimeType': 'application/vnd.google-apps.folder'})
        folder.Upload()

    def create_folder_in_folder(self, chat_id, mother_folder_name, son_folder_name):
        mother_id = self.search_file(mother_folder_name, chat_id, True)  # can't allow to create folders to other users folders

        f = self.drive.CreateFile({'title': son_folder_name, 'mimeType': 'application/vnd.google-apps.folder', "parents": [{"kind": "drive#fileLink", "id": mother_id}]})
        f.Upload()

    def upload_to_folder(self, filename, foldername):
        folder_id = self.search_file(foldername, None, True)

        if foldername == "Root" or foldername == "root":
            self.upload_file_to_root_dir(filename)
        else:
            f = self.drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder_id}]})
            f.SetContentFile(filename)
            f.Upload()

    def create_file(self, filename, directory):
        with open(f"{filename}.txt", "w") as file:
            temp_dict = {}
            json.dump(temp_dict, file)

        self.upload_to_folder(f"{filename}.txt", directory)

    def add_data(self, file_id, dir_id, email, phone_number):
        filename = self.search_file_name(file_id)

        dirname = self.search_file_name(dir_id, None, True)

        file_content = self.read_file(filename)

        if file_content == "{}":
            data_dict = {}
        else:
            data_dict = json.loads(file_content)

        if str(email) in data_dict:
            del data_dict[str(email)]

        data_dict.setdefault(email, [])

        data_dict[email].append(phone_number)

        data_dict[email].append("online")


        new_name = self.create_local_file(filename, data_dict)

        self.delete_file(filename, dir_id)

        self.upload_to_folder(new_name, dirname)

    def collect_all_data(self, user_id):
        try:
            file_list = self.drive.ListFile({'q': f"'{str(user_id)}' in parents and trashed=false"}).GetList()

            for file1 in file_list:
                # print('title: %s, id: %s' % (file1['title'], file1['id']))
                if file1['mimeType'] == "text/plain":

                    self.all_data += (f"'{str(file1['title'])}'" + "\n\n")

                    file_content = self.read_file(file1['title'])

                    if file_content != "{}":
                        data_dict = json.loads(file_content)

                        for key, value in data_dict.items():
                            self.all_data += f"{key}\n{value[0]}: {value[1]}\n\n"

            for file1 in file_list:
                if file1['mimeType'] == 'application/vnd.google-apps.folder':
                    self.all_data += ("\n\n" + str(file1['title']).upper() + "\n\n")
                    self.collect_all_data(file1['id'])


            return self.all_data  # if file is not found and there are no more folders
        except Exception as e:
            #print(e)
            # print("Error while searching file")
            return "Couldn't collect data"  #if there is an error
            #pass

    def create_local_file(self, filename, data):
        new_name = f"{filename}"

        with open(new_name, "w") as file:
            json.dump(data, file)

        return new_name

    def change_phonenumber_state(self, phonenumber, file_id, dir_id):
        filename = self.search_file_name(file_id)

        dirname = self.search_file_name(dir_id, None, True)

        file_content = self.read_file(filename)

        if file_content == "{}":
            return "No content in that file"
        else:
            data_dict = json.loads(file_content)

            found = False

            for key, value in data_dict.items():
                if value[0] == str(phonenumber):
                    if value[1] == "working":
                        new_state = "deleted"
                        curr_time = str(int(time.time()))
                        value[1] = f"deleted: {curr_time}"
                    elif value[1] == "online":
                        new_state = "working"
                        value[1] = "working"
                    else:
                        new_state = "online"
                        value[1] = "online"
                    found = True
        if not found:
            return "Phone number not found"

        new_name = self.create_local_file(filename, data_dict)

        self.delete_file(filename, dir_id)

        self.upload_to_folder(new_name, dirname)

        return f"Phone state of number {phonenumber} changed to {new_state}"

    def add_to_alert_dict(self, alert_file_id, key, value, eventual_email = None):
        alert_filename = self.search_file_name(alert_file_id)

        file_content = self.read_file(alert_filename)

        if file_content == "{}":
            alert_dict = {}

            if eventual_email != None:
                alert_dict.setdefault(key, [])
                alert_dict[key].append(value)
                alert_dict[key].append(eventual_email)
            else:
                alert_dict[key] = value
        else:
            alert_dict = json.loads(file_content)

            if eventual_email != None:
                if str(key) in alert_dict.keys():
                    del alert_dict[str(key)]

                    alert_dict.setdefault(key, [])
                    alert_dict[key].append(value)
                    alert_dict[key].append(eventual_email)
            else:
                if str(key) in alert_dict.keys():
                    del alert_dict[str(key)]

                    alert_dict[key] = value

        new_name = self.create_local_file(alert_filename, alert_dict)

        self.delete_file(str(alert_filename), "root")

        self.upload_file_to_root_dir(str(new_name))

    def delete_record(self, data, type, file_id, dir_id):
        filename = self.search_file_name(file_id)
        dirname = self.search_file_name(dir_id, None, True)

        file_content = self.read_file(filename)

        if file_content == "{}":
            data_dict = {}
        else:
            data_dict = json.loads(file_content)


        if str(type) == "email":
            try:
                del data_dict[str(data)]
                to_return = "Data deleted"
            except:
                return "Couldn't find that email"
        elif str(type) == "phonenumber":
            found = False
            for key, value in data_dict.items():
                if value[0] == str(data):
                    found = True
                    to_return = "Data deleted"
                    break

            del data_dict[str(key)]

            if not found:
                to_return = "Couldn't find that phonenumber"

        new_name = self.create_local_file(filename, data_dict)

        self.delete_file(filename, dir_id)

        self.upload_to_folder(new_name, dirname)

        return to_return

    def bot_task_check(self):
        self.teleg_alerts_dict = {}

        file_list = self.drive.ListFile({'q': f"'root' in parents and trashed=false"}).GetList()

        for file1 in file_list:
            if file1['mimeType'] == 'application/vnd.google-apps.folder':
                user = file1['title']

                user_id = file1['id']

                message = self.find_bot_data(user_id, "root/")

                while self.check_result == True:

                    self.send_alert(user, message)

                    message = self.find_bot_data(user_id, "root/")

        return self.teleg_alerts_dict

    def get_server_bot_key(self):
        with open("bot_reserved_data.txt", "r") as file:
            sender_address = file.readline()
            sender_pass = file.readline()

        return sender_address, sender_pass

    def send_alert(self, user, message):
        alert_file_id = self.search_file("alert")

        alert_filename = self.search_file_name(alert_file_id)

        file_content = self.read_file(alert_filename)

        if file_content == "{}":  # can't actually be void
            return
        else:
            alert_dict = json.loads(file_content)

            for key, value in alert_dict.items():
                if str(key) == str(user):
                    if isinstance(value, list):
                        if value[0] == 1:
                            self.send_email_alert(str(user), value[1], message)
                        else:  # value[0] == 3
                            self.send_email_alert(str(user), value[1], message)
                            self.send_telegram_alert(str(user), message)
                    else:
                        if value == 2:
                            self.send_telegram_alert(str(user), message)
                    break


    def send_email_alert(self, user, email, message):
        sender_address, sender_pass = self.get_server_bot_key()

        str_email_subject = "Recreate your account"

        str_send_email = f"Hi, you can recreate the phone number at folder {message}"

        # preparing session
        session = smtplib.SMTP('smtp.gmail.com',
                               587)  # use gmail with port    IT IS ALWAYS THE SAME BECAUSE THIS ARE THE SENDER DATA
        session.starttls()  # enable security
        session.login(sender_address,
                      sender_pass)  # login with mail_id and password WHICH ARE GLOBAL (don't need to pass them in function)

        # preparing message
        message = MIMEMultipart()

        message['Subject'] = str_email_subject  # The subject line



        message.attach(MIMEText(str_send_email, 'plain'))

        text = message.as_string()
        session.sendmail(sender_address, email, text)

        # logout from sender address
        session.quit()

    def send_telegram_alert(self, chat_id, message):
        self.teleg_alerts_dict[str(message)] = chat_id

    def find_bot_data(self, user_id, in_folder):
        try:
            file_list = self.drive.ListFile({'q': f"'{str(user_id)}' in parents and trashed=false"}).GetList()

            for file1 in file_list:
                # print('title: %s, id: %s' % (file1['title'], file1['id']))
                if file1['mimeType'] == "text/plain":

                    in_folder += (f"{str(file1['title'])}/" + "\n\n")

                    file_content = self.read_file(file1['title'])

                    if file_content != "{}":
                        data_dict = json.loads(file_content)

                        for key, value in data_dict.items():
                            if "deleted" in value[1]:
                                if time.time() - int(value[1].split("deleted: ")[1]) > 172800:   # seconds in two days
                                    in_folder += f"email: {key}\nphonenumber: {value[0]}\n"

                                    value[1] = "online"

                                    new_name = self.create_local_file(file1['title'], data_dict)

                                    self.delete_file(file1['title'], str(user_id))

                                    self.upload_to_folder(new_name, str(self.search_file_name(str(user_id), None, True)))

                                    self.check_result = True
                                    return in_folder
                            else:
                                self.check_result = False
                    else:
                        self.check_result = False


            for file1 in file_list:
                if file1['mimeType'] == 'application/vnd.google-apps.folder':
                    in_folder += (f"{str(file1['title'])}/" + "\n\n")

                    msg = self.find_bot_data(file1['id'], in_folder)

                    if self.check_result:
                        return msg
                    else:
                        pass  # if file is not found and there are no more folders
            return ""
        except Exception as e:
            # print(e)
            # print("Error while searching file")
            return ""  # if there is an error
            # pass