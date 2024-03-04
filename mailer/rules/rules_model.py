
from pydantic import BaseModel, field_validator
from typing import Union, List
from typing_extensions import Literal

field_datatype_map = {
    'from': str,
    'to': str,
    'subject': str,
    'date_received_days': int,
    'date_received_months': int,
}
predicate_datatype_map = {
    str: ['contains', 'not_contains', 'equal', 'not_equal'],
    int: ['lesser_than', 'greater_than'],
}

condition_fields = tuple(field_datatype_map.keys())
condition_predicates = tuple(element for sublist in predicate_datatype_map.values() for element in sublist)
rule_predicates = ('all', 'any')
action_attributes = ('message')
actions = ('mark', 'move')
action_values = ('inbox', 'read', 'unread')


class Condition(BaseModel):
    field: Literal[condition_fields]
    predicate: Literal[condition_predicates]
    value: Union[str, int]

    def valudate_field(cls, field, info):
        if field not in condition_fields:
            raise ValueError(f"Invalid field {field}. Supported fields {condition_fields}")
        return field

    @field_validator("predicate")
    def validate_predicate(cls, predicate, info):
        field = info.data['field']
        field_datatype = field_datatype_map[field]
        if predicate not in predicate_datatype_map[field_datatype]:
            raise ValueError(f"Invalid predicate {predicate} for field {field}")
        return predicate
    
    @field_validator("value")
    def validate_value(cls, value, info):
        field = info.data['field']
        field_datatype = field_datatype_map[field]
        if not isinstance(value, field_datatype):
            raise ValueError(f"Invalid value {value} for field {field}. Value must be of type {field_datatype}")
        return value

class Rule(BaseModel):
    conditions: List[Union[Condition, 'Rule']]
    predicate: Literal[rule_predicates]

class RuleSet(BaseModel):
    rules: List[Union[Condition, Rule]]
    predicate: Literal[rule_predicates]

class Action(BaseModel):
    attribute: Literal[action_attributes]
    name: Literal[actions]
    value: Literal[action_values]
    # NOTE: To handle name, value combination validation
