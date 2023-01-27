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

 
