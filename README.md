# mailer
A simple service for populating emails using gmail api and taking actions on it using rules

:gear: Requirements
-------------------
- Python 3.10.8 and Postgres 14.11 to be installed and postgres running at port 5432
- Create venv and pip install the requirements.txt

:rocket: Quick Setup
--------------------
Install postgres and create database with following configs
```
sudo apt-get install libpq-dev
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install postgresql postgresql-contrib -f -y
psql -U postgres
create database happyfox;
```
Create a virtual environment and install requirements
```
python -m venv venv; source venv/bin/activate; pip install -r requirements.txt
```
Set the pythonpath
```
export PYTHONPATH="${PYTHONPATH}:."
```
Get oauth credentials for running populate script
```
You can get the oauth credentials from api console 
 https://console.developers.google.com/
Follow this to create an Oauth app and get the credentials with scope gmail
 https://developers.google.com/workspace/guides/create-credentials#desktop-app

```
Run populate script
```
python mailer/populate.py {user_id} {auth_config_option} {auth_config_value}

{user_id} -> email address
{config_option} -> cli or file
{config_value}
    CLI
        { "token": "{token}", "refresh_token": "{refresh_token}", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "{client_id}", "client_secret": "{client_id}", "scopes": [ "https://www.googleapis.com/auth/gmail.readonly" ], "universe_domain": "googleapis.com", "account": "", "expiry": "" }
    File
        filepath to credentials.json
```
Get access token from Google client
```
You can get the oauth access token from Oauth playground. Select gmail api with corresponding scope and exchange
grant code for access token
 https://developers.google.com/oauthplayground
```
Run action script
```
python mailer/action.py {config_option} {config_value} {access_token}
{config_option} -> file
{config_value} -> filepath to rules json
{access_token} -> access token we got in previous step
```