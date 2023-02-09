# Import necessary libraries
import requests.exceptions
from pyhpeimc.auth import IMCAuth
from pyhpeimc.plat.device import *
import io
import re
import os
import smtplib
from datetime import datetime
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import dotenv_values
import zipfile
import argparse

argParser = argparse.ArgumentParser()
argParser.add_argument("-v", "--verbose", required=False, type=bool, help="python script.py -v True/Flase")
args = argParser.parse_args()
print(args.verbose)
variables = dotenv_values(".env")

zip_arr = []

# Global varibles for the code (Change Here for personalizzation
IMC_HOSTNAME = variables["IMC_HOSTNAME"]
IMC_PROTOCOL = variables["IMC_PROTOCOL"]
IMC_PORT = variables["IMC_PORT"]
IMC_USERNAME = variables["IMC_USERNAME"]
IMC_PASSWORD = variables["IMC_PASSWORD"]

SMTP_SERVER = variables["SMTP_SERVER"]
SMTP_SENDER = variables["SMTP_SENDER"]
SMTP_RECIPIENT = variables["SMTP_RECIPIENT"]
SMTP_SUBJECT = variables["SMTP_SUBJECT"]

LOG_FILE = variables["LOG_FILE"]


# Strip all blank spaces for utility puposes
def strip_blank_lines(s):
    return '\n'.join([line for line in s.split('\n') if line.strip()])


# Helper function that returns mismaching interfaces with the first device in a stack
def compare_dicts(dictarr):
    mismatches_local = {}
    try:
        for s in range(len(dictarr)):
            for i, (interface, configuration) in enumerate(dictarr[0].items()):
                if list(dictarr[s+1].values())[i] != configuration:
                    mismatches_local[list(dictarr[s+1])[i]] = list(set(list(dictarr[s + 1].values())[i]) ^ set(configuration))
    except IndexError:
        pass
    return mismatches_local


# Removes all interfaces not matchin Ten-GigabitEthernet or GigabitEthernet and separates in a self incrementig
# dictionary for scalbility purposes
def switch_separator(r_configuration: dict):
    local_arr = []
    try:
        for r in range(1, int(re.sub(r'\D', '', str(list(r_configuration)[-1]))[0])+1):
            local_dict = {}
            for interface, configuration in r_configuration.items():
                if f'interface Ten-GigabitEthernet{r}/0' in interface or f'interface GigabitEthernet{r}/0' in interface:
                    local_dict[interface] = configuration
            local_arr.append(local_dict)
    except IndexError:
        pass
    return compare_dicts(local_arr)


# Helper function to send an email notification
def send_email(sender, recipient, subject, error_handler: str):
    # Create the email message
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = recipient
    # Condition for preventing empty emails
    if not zip_arr == []:
        content = f"Check the Interfaces with the first Switch in the stack\nDate of Execution: {datetime.now()}\n"
        text = MIMEText(content)
        message.attach(text)
        with open("zipfile.zip", 'rb') as file:
            # Attach the file with filename to the email
            message.attach(MIMEApplication(file.read(), Name='report.zip'))

        # Send the email
        smtp_server = smtplib.SMTP(SMTP_SERVER)
        smtp_server.send_message(message)
        smtp_server.quit()
    elif error_handler == "Error":
        content = f"ERROR IN EXECUTION\nDate of Execution: {datetime.now()}\n"
        text = MIMEText(content)
        message.attach(text)
        smtp_server = smtplib.SMTP(SMTP_SERVER)
        smtp_server.send_message(message)
        smtp_server.quit()
    else:
        content = f"NO MISMATECHS FOUND\nDate of Execution: {datetime.now()}\n"
        text = MIMEText(content)
        message.attach(text)
        smtp_server = smtplib.SMTP(SMTP_SERVER)
        smtp_server.send_message(message)
        smtp_server.quit()


# Helper function to write data for json parsing in the email sender function
def add_wrong_interface(host,  issues):
    report = {
        "Host": host,
        "Wrong Interfaces": issues
    }
    return report


