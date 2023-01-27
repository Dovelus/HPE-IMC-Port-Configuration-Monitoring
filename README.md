# HPE-IMC-Port-Configuration-Monitoring

Monitoring script for HPE IMC to check if HA switch stack is configured correctly

## Usage

    pip install -r requirements.txt

This will install all the required libraries

Remenber to change the following lines to your settings

    IMC_HOSTNAME = "localhost"
    IMC_PROTOCOL = "http"
    IMC_PORT = "8080"
    IMC_USERNAME = "username"
    IMC_PASSWORD = "password"
    SMTP_SERVER = "localhost"
    SMTP_SENDER = "test@test.com"
    SMTP_RECIPIENT = "papercut@papercut.com"
    SMTP_SUBJECT = "Mismatched Switch Ports"

The file.txt is the list of monitoring devices that uses that location as key to check in my case you'll see that i excluded all devices that has "BL" in the name you can remove that if you want 
line: (https://github.com/Dovelus/HPE-IMC-Port-Configuration-Monitoring/blob/cc1a95f5d8134a3b1d7024fc136de9a5edee1a42/HPE_IMC_monitoring.py#L121)
 
