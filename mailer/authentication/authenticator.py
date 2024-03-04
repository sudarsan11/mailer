from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import logging
logger = logging.getLogger('mailer.google_auth')
logger.setLevel(logging.INFO)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class GoogleAuthenticator():

    @staticmethod
    def refresh_token(credentials, SCOPES):
        logger.info("Refreshing credentials")
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
        credentials = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(credentials.to_json())

    @classmethod
    def from_file(cls, file_path, service_name='gmail', version='v1'):
        
        credentials = Credentials.from_authorized_user_file(file_path, cls.SCOPES)
        if not credentials or not credentials.valid:
            cls.refresh_token(credentials, cls.SCOPES)

        return cls.init_service(credentials, service_name, version)

    @classmethod
    def from_config(cls, config, service_name='gmail', version='v1'):
        credentials = Credentials.from_authorized_user_info(info=config)

        if not credentials or not credentials.valid:
            cls.refresh_token(credentials, cls.SCOPES)

        return cls.init_service(credentials, service_name, version)

    @classmethod
    def init_service(cls, credentials, service_name, version):
        try:
            service =  build(service_name, version, credentials=credentials)
            logger.info("Service initialized")
            return service
        except HttpError as error:
            logger.error(f"Error initalizing service: {error}")
