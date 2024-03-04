

import json
import logging
from mailer.utils.api_requests import APIRequest
from requests.exceptions import HTTPError

logger = logging.getLogger('mailer.actions_handler')

class GmailActionsHandler:

    def __init__(self, resource_fetcher, rules_fetcher):
        self.resource_fetcher = resource_fetcher
        self.rules_fetcher = rules_fetcher
        self.api_requests = APIRequest('https://www.googleapis.com/batch/gmail/v1')

    def construct_batch_request(self, request_configs, boundary='batch_boundary'):

        logger.info(f"Constructing batch request for actions")
        batch_request_body = ''
        for idx, config in enumerate(request_configs):
            endpoint, request_body = config['endpoint'], config['body']
            batch_request_body += (
                f'--{boundary}\r\n'
                f'Content-Type: application/http\r\n'
                f'Content-ID: <item{idx}>\r\n\r\n'
                f'POST {endpoint} HTTP/1.1\r\n'
                f'Content-Type: application/json\r\n\r\n'
                f'{json.dumps(request_body)}\r\n'
            )
        
        batch_request_body += f'--{boundary}--'
        return batch_request_body
    
    def add_label_to_messages(self, label, message_ids, access_token):
        request_configs = []
        for message_id in message_ids:
            request_configs.append(
                {
                    'endpoint': f'/gmail/v1/users/me/messages/{message_id}/modify',
                    'body': {"addLabelIds": [label]}
                }
            )
        payload = self.construct_batch_request(request_configs)
        try:
            headers = {
                "Content-Type": f"multipart/mixed; boundary=batch_boundary",
                "Authorization": f"Bearer {access_token}"
            }
            res = self.api_requests.post(headers=headers, data=payload)
            logger.info(f"Added label {label} from messages")
            logger.debug(res)
        except HTTPError as err:
            logger.error(err)

    def remove_label_from_messages(self, label, message_ids, access_token):
        request_configs = []
        for message_id in message_ids:
            request_configs.append(
                {
                    'endpoint': f'/gmail/v1/users/me/messages/{message_id}/modify',
                    'body': {"removeLabelIds": [label]}
                }
            )
        payload = self.construct_batch_request(request_configs)
        try:
            headers = {
                "Content-Type": f"multipart/mixed; boundary=batch_boundary",
                "Authorization": f"Bearer {access_token}"
            }
            res = self.api_requests.post(headers=headers, data=payload)
            logger.info(f"Removed label {label} from messages")
            logger.debug(res)
        except HTTPError as err:
            logger.error(err)
    
    def actions_dispatcher(self, actions, **kwargs):
        attribute_action_map = {
            'message': {
                'move': {
                    'inbox': (
                        self.add_label_to_messages, 
                        {'label': 'INBOX', 'message_ids': kwargs.get('message_ids'), 'access_token': kwargs.get('access_token')}
                    )
                },
                'mark': {
                    'read': (
                        self.remove_label_from_messages, 
                        {'label': 'UNREAD', 'message_ids': kwargs.get('message_ids'), 'access_token': kwargs.get('access_token')}
                    ),
                    'unread': (
                        self.add_label_to_messages, 
                        {'label': 'UNREAD', 'message_ids': kwargs.get('message_ids'), 'access_token': kwargs.get('access_token')}
                    ),
                }
            }
        }

        for action in actions:
            func, params = attribute_action_map[action.attribute][action.name][action.value]
            logger.info(f"Disptching action for {action.name}")
            func(**params)

    def actions_handler(self, access_token, resource_type):
        
        rules, actions = self.rules_fetcher.construct_rules()
        resources = self.resource_fetcher.fetch(resource_type, rules)
        resource_args_map = {
            'message': {'message_ids': resources}
        }
        self.actions_dispatcher(actions, access_token=access_token, **resource_args_map[resource_type])