def create_json_file(data, name):
    file_name = f"{name}.json"
    json_file = io.StringIO()
    json.dump(data, json_file, indent=4)
    return file_name, json_file


def create_zip_file(file_names_and_objects):
    zip_file = io.BytesIO()
    with zipfile.ZipFile(zip_file, "w") as zf:
        for file_name, file_obj in file_names_and_objects:
            zf.writestr(file_name, file_obj.getvalue())
    return zip_file


# Helper function to write log file
def log_writer(mismathes, host=None):
    with open(LOG_FILE, "a") as log:
        if mismathes != "No Findings to Report" and mismathes != "Error":
            log.write(f"[{datetime.now()}] [SUCCESS] Address : {host} Wrong Interfaces : {mismathes if mismathes != [] else None}\n")
        elif mismathes == "No Findings to Report":
            log.write(f"[{datetime.now()}] [INFO] Message: {mismathes}\n")
        else:
            log.write(f"[{datetime.now()}] [ERROR] IMCError \n")


def main():
    # Authenticate with the HPE IMC server
    try:
        auth = IMCAuth(f"{IMC_PROTOCOL}://", IMC_HOSTNAME, IMC_PORT, IMC_USERNAME, IMC_PASSWORD)
        devices = get_all_devs(auth, f"{IMC_PROTOCOL}://{IMC_HOSTNAME}:{IMC_PORT}")
        with open("exclusion.txt", "r") as file:
            file = file.readlines()
            for device in devices:
                #for host in file:
                    if device['devCategoryImgSrc'] == "switch" and str(device['label']+"\n") not in file:
                        # Check if the location corrisponds to one in the file and ingore any device with bl in the label
                        if args.verbose:
                            print(f"{datetime.now()} | {str(device['label'])}")
                        config = get_dev_run_config(auth, f"{IMC_PROTOCOL}://{IMC_HOSTNAME}:{IMC_PORT}", devip=str(device['ip']))

                        # Remove blank lines from the device configuration
                        config = strip_blank_lines(config)

                        # Create a file-like object to store the configuration in memory
                        text_io = io.StringIO(config)

                        # Dictionary to store the device configuration as key-value pairs
                        config_dict = {}

                        # Variable to keep track of the current interface being processed
                        current_key = None

                        # Iterate over each line in the configuration
                        for line in text_io:
                            line = line.strip()
                            # If the line starts with "interface", set the current interface
                            if line.startswith("interface"):
                                current_key = line
                                config_dict[current_key] = []
                            # If the line starts with a "#" symbol, the current interface has ended
                            elif line.startswith("#"):
                                current_key = None
                            # If the current interface is not None, add the line to the configuration dictionary
                            elif current_key is not None:
                                if "description" not in line:
                                    config_dict[current_key].append(line)
                        # Checks if the dictionary is not empty to reduce loop times
                        if switch_separator(config_dict) != {}:
                            file_name, json_file = create_json_file(add_wrong_interface(device['ip'], switch_separator(config_dict)), device["label"])
                            zip_arr.append((file_name, json_file))
                            #print(config_dict)
                            log_writer(switch_separator(config_dict), device['ip'])
        # Checks if the data array is empty in case the configuration are all correct for the current pool
        if not zip_arr == []:
            zip_file = create_zip_file(zip_arr)
            with open("zipfile.zip", "wb") as f:
                f.write(zip_file.getvalue())
            send_email(SMTP_SENDER, SMTP_RECIPIENT, SMTP_SUBJECT, error_handler="")
            os.remove("zipfile.zip")
        else:
            log_writer(mismathes="No Findings to Report\n")
            send_email(SMTP_SENDER, SMTP_RECIPIENT, SMTP_SUBJECT, error_handler="")
    except requests.exceptions.ConnectTimeout:
        log_writer(mismathes="Error")
        send_email(SMTP_SENDER, SMTP_RECIPIENT, SMTP_SUBJECT, error_handler="Error")


if __name__ == "__main__":
    main()
