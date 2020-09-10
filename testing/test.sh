#!/bin/sh
set -e
cd ./assets
BR_YELLOW='\e[0;93m'
RESET='\e[0m'

echo -e "${BR_YELLOW}Testing out sunny day...${RESET}"
./out / < ../testing/content.json
echo -e

echo -e "${BR_YELLOW}Testing in sunny day...${RESET}"
./in / < ../testing/content.json
echo -e

echo -e "${BR_YELLOW}Testing check sunny day...${RESET}"
./check / < ../testing/content.json
echo -e

echo -e "${BR_YELLOW}Testing out bad config...${RESET}"
if ./out / < ../testing/bad-config.json ; then
	false
else
	true
fi
echo -e

echo -e "${BR_YELLOW}Testing out bad url...${RESET}"
if ./out / < ../testing/bad-url.json ; then
	false
else
	true
fi
echo -e
