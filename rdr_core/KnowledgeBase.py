import json
from .models import Rule


class KnowledgeBase:

    kb = None
    features = None

    @staticmethod
    def get_kb(features=[]):
        if KnowledgeBase.kb == None:
            KnowledgeBase.kb = KnowledgeBase()
            KnowledgeBase.features = features

        return KnowledgeBase.kb

    @staticmethod
    def add_rule(rule_object: Rule):
        rule_object.id = Rule.objects.all().count()+1
        if rule_object.is_stopping:
            parent = rule_object.parent
            parent_rule_object = Rule.objects.get(id=parent)
            rule_object.if_false = parent_rule_object.if_true
            parent_rule_object.if_true = rule_object.id
            parent_rule_object.save()

        rule_object.save()

    @staticmethod
    def rule_satisfied(rule, case: list) -> bool:
        conditions = json.loads(rule.conditions)
        condition_keys = conditions.keys()
        for key in condition_keys:
            # print(KnowledgeBase.features)
            feature_index = KnowledgeBase.features.index(key)
            condition = conditions[key]
            if key in condition:
                tobe_evaluated_string = condition.replace(
                    key, str(case[feature_index]))
            else:
                tobe_evaluated_string = f"{case[feature_index]} {condition}"
            if not eval(tobe_evaluated_string):
                # print(f"{case[feature_index]} {condition}")
                return False
        return True

    @staticmethod
    def eval_case(case: list, all_rules=None) -> tuple | bool:
        rules_fired = []
        rules_evaluated = []
        conclusions = []
        if not all_rules:
            all_rules = Rule.objects.all()
        for current_rule in all_rules:
            stopped = False
            if current_rule.is_stopping:
                continue
            rules_evaluated.append(current_rule.id)
            satisfied = KnowledgeBase.rule_satisfied(current_rule, case)
            if satisfied:
                rules_fired.append(current_rule.id)
                if current_rule.if_true:
                    # print(current_rule.if_true)
                    stopping_rule = Rule.objects.get(id=current_rule.if_true)
                    while stopping_rule:
                        rules_evaluated.append(f"({stopping_rule.id})")
                        if KnowledgeBase.rule_satisfied(stopping_rule, case):
                            rules_fired.append(stopping_rule.id)
                            stopped = True
                            break
                        try:
                            stopping_rule = Rule.objects.get(
                                id=stopping_rule.if_false)
                        except Rule.DoesNotExist:
                            print(
                                f"Rule matching query does not exist:: {stopping_rule.if_false}")
                            stopping_rule = None

                if not stopped and current_rule.conclusion not in conclusions:
                    conclusions.append(current_rule.conclusion)
        print("Rule Evaluated:", rules_evaluated)
        print("Rule Fired:", rules_fired)
        print("Conclusion:", conclusions)
        if len(conclusions) == 0:
            return False, rules_evaluated, rules_fired
        else:
            return conclusions, rules_evaluated, rules_fired
