import os
import logging
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

from datetime import datetime
from django.db import transaction
from db.models import Message, User, UserMessage, Label, MessageHeaderValues
logger = logging.getLogger('mailer.gmail_message_processor')
logger.setLevel(logging.INFO)

class GmailMessageProcessor:
    recipient = None
    @classmethod
    def process_messages(cls, messages_data):
        with transaction.atomic():
            cls.create_senders(messages_data)
            cls.create_messages(messages_data)

            # Bulk create is not returning pk, need to check why. Filtering as a hack
            created_messages = Message.objects.filter(message_id__in=[message_data['id'] for message_data in messages_data])

            cls.create_message_labels(created_messages, messages_data)
            cls.create_user_messages(created_messages, messages_data) 
            cls.create_message_headers(created_messages, messages_data)
    
    @classmethod
    def register_recipient(cls, recipient_email):
        cls.recipient, _ = User.objects.get_or_create(email=recipient_email, username=recipient_email)
        logger.info(f"Registered recipient {cls.recipient.email}")
        return cls.recipient

    @classmethod
    def create_senders(cls, messages_data):
        users = set()
        # Ignoring cc, bcc to add support later
        for message in messages_data:
            for header in message['payload']['headers']:
                if header['name'] in ['From']:
                    users.add(header['value'])

        try:
            user_objs = [
                User(email=email_id,username=email_id)
                for email_id in users
            ]
            User.objects.bulk_create(user_objs, ignore_conflicts=True)
            logger.info(f"Populated message senders for recipient {cls.recipient.email}")
            return users
        except Exception as err:
            raise err

    @classmethod
    def create_labels(cls, user, label_data):
        mail_labels = label_data.get('labels', [])
        labels = [
            Label(
                name=label['id'],
                label_name=label['name'],
                label_type=Label.LabelTypes.USER if label['type'] == 'user' else Label.LabelTypes.SYSTEM,
                message_list_visibility=label.get('messageListVisibility'),
                label_list_visibility=label.get('labelListVisibility'),
                user_id=user if label['type'] == 'user' else None
            )
            for label in mail_labels
        ]
        try:
            Label.objects.bulk_create(labels, ignore_conflicts=True)
            logger.info(f"Populated static message labels for recipient {cls.recipient.email}")
        except Exception as err:
            raise err

    @classmethod
    def create_messages(cls, messages_data):
        messages = [
            Message(
                message_id=message_data['id'],
                thread_id=message_data['threadId'],
                history_id=message_data['historyId'],
                size_estimate=message_data['sizeEstimate'],
                internal_date=datetime.fromtimestamp(int(message_data['internalDate']) / 1000),
                snippet=message_data['snippet']
            )
            for message_data in messages_data
        ]
        try:
            Message.objects.bulk_create(messages, ignore_conflicts=True)
            logger.info(f"Populated messages for recipient {cls.recipient.email}")
        except Exception as err:
            raise err

    @classmethod
    def create_message_labels(cls, messages, message_data):
        message_labels = []
        for message in message_data:
            message_labels.extend(message['labelIds'])

        label_objects = Label.objects.filter(label_name__in=message_labels)
        grouped_label_objects = {obj.name: obj for obj in label_objects}

        try:
            for message_obj, raw_message in zip(messages, message_data):
                raw_message_labels = raw_message['labelIds']
                message_label_objects = [grouped_label_objects[label_id] for label_id in raw_message_labels]
                message_obj.labels.add(*message_label_objects)
            logger.info(f"Populated message labels table for {cls.recipient.email}")
        except Exception as err:
            raise err

    @classmethod
    def create_user_messages(cls, messages, message_data):
        users = {'sender': []}
        user_msg_map = []
        grouped_msg_objects = {obj.message_id: obj for obj in messages}

        for message in message_data:
            sender = None
            for header in message['payload']['headers']:
                if header['name'] in ['From']:
                    sender = header['value']
                    users['sender'].append(sender)


            user_msg_map.append({'sender': sender, 'message': message['id']})
        
        user_objects = User.objects.filter(email__in=users['sender'])
        grouped_user_objects = {obj.email: obj for obj in user_objects}

        user_messages = []
        for msg_map in user_msg_map:
            sender_obj = grouped_user_objects.get(msg_map.get('sender'))
            recipient_obj = cls.recipient
            message_obj = grouped_msg_objects.get(msg_map.get('message'))
            user_messages.extend(
                 [
                     UserMessage(user_id=sender_obj, message_id=message_obj, user_type=UserMessage.UserTypes.SENDER),
                     UserMessage(user_id=recipient_obj, message_id=message_obj, user_type=UserMessage.UserTypes.RECIPIENT)
                ]
            )

        try:
            UserMessage.objects.bulk_create(user_messages)    
            logger.info(f"Populated user message table for {cls.recipient.email}")
        except Exception as err:
            raise err

    @classmethod
    def create_message_headers(cls, messages, message_data):
        message_headers = []
        for message_obj, raw_message in zip(messages, message_data):
            for header in raw_message['payload']['headers']:
                message_headers.append(
                    MessageHeaderValues(message_id=message_obj, header=header['name'], value=header['value'])
                )
        try:
            MessageHeaderValues.objects.bulk_create(message_headers)
            logger.info(f"Populated message headers table for {cls.recipient.email}")
        except Exception as err:
            raise err
