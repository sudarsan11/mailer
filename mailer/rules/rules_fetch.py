import json
import logging
from mailer.rules.rules_model import Condition, Rule, RuleSet, Action

logger = logging.getLogger('mailer.rules')

class RulesFetch:
    """
    Initialize rules fetcher
    Arguments:
        rules_data -> (list of dict) -> Initalize the list of rules
    Returns: 
        None
    """
    def __init__(self, rules_data):
        self.rules_data = rules_data

    """
    Alternate constructor to read rules from json fiel
    Arguments:
        rule_file_path -> (str) -> local file path of rules json
    Returns: 
        None
    """
    @classmethod
    def read_rules_from_file(cls, rule_file_path):
        try:
            with open(rule_file_path, 'r') as rules_file:
                rules_data = json.load(rules_file)
            logger.info(f"Initializing rules from file")
            return cls(rules_data)
        except FileNotFoundError as file_err:
            logger.error(file_err)
        except ValueError as val_err:
            logger.error(val_err)
    """
    Validate and construct conditions object
    Arguments:
        conditionss -> (list of dict)
    Returns: 
        condition object -> (Condition)
    """
    def construct_conditions(self, conditions):
        validated_conditions = []
        try:
            for condition in conditions:
                validated_conditions.append(
                    Condition(
                        field=condition.get('field'), 
                        predicate=condition.get('predicate'), 
                        value=condition.get('value'),
                    )
                )
            logger.info(f"Constructing rule conditions")
            return validated_conditions
        except ValueError as val_err:
            raise val_err
    
    """
    Validate and construct action object
    Arguments:
        actions -> (list of dict)
    Returns: 
        action object -> (Action)
    """
    def construct_actions(self, actions):
        validated_actions = []
        try:
            for action in actions:
                validated_actions.append(
                    Action(
                        attribute=action.get('attribute'), 
                        name=action.get('name'), 
                        value=action.get('value'),
                    )
                )
            logger.info(f"Constructing rule actions")
            return validated_actions
        except ValueError as val_err:
            raise val_err
    
    """
    Validate and construct rules and actions
    Arguments:
        None
    Returns: 
        rule_set -> (RuleSet) -> List of rules to search messages
        actions  -> (Action)  -> List of actions to be invoked on filtered messages
    """
    def construct_rules(self):
        data = self.rules_data
        rules = data.get('rules', [])
        rule_predicate = data.get('predicate')
        actions = data.get('actions', [])

        try:
            validated_rules = []
            for rule in rules:
                conditions = rule.get('conditions', [])
                condition_predicate = rule.get('predicate')
                validated_conditions = self.construct_conditions(conditions)
                validated_rules.append(
                    Rule(conditions=validated_conditions, predicate=condition_predicate)
                )
            rule_set = RuleSet(rules=validated_rules, predicate=rule_predicate)
            action_set = self.construct_actions(actions)
            return rule_set, action_set
        except ValueError as val_err:
            raise val_err
