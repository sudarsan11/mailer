
import sys
import os
import logging

from mailer.rules.rules_fetch import RulesFetch
from mailer.actions.actions_handler import GmailActionsHandler
from mailer.search.email_search import EmailSearch

logger = logging.getLogger("mailer.action")
logging.basicConfig(level=logging.INFO)

def is_json_file(filepath):
    _, extension = os.path.splitext(filepath)
    return extension.lower() == '.json'

def initialize(args):
    args = sys.argv[1:]
    rule_config_type, rule_config_value, access_token = args

    if not access_token:
        raise Exception("Missing access token")
    
    allowed_rule_config_types = ['file']
    if rule_config_type not in allowed_rule_config_types or not is_json_file(rule_config_value):
        raise Exception(f"Invalid config type {rule_config_type}, allowed types: {allowed_rule_config_types}")
    

    rules_fetcher = None
    if rule_config_type == 'file':
        rules_fetcher = RulesFetch.read_rules_from_file(rule_config_value)

    resource_fetcher = EmailSearch()
    
    if not rules_fetcher:
        raise Exception("Error initializing rules fetcher service")
    
    return resource_fetcher, rules_fetcher, access_token

def main():

    resource_fetcher, rules_fetcher, access_token = initialize(sys.argv[1])
    handler = GmailActionsHandler(
        resource_fetcher,
        rules_fetcher
    )
    handler.actions_handler(access_token, 'message')
    logger.info("Successfully dispatched actions for messages based on rules")

main()