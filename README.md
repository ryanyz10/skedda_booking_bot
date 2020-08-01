# Skedda Booking Bot
## About
The tennis courts in my neighborhood are booked using a site called Skedda. Skedda opens bookings exactly 7 days in advance, meaning if I want to the prime times between 7-8pm, I need to get on a week before exactly at 7pm. This can get tedious and difficult to remember so I wrote this bot to do it for me.

It is deployed as an AWS Lambda function triggered by a cron job.

Big thanks to the [PyChromeless](https://github.com/21Buttons/pychromeless) repo for help in getting the Lambda Docker image setup for a webscraper.

## Running
First, make sure to install the dependencies with `pip3 install -r requirements.txt`. 

Also make sure you have Docker installed locally.

Run `make docker-run` to run the Lambda function locally, and `make build-lambda-package` to create a zip file to upload to AWS.