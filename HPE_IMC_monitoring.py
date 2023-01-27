# Import necessary libraries
from pyhpeimc.auth import IMCAuth
from pyhpeimc.plat.device import *
import io
import re
import smtplib
from datetime import datetime
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

data = []

# Global varibles for the code (Change Here for personalizzation
IMC_HOSTNAME = "localhost"
IMC_PROTOCOL = "http"
IMC_PORT = "8080"
IMC_USERNAME = "username"
IMC_PASSWORD = "password"

SMTP_SERVER = "localhost"
SMTP_SENDER = "test@test.com"
SMTP_RECIPIENT = "papercut@papercut.com"
SMTP_SUBJECT = "Mismatched Switch Ports"

LOG_FILE = "IMCMonitoring.log"


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
                    mismatches_local[list(dictarr[s+1])[i]] = list(dictarr[s+1].values())[i]
    except IndexError:
        pass
    return mismatches_local


# Removes all interfaces not matchin Ten-GigabitEthernet or GigabitEthernet and separates in a self incrementig
# dictionary for scalbility purposes
def switch_separator(r_configuration: dict):
    local_arr = []
    for r in range(1, int(re.sub(r'\D', '', str(list(r_configuration)[-1]))[0])+1):
        local_dict = {}
        for interface, configuration in r_configuration.items():
            if f'interface Ten-GigabitEthernet{r}/0' in interface or f'interface GigabitEthernet{r}/0' in interface:
                local_dict[interface] = configuration
        local_arr.append(local_dict)
    return compare_dicts(local_arr)


# Helper function to send an email notification
def send_email(sender, recipient, subject):
    # Create the email message
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = recipient
    # Condition for preventing empty emails
    if not data == []:
        content = f"Check the Interfaces with the first Switch in the stack\nDate of Execution: {datetime.now()}\n"
        text = MIMEText(content)
        message.attach(text)
        # Convert the list to a json string
        json_data = json.dumps(data, indent=2)
        # Attach the json file
        json_file = MIMEText(json_data, _subtype='json')
        json_file.add_header('Content-Disposition', 'attachment', filename='report.json')
        message.attach(json_file)

        # Send the email
        smtp_server = smtplib.SMTP(SMTP_SERVER)
        smtp_server.send_message(message)
        smtp_server.quit()
    else:
        content = f"NO MISMATCHES FOUND\nDate of Execution: {datetime.now()}\n"
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
    data.append(report)
    return data


# Helper function to write log file
def log_writer(mismathes, host=None):
    with open(LOG_FILE, "a") as log:
        if mismathes != "No Findings to Report":
            log.write(f"[{datetime.now()}]  Address : {host} Wrong Interfaces : {mismathes if mismathes != [] else None}\n")
        else:
            log.write(f"[{datetime.now()}]  Message: {mismathes}\n")


def main():
    # Authenticate with the HPE IMC server
    auth = IMCAuth(f"{IMC_PROTOCOL}://", IMC_HOSTNAME, IMC_PORT, IMC_USERNAME, IMC_PASSWORD)
    devices = get_all_devs(auth, f"{IMC_PROTOCOL}://{IMC_HOSTNAME}:{IMC_PORT}")
    with open("file.txt", "r") as file:
        file = file.readlines()
        for device in devices:
            if device['devCategoryImgSrc'] == "switch":
                for host in file:
                    # Check if the location corrisponds to one in the file and ingore any device with bl in the label
                    if host.strip("\n") in str(device['location']).lower() and "bl" not in str(device['label']).lower():
                        config = get_dev_run_config(auth, f"{IMC_PROTOCOL}://{IMC_HOSTNAME}:{IMC_PORT}",
                                                    devip=str(device['ip']))

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
                            add_wrong_interface(device['ip'], switch_separator(config_dict))
                            log_writer(switch_separator(config_dict), device['ip'])
    # Checks if the data array is empty in case the configuration are all correct for the current pool
    if not data == []:
        send_email(SMTP_SENDER, SMTP_RECIPIENT, SMTP_SUBJECT)
    else:
        log_writer(mismathes="No Findings to Report\n")
        send_email(SMTP_SENDER, SMTP_RECIPIENT, SMTP_SUBJECT)


if __name__ == "__main__":
    main()
