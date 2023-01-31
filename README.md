# HPE-IMC-Port-Configuration-Monitoring

Monitoring script for HPE IMC to check if HA switch stack is configured correctly

## Usage

    pip install -r requirements.txt

This will install all the required libraries

Remenber to change the following lines to your settings

https://github.com/Dovelus/HPE-IMC-Port-Configuration-Monitoring/blob/5ebb4845aebe5fc990d4749bf515ae1dc9fee8df/HPE_IMC_monitoring.py#L15-L26

The file.txt is the list of monitoring devices that uses that location as key to check in my case you'll see that i excluded all devices that has "BL" in the name you can remove that if you want 
line: https://github.com/Dovelus/HPE-IMC-Port-Configuration-Monitoring/blob/cc1a95f5d8134a3b1d7024fc136de9a5edee1a42/HPE_IMC_monitoring.py#L121
 
