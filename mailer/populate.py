
import sys
import json
import datetime
import logging

from mailer.authentication.authenticator import GoogleAuthenticator
from mailer.ingestion.email_fetcher import GmailFetcher, IngestionInterval
from mailer.ingestion.email_message_processor import GmailMessageProcessor

logger = logging.getLogger("mailer.populate")
logging.basicConfig(level=logging.INFO)

def initialize(args):
    args = sys.argv[1:]
    user_email, config_type, config_value = args
    
    allowed_config_types = ['cli', 'file']
    if config_type not in allowed_config_types:
        raise Exception(f"Invalid config type {config_type}, allowed types: {allowed_config_types}")

    gmail_service = None
    if config_type == 'cli':
        gmail_service = GoogleAuthenticator().from_config(json.loads(config_value))
    elif config_type == 'file':
        gmail_service = GoogleAuthenticator().from_file(config_value)
    
    if not gmail_service:
        raise Exception("Error initializing gmail service")
    
    return user_email, gmail_service

def main():

    user_email, gmail_service = initialize(sys.argv[1])
    ingestion = GmailFetcher(
        gmail_service,
        user_email,
        IngestionInterval(
            start_date=(datetime.datetime.now() - datetime.timedelta(days=1)).date(),
        )
    )

    # Register sender
    recipient = GmailMessageProcessor.register_recipient(user_email)

    # Updating user and system labels
    message_labels = ingestion.fetch_labels()
    GmailMessageProcessor.create_labels(recipient, message_labels)

    # Processing messages
    for message_batch in ingestion.fetch_messages():
        GmailMessageProcessor.process_messages(message_batch)

    logger.info("Successfully populated messages in db")

main()