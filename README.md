# HPE-IMC-Port-Configuration-Monitoring

Monitoring script for HPE IMC to check if HA switch stack is configured correctly

## Usage:

    pip install -r requirements.txt
    
This will install all the required libraries

## Execution:
    
    python  HPE_IMC_monitoring.py -v True (Verbose mode on)
    python  HPE_IMC_monitoring.py (Verbose mode off)


### The exclusion.txt file is the list of devices to ignore based on their label

Remenber to create a .env file with the varibles values with the following names

https://github.com/Dovelus/HPE-IMC-Port-Configuration-Monitoring/blob/52a7d49498ce3bfde67d7083c9a9343f269a5190/HPE_IMC_monitoring.py#L27-L38
