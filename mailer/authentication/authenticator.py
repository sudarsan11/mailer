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

    """
    Method to fetch access token using refresh token if it expires
    and saves it to credentials.json

    Arguments:
        credentials (dict) -> google credentials object
        SCOPES      (list) -> Scope of the gmail service (read only, write only etc)
    Returns: 
        None
    """
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

    """
    Alternative constructor for reading credentials from json file
    Arguments:
        file_path    (str) -> local file path to credentials file
        service_name (str) -> google service name
        version      (str) -> api version to use
    Returns: 
        service_object () -> gmail service object
    """
    @classmethod
    def from_file(cls, file_path, service_name='gmail', version='v1'):
        
        credentials = Credentials.from_authorized_user_file(file_path, cls.SCOPES)
        if not credentials or not credentials.valid:
            cls.refresh_token(credentials, cls.SCOPES)

        return cls.init_service(credentials, service_name, version)
    
    """
    Alternative constructor for reading credentials from cli
    Arguments:
        config       (dict) -> dict of credentials with token, refresh token, expiry etc
        service_name (str)  -> google service name
        version      (str)  -> api version to use
    Returns: 
        service_object () -> gmail service object
    """
    @classmethod
    def from_config(cls, config, service_name='gmail', version='v1'):
        credentials = Credentials.from_authorized_user_info(info=config)
        return cls.init_service(credentials, service_name, version)

    """
    Initialize and return service object using credentials
    Arguments:
        credentials  (dict) -> dict of credentials with token, refresh token, expiry etc
        service_name (str)  -> google service name
        version      (str)  -> api version to use
    Returns: 
        service_object () -> gmail service object
    """
    @classmethod
    def init_service(cls, credentials, service_name, version):
        try:
            service =  build(service_name, version, credentials=credentials)
            logger.info("Service initialized")
            return service
        except HttpError as error:
            logger.error(f"Error initalizing service: {error}")
