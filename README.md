# AWS EC2 Instance Manager

This Python Django web application allows users to start AWS EC2 instances using a simple UI. The purpose of the application is to enable people to view hobby projects I have created and deployed on AWS infrastructure, without incurring costs while they're idling.

The application uses the boto3 library to manage AWS resources.  The data is stored in a Dockerised PostgreSQL database.

## Local Development Setup

Clone the repository and create a `.env` file to store environment variables for the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY. 

### Install libraries

`cd` into the root directory and run `pip install -r requirements.txt` .

### Create local database
`cd` into the root directory and run `docker-compose up`.

Run the database migrations by executing the following from the root directory:
```
python manage.py makemigrations ec2_starter --empty
python manage.py makemigrations
python manage.py migrate
```

Open the application with an IDE (such as PyCharm) 

In addition to the Django Server run configuration, create a separate Python run configuration with the following values:
```
Name: Celery Worker
Interpreter: Python 3.13
Script: -m
Script parameters: celery -A instance_starter worker --pool=solo -l INFO
Working directory: the project root
```
Finally, create a Compound Run Configuration and add the Django Server and Celery Worker run configs.

Run the compound run configuration. The URL is available at `http://localhost:8000`
