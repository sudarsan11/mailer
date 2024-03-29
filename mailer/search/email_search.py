import os
import logging
import datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()
from django.db.models import Q, Count

from db.models import MessageHeaderValues
logger = logging.getLogger('mailer.email_search')

class EmailSearch:

    """
    Initalize search service for resource based on provided rules
    Arguments:
        resource_type -> (str)     -> Resource like message 
        rules_data    -> (RuleSet) -> Rules to filter
    Returns: 
        resource_ids -> (list) -> List of resource ids filtered by rules
    """
    @classmethod
    def fetch(cls, resource_type, rules_data):
        if resource_type == 'message':
            rules, rules_predicate = rules_data.rules, rules_data.predicate
            messages = cls.fetch_message_by_header(rules, rules_predicate)
            if not messages or len(messages) == 0:
                raise Exception('No messages found matching rules')
            return list(messages)
        else:
            raise Exception('Invalid resource type')

    """
    Helper to construct query given a column, operator and value
    Arguments:
        column_name -> (str) -> The db table column name
        operator    -> (str) -> The operator to use for query
        value       -> (str) -> The value to use for query
    Returns: 
        query_object -> (django Q)
    """
    @staticmethod
    def get_query(column_name, operator, value):
        field_lookup = f"{column_name}__"
        if operator == 'contains':
            return Q(**{f"{field_lookup}icontains": value})
        elif operator == 'not_contains':
            return ~Q(**{f"{field_lookup}icontains": value})
        elif operator == 'equals':
            return Q(**{f"{field_lookup}iexact": value})
        elif operator == 'not_equal':
            return ~Q(**{f"{field_lookup}iexact": value})
        elif operator == 'lesser_than':
            return Q(**{f"{field_lookup}lte": value})
        elif operator == 'greater_than':
            return Q(**{f"{field_lookup}gte": value})
        else:
            return Q()

    """
    Given a field name in condition, returns the column and value to query on
    Arguments:
        field -> (str) -> The field name in the condition
    Returns: 
        query_object -> (tuple) -> Has the column name and value
    """
    @staticmethod
    def get_header_name(field):
        if field == 'from':
            return ('header', 'From')
        elif field == 'to':
            return ('header', 'To')
        elif field == 'subject':
            return ('header', 'Subject')
        else:
            return (None, None)

    """
    Given a field value in condition, returns the column and value to query on
    Arguments:
        field -> (str) -> The field name in the condition
    Returns: 
        query_object -> (tuple) -> Has the column name and value
    """
    @staticmethod
    def get_header_value(value):
        return ('value', value)

    """
    In case if query must be performed on message table returns the column and value to query on
    Arguments:
        field -> (str) -> The field name in the condition
        value -> (str) -> The value in the condition
    Returns: 
        query_object -> (tuple) -> Has the column name and value
    """
    @staticmethod
    def get_message_condition_column(field, value):
        if field == 'date_received_days':
            return ('message_id__internal_date', datetime.datetime.utcnow() - datetime.timedelta(days=value))
        elif field == 'date_received_months':
            return ('message_id__internal_date', datetime.datetime.utcnow() - datetime.timedelta(days=30*value))

    """
    Takes a list of conditions and construct query
    Arguments:
        conditions -> (Rule.conditions) -> List of conditions read from user input
    Returns: 
        message_query -> (django queryset) -> Has the queryset related to message table
        header_query  -> (django queryset) -> Has the queryset related to message header table
    """
    @classmethod
    def construct_query(cls, conditions):        
        # We need to build a filter like this
        # AND predicate -> for external table fields
        # OR predicate  -> for headers & values [for both all & any]

        # Example query filtering
        # 
        # .filter(
        #     Q(message_id_id__internal_date__lt=datetime.now()-timedelta(days=1)) &
        #     (
        #         Q(header='From', value__icontains='') |
        #         Q(header='Subject', value__icontains='')
        #     )
        # )
        
        message_query = Q()
        header_query = Q()

        message_condition_fields = ['date_received_days', 'date_received_months']
        for condition in conditions:
            field_name, predicate, field_value = condition.field, condition.predicate, condition.value
        
            if field_name in message_condition_fields:
                column_name, column_value = cls.get_message_condition_column(field_name, field_value)
                query = cls.get_query(column_name, predicate, column_value)
                message_query &= query
                
            else:
                header_name_column, header_name = cls.get_header_name(field_name)
                header_value_column, header_value = cls.get_header_value(field_value)

                header_name_query = cls.get_query(header_name_column, 'equals', header_name)
                header_value_query = cls.get_query(header_value_column, predicate, header_value)

                header_query |= header_name_query & header_value_query

        logger.info(f"Constructing message and header queries for conditions")
        return message_query, header_query
    
    """
    Takes a list of conditions and construct query
    Arguments:
        rules -> (RuleSet) -> List of rules read from user input
        rule_predicate -> (RuleSet.predicate) -> Predicate for list of rules
    Returns: 
        queryset -> (django queryset) -> Has the message ids filtered based on rules
    """
    @classmethod
    def fetch_message_by_header(cls, rules, rule_predicate):      
        message_headers_queryset = MessageHeaderValues.objects.all()
        rule_set_query = Q()

        for rule in rules:
            conditions_predicate = rule.predicate
            message_query, header_query = cls.construct_query(rule.conditions)
            rule_query = message_query & header_query

            # In case of all, since our q is like if (header is 'from' & value is 'some_val') or (header is 'to' & value is 'some_val')
            # we are explicitly matching all entries which match at least n conditions by a group by
            # Eg select msg where (header & value) or (header & value) group by msg_id having count('id') = 2
            logger.info(f"Filtering message based on message and header queries")
            if conditions_predicate == 'all':
                message_headers_queryset = (
                    message_headers_queryset
                    .filter(rule_query).values('message_id')
                    .annotate(num_conditions=Count('id'))
                    .filter(num_conditions=len(header_query))
                    .values_list('message_id_id__message_id', flat=True)
                    .distinct()
                )
            else:
                message_headers_queryset = (
                    message_headers_queryset
                    .filter(rule_query)
                    .values_list('message_id__message_id', flat=True)
                    .distinct()
                )

            # Supports only all need to extend for any
            rule_set_query &= rule_query

        message_headers_queryset.filter(rule_set_query)
        return message_headers_queryset
