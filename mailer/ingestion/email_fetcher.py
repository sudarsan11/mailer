import datetime
import logging
from pydantic import BaseModel, Field, PastDate, FutureDate, EmailStr
from googleapiclient.errors import HttpError


logger = logging.getLogger('mailer.ingestion')

class IngestionInterval(BaseModel):
    start_date: PastDate = Field(default=(datetime.datetime.now() - datetime.timedelta(days=7)).date())
    end_date: FutureDate = Field(default=datetime.datetime.now().date())

class IngestionFilters(BaseModel):
    user_id: EmailStr = Field(default='me')
    max_results: int = Field(default=10)

class GmailFetcher:
    """
    Initialize gmail fetcher using service object
    Arguments:
        gmail_service      ()    -> gmail service object
        user_email         (str) -> user email for which emails will be fetched
        ingestion_interval (IngestionInterval) -> start and end date
        ingestion_filters  (IngestionFilters)  -> filters for fetching emails
    Returns: 
        None
    """
    def __init__(self, gmail_service, user_email=None, ingestion_interval=None, ingestion_filters=None):
        self.gmail_service = gmail_service
        self.user_email = user_email
        self.ingestion_interval = ingestion_interval or IngestionInterval()
        self.ingestion_filters = ingestion_filters or IngestionFilters()
        self.resources = []

    """
    To fetch system and user labels before fetching messages
    Arguments:
        None
    Returns: 
        labels -> (list of dict) -> Email message labels created by system and user
    """
    def fetch_labels(self):
        try:
            labels = self.gmail_service.users().labels().list(
                userId=self.user_email or self.ingestion_filters.user_id,
            ).execute()
            logger.info(f"Fetched message labels for {self.user_email}")
            return labels
        except HttpError as error:
            logger.error(f"Failed to fetch labels: {error}")

    """
    To construct filters for fetching messages
    Arguments:
        None
    Returns: 
        query_params -> (str) -> Space separated query params for fetching messages
    """
    def construct_message_filters(self):
        query_params = []
        query_param_map = {
            'start_date': 'after',
            'end_date': 'before'
        }
        for field, value in iter(self.ingestion_interval):
            param_str = f"{query_param_map[field]}:{value}"
            query_params.append(param_str)

        return " ".join(query_params)
    
    """
    Google's batch request requires a callback function
    Arguments:
        request_id -> () -> request id for the resource in the batch for which the callback is invoked
        response   -> () -> response in for the resource the batch for which the callback is invoked
        exception  -> () -> exceptions if any
    Returns: 
        None
    """
    def batch_request_callback(self, request_id, response, exception):
        if exception:
            logger.error(f"Failed to fetch resource : {request_id} {exception}")
        
        self.resources.append(response)

    """
    Construct a batch request for messages and executes them
    Arguments:
        message_ids -> (list) -> message ids fetched during list messages
    Returns: 
        None
    """
    def get_message_in_batch(self, message_ids):
        batch_request = self.gmail_service.new_batch_http_request()
        logger.info("Fetching messages in batch from gmail api, please wait....")
        for message_id in message_ids:
            batch_request.add(
                self.gmail_service.users().messages().get(
                    userId=self.user_email or self.ingestion_filters.user_id,
                    id=message_id
                ), 
                callback=self.batch_request_callback
            )                
        batch_request.execute()
        
    """
    Generator function which fetches paginated results of messages, it has only message and thread ids
    Arguments:
        None
    Returns: 
        resources -> (list) -> yields list of paginated resources
    """
    def fetch_messages(self):
        next_page_token = None
        page_num = 1
        while True:
            try:
                query_params = self.construct_message_filters()
                response = self.gmail_service.users().messages().list(
                    userId=self.user_email or self.ingestion_filters.user_id,
                    q=query_params, 
                    maxResults=self.ingestion_filters.max_results,
                    pageToken=next_page_token 
                ).execute()
                next_page_token = response.get('nextPageToken')
                messages = response.get('messages', [])
                message_ids = [message['id'] for message in messages]

                self.get_message_in_batch(message_ids)
                logger.info(f"Fetched message batch page {page_num} with {len(message_ids)} messages")
                page_num += 1
                yield self.resources
                self.resources = []

                if not next_page_token:
                    break

            except HttpError as error:
                logger.error(f"Failed to fetch labels: {error}")

        return self.resources
