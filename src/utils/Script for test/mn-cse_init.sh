#!/bin/bash


#Script arguments
me=${0##*/}
if [ $# -ne 3 ]; then
  echo "Usage: $me <IP Address> <Port #> <CSE name>"
  exit 1
fi

# Turn on verbose and echo.
set -vx

#Set parameters
IPADDRESS=$1
PORT=$2
CSE=$3

FIRST_HEADER="Content-Type: application/vnd.onem2m-res+json"

# Create an ADN-AE1
echo
echo ----------Create ADN-AE1
curl -i -X POST $IPADDRESS:$PORT/$CSE -H "$FIRST_HEADER" -H "X-M2M-RI: req001"  -d @payloadAe_01.json

# Create an ADN-AE2
echo
echo ----------Create ADN-AE2
curl -i -X POST $IPADDRESS:$PORT/$CSE -H "$FIRST_HEADER" -H "X-M2M-RI: req002" -d @payloadAe_02.json

# Create an MN-AE
echo
echo ----------Create MN-AE
curl -i -X POST $IPADDRESS:$PORT/$CSE -H "$FIRST_HEADER" -H "X-M2M-RI: req003" -d @payloadAe_03.json



# Create a container under AE1
echo
echo ----------Create container under ADN-AE1
curl -i -X POST $IPADDRESS:$PORT/$CSE/light_ae1 -H "$FIRST_HEADER" -H "X-M2M-RI: req005" -d @payloadContainer_01.json

# Create a container under AE2
echo
echo ----------Create container under ADN-AE2
curl -i -X POST http://$IPADDRESS:$PORT/$CSE/light_ae2 -H "$FIRST_HEADER" -H "X-M2M-RI: req006" -d @payloadContainer_02.json


# Create a content instance under Light of AE1
echo
echo ----------Create content instance under Light of AE1
curl -i -X POST http://$IPADDRESS:$PORT/$CSE/light_ae1/light -H "$FIRST_HEADER" -H "X-M2M-RI: req007" -d @payloadCI_init.json

# Create a content instance under Light of AE2
echo
echo ----------Create content instance under Light of AE2
curl -i -X POST http://$IPADDRESS:$PORT/$CSE/light_ae2/light -H "$FIRST_HEADER" -H "X-M2M-RI: req008"  -d @payloadCI_init.json

