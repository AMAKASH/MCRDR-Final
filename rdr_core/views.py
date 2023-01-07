import json
import pandas
import os

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from datetime import datetime

from .KnowledgeBase import KnowledgeBase
from .models import Rule, Case

# Create your views here.
dataset = None
initialized = False
features = []
cornerstones = []
definitions = []
error_row = -1


def load_primary_dataset():
    df = pandas.read_csv(
        'rdr_core/core/datasets/train_dataset.csv')
    df.drop('Sl', inplace=True, axis=1)
    files = os.listdir('rdr_core/core/datasets/testing')
    testing_path = 'rdr_core/core/datasets/testing'
    for filepath in files:
        path = os.path.join(testing_path, filepath)
        print(path)
        tdf = pandas.read_csv(path)
        tdf.drop(tdf.columns[0], inplace=True, axis=1)
        df = pandas.concat([df, tdf], ignore_index=True)
    return df


def initialize():
    global dataset
    global initialized
    global features
    global definitions
    global error_row
    if not initialized:
        print('Initializing Knowledgebase and dataset................')
        # dataset = pandas.read_csv('rdr_core/core/datasets/animal_dataset.csv')
        dataset = load_primary_dataset()
        features = list(dataset.columns)
        definitions = pandas.read_csv(
            'rdr_core/core/definitions/definition.csv')

        initialized = True
        error_row = -1
        KnowledgeBase.get_kb(features=features)
        load_cornerstones()


class IndexView(View):
    def get(self, request):
        initialize()
        questions = pandas.read_csv(
            'rdr_core/core/questions/questions.csv')
        questions.fillna('-', inplace=True)
        return render(request, 'rdr_core/index.html', {
            'questions': questions,
            'showQuestions': True
        })

    def post(self, request):
        initialize()
        data = request.POST
        data = data.copy()
        case = pre_process_post_data_for_eval(dict(data))
        kb = KnowledgeBase.get_kb()

        conclusion = kb.eval_case(case)

        print("=======================================================================")
        print('User Test Case: ', case)
        print('Evaluation: ', conclusion)
        print("=======================================================================")

        conclusion = conclusion[0]
        json_case = json.dumps(list(map(str, case)))
        query = Case.objects.filter(case_arr=json_case)
        if not query:
            print(query)
            db_case = Case(case_arr=json_case)
            db_case.save()

        return render(request, 'rdr_core/index.html', {
            'conclusions': conclusion
        })


def dataset_view(request):
    initialize()
    global dataset
    global initialized
    global features
    global definitions

    # dataset.to_csv('new-target.csv')

    return render(request, 'rdr_core/dataset.html', {
        'dataset': dataset,
        'features': features,
        'feature_definitions': definitions,
        'error_row': error_row
    })


def cornerstones_view(request):
    initialize()
    global cornerstones
    global dataset
    column_names = features.copy()
    column_names.append('Current Conclusion')

    return_obj = []
    for cornerstone in cornerstones:
        case = list(dataset.iloc[cornerstone[0]])[0:len(features)]
        temp = [cornerstone[2], cornerstone[0]]
        temp = temp + case + [cornerstone[1]]

        return_obj.append(temp)
    return render(request, 'rdr_core/cornerstones.html', {
        'column_names': column_names,
        'cornerstones': return_obj,
        'feature_definitions': definitions,
    })


def rules_view(request):
    initialize()
    global features
    column_names = features.copy()
    column_names = ['Go to If True',
                    'Go to If False', 'Rule no'] + column_names
    column_names.append('Conclusion')

    all_rules = Rule.objects.filter(is_stopping=False).order_by('id')
    return_object = []
    temp = []
    i = 0
    while i < len(all_rules) or temp:
        row = [''] * len(column_names)
        if len(temp) == 0:
            current_rule = all_rules[i]
            if i != len(all_rules)-1:
                next_parent_rule = all_rules[i+1].id
            else:
                next_parent_rule = "exit"
            i += 1
            if current_rule.is_stopping:
                continue
        else:
            current_rule = temp.pop(0)

        if current_rule.if_true:
            stopping_rule = Rule.objects.get(id=current_rule.if_true)
            while stopping_rule:
                temp.append(stopping_rule)
                if stopping_rule.if_false:
                    stopping_rule = Rule.objects.get(id=stopping_rule.if_false)
                else:
                    stopping_rule = None

        conditions = json.loads(current_rule.conditions)
        if current_rule.conclusion:
            row[-1] = current_rule.conclusion
        if current_rule.is_stopping:
            row[2] = f"({current_rule.id})"
        else:
            row[2] = current_rule.id

        row[0] = next_parent_rule
        row[1] = next_parent_rule

        if current_rule.if_true:
            row[0] = f"({current_rule.if_true})"

        elif current_rule.if_false:
            row[1] = f"({current_rule.if_false})"

        condition_keys = conditions.keys()
        for key in condition_keys:
            feature_index = features.index(key)
            condition = conditions[key]
            row[feature_index+3] = condition

        return_object.append(row)
    if return_object:
        return_object[-1][0] = 'exit'
        return_object[-1][1] = 'exit'

    return render(request, 'rdr_core/rules.html', {
        'column_names': column_names,
        'rows': return_object,
        'feature_definitions': definitions,
    })


class TestDatasetView(View):
    def get(self, request):
        initialize()
        global definitions

        query = Case.objects.all()
        if query:
            global features
            test_features = features.copy()
            test_features.remove('Target')
            request.session['user_data_exist'] = True
            dataset_list = []
            for q in query:
                dataset_list.append(list(map(int, (json.loads(q.case_arr)))))
            tdf = pandas.DataFrame(dataset_list, columns=test_features)

            return self.post(request, True, tdf)

        return render(request, 'rdr_core/testing.html', {
            'feature_definitions': definitions,
        })

    def post(self, request, flag=False, tdf=None):
        initialize()
        global definitions
        global features
        error = False
        test_features = features.copy()
        test_features.remove('Target')
        try:
            if flag:
                test_df = tdf
            else:
                csv = request.FILES['csv']
                test_df = pandas.read_csv(csv)
            test_df = run_view("", True, test_dataset=test_df)
            # print(csv)
        except Exception as e:
            error = 'Error Loading File. Please Upload The Correct Formated CSV file.'
            print(e)

        return_dictionary = {
            'feature_definitions': definitions,
            'features': test_features
        }
        if error:
            return_dictionary['error'] = error
        else:
            return_dictionary['dataset'] = test_df
            return_dictionary['dataset_present'] = True
            request.session['test_dataset'] = test_df.to_json()

        return render(request, 'rdr_core/testing.html', return_dictionary)


def run_view(request, test=False, test_dataset=None):
    initialize()
    global dataset
    if test:
        tobe_tested = test_dataset
    else:
        tobe_tested = dataset
    global error_row
    error_row = -1
    kb = KnowledgeBase.get_kb()
    tobe_tested['Conclusion'] = ""
    tobe_tested['Rules Evaluated'] = ""
    tobe_tested['Rules Fired'] = ""

    for index, row in tobe_tested.iterrows():
        evaluation = kb.eval_case(list(row))
        tobe_tested.loc[index,
                        'Rules Evaluated'] = "->".join(map(str, evaluation[1]))
        tobe_tested.loc[index,
                        'Rules Fired'] = "->".join(map(str, evaluation[2]))
        if not evaluation[0]:
            # error_row = index
            # break
            tobe_tested.loc[index, 'Conclusion'] = 'No Disorder'
        else:
            tobe_tested.loc[index, 'Conclusion'] = ', '.join(evaluation[0])

        if not test and not match_target_conclusion(row['Target'], evaluation[0]):
            error_row = index
            break

    if test:
        return tobe_tested

    return HttpResponseRedirect(reverse('dataset-page'))


def reset_view(request):
    global initialized
    initialized = False
    return HttpResponseRedirect(reverse('dataset-page'))


def update_conclusion_view(request):
    data = json.loads(request.body)
    print(data)
    rule = Rule.objects.get(id=data['update_rule_no'])
    rule.conclusion = data['new_conclusion']
    rule.save()
    return JsonResponse({
        'error': False,
        'msg': f"Conclusion for Rule {data['update_rule_no']} has been updated successfully."
    })


class AddDataFromTestView(View):
    def post(self, request):
        global initialized
        df = pandas.read_json(request.session['test_dataset'])
        corrections = request.POST
        for idx, correction in enumerate(corrections):
            if corrections[correction]:
                df.loc[idx, 'Conclusion'] = corrections[correction]

        df.drop('Rules Evaluated', inplace=True, axis=1)
        df.drop('Rules Fired', inplace=True, axis=1)
        df.rename(columns={'Conclusion': 'Target'}, inplace=True)
        today = datetime.today()
        today = today.strftime("%d-%m-%Y %H-%M-%S")
        print(today)
        if request.session.get('user_data_exist', None):
            filename = f'rdr_core/core/datasets/testing/user-data-{today}.csv'
            Case.objects.all().delete()
        else:
            filename = f'rdr_core/core/datasets/testing/test-data-{today}.csv'
        df.to_csv(filename)
        request.session['user_data_exist'] = False
        initialized = False
        return HttpResponseRedirect(reverse('run-view'))


class EvalTest(View):

    def get(self, request):
        rules = Rule.objects.all()
        for rule in rules:
            con = json.loads(rule.conditions)
            print(con)
            keys = list(con.keys()).copy()
            for k in keys:
                new = k.replace('SYM_', 'F')
                con[new] = con.pop(k)

            print(con)
            rule.conditions = json.dumps(con)
            rule.save()
        return HttpResponse('OK')

    def post(self, request):
        KnowledgeBase.get_kb()
        print(request.POST)
        return HttpResponse('OK')


class EvaluateSingle(View):
    def get(self, request):
        global features
        global dataset
        msg = "No Rules found for the Case Please Add a new Rule Above"
        kb = KnowledgeBase.get_kb()
        idx = int(request.GET['index'])
        case = list(dataset.iloc[idx])
        try:
            evaluation = kb.eval_case(case)
        except SyntaxError as e:
            evaluation = False
            msg = type(e)
        except Exception as e:
            evaluation = False
            msg = type(e)

        print(evaluation)
        if evaluation[0]:
            return_obj = []
            conclusions, _, rules_fired = evaluation

            rules_tobe_sent = rules_fired.copy()

            for rule_no in rules_fired:
                rule = Rule.objects.get(id=rule_no)
                if rule.is_stopping:
                    rules_tobe_sent.remove(rule.id)
                    rules_tobe_sent.remove(rule.parent)

            for rule_no in rules_tobe_sent:
                temp_dict = create_rule_dictionary(rule_no)
                if temp_dict:
                    return_obj.append(temp_dict)
            return JsonResponse({
                'error': False,
                'eval': evaluation,
                'eval_data': return_obj
            })
        else:
            return JsonResponse({
                'error': False,
                'eval': False,
                'msg': msg
            })


class AddRule(View):
    def post(self, request):
        kb = KnowledgeBase.get_kb()
        rule_datas = json.loads(request.body)
        print(rule_datas)
        conditions = {}
        conclusion = None
        cornerstone = []
        parent = -1
        for key in rule_datas.keys():
            if key == 'parent':
                parent = rule_datas['parent']
                continue
            if key == 'case':
                cornerstone = rule_datas['case']
                continue
            if key == 'conclusion':
                if rule_datas['conclusion'].upper() != 'N/A':
                    conclusion = rule_datas['conclusion']
                    conclusion = conclusion.strip()
                continue
            if rule_datas[key] != '':
                temp = key
                idx = int(temp.replace('condition', ''))
                conditions[features[idx]] = rule_datas[key]

        conditions = json.dumps(conditions)

        print('conditions: ', conditions)
        print('conclusion: ', conclusion)
        print('cornerstone', cornerstone)
        stopping_rule = Rule(conditions=conditions, parent=parent,
                             is_stopping=True, cornerstone=cornerstone)
        new_rule = Rule(conditions=conditions,
                        conclusion=conclusion, cornerstone=cornerstone)

        if conclusion:
            # Evaluate and Add new Rule
            skip_check = (parent == -2)
            matched_rule_no = check_matching_cornerstone(new_rule)
            if skip_check:
                kb.add_rule(new_rule)
            elif matched_rule_no != -1:
                return JsonResponse({
                    'error': True,
                    'eval_data': create_rule_dictionary(matched_rule_no),
                    'msg': f"The rule matches with a different cornerstone. Do you want to update the conclusion of the relavent rule (Rule {matched_rule_no}) with the new Conclusion?"
                })
            else:
                kb.add_rule(new_rule)

        if parent > 0 and not conclusion:
            print('Stopping Rule Added..........')
            kb.add_rule(stopping_rule)

        load_cornerstones()

        return JsonResponse({
            'error': False,
            'msg': 'Rule(s) Added to Knowledgebase Successfully!!'
        })


def check_matching_cornerstone(new_rule):
    global cornerstones
    global dataset
    kb = KnowledgeBase.get_kb()
    for cornerstone, conclusion, rule_no in cornerstones:
        case = list(dataset.iloc[cornerstone])
        evaluation = kb.eval_case(case, [new_rule])
        if evaluation[0]:
            return rule_no

    return -1


def load_cornerstones():
    print('Loading Cornerstones.......')
    global cornerstones
    cornerstones = []
    rules = Rule.objects.all()
    for rule in rules:
        if rule.is_stopping:
            continue
        cornerstones.append((rule.cornerstone, rule.conclusion, rule.id))


def create_rule_dictionary(rule_no):
    temp_dict = {}
    rule = Rule.objects.get(id=rule_no)
    if rule.is_stopping:
        return {}
    temp_dict['rule_no'] = rule_no
    temp_dict['cornerstone'] = list(map(str, list(dataset.iloc[rule.cornerstone])[
        0:len(features)]))
    temp_dict['conclusion'] = rule.conclusion
    return temp_dict


def match_target_conclusion(target, conclusion):
    target = target.strip().split(', ')
    # print(target)
    # print(conclusion)

    if not conclusion:
        conclusion = ['No Disorder']

    if len(target) != len(conclusion):
        print('MisMatchError in length')
        return False

    for single_conclusion in conclusion:
        if single_conclusion.strip() not in target:
            print("MisMatchError in :", single_conclusion)
            return False
    return True


def pre_process_post_data_for_eval(data):
    case = []
    if 'qb23c' in data.keys():
        val = data['qb23c']
        if 'None of the above' in val:
            data['qb23c'] = [0]
        else:
            data['qb23c'] = [1]
    else:
        data['qb23c'] = [0]

    raw = pandas.DataFrame.from_dict(data)

    # Encode PHQ part

    phq = raw.iloc[:, 0:9].copy()
    phq_cols = list(phq)
    phq.replace(to_replace={'Not at all': 0, 'Several days': 1,
                'More than half the days': 2, 'Nearly every day': 3}, inplace=True)

    # SUM the PHQ values, replace in raw
    raw.drop(columns=phq_cols, inplace=True)
    raw['PHQ'] = phq.sum(axis=1)

    # Encode GAD part
    gad = raw.iloc[:, 0:7].copy()
    gad_cols = list(gad)
    gad.replace(to_replace={'Not at all': 0, 'Several days': 1,
                'More than half the days': 2, 'Nearly every day': 3}, inplace=True)

    # SUM the GAD values, replace in raw
    raw.drop(columns=gad_cols, inplace=True)
    raw['GAD'] = gad.sum(axis=1)

    # Encode GEN part
    gen = raw.iloc[:, 0:1].copy()
    gen.replace(to_replace={'Not difficult at all': 0, 'Somewhat difficult': 1,
                'Very difficult': 2, 'Extremely difficult': 3}, inplace=True)
    # replace in raw
    raw.drop(columns=['qa16s'], inplace=True)
    raw['GEN'] = gen[:]

    # Encode duration part
    dur = raw[['qb32s']].copy()
    dur.replace(to_replace={
        "I don't have any of the symptoms": 0,
        'Less than 2 weeks': 1,
        'More than 2 weeks but less than 1 month': 2,
        'More than 1 month but less than 6 months': 3,
        'More than 6 months but less than 2 years': 4,
        'More than 2 years': 5
    }, inplace=True)

    # replace in raw
    raw.drop(columns=['qb32s'], inplace=True)
    raw['qb32s'] = dur[:]

    age = raw[['qb27s']].copy()

    age.replace(to_replace={
        '0 to 5': 0,
        '6 to 11': 1,
        '12 to 17': 2,
        '18+': 3
    }, inplace=True)

    # replace in raw
    raw.drop(columns=['qb27s'], inplace=True)
    raw['qb27s'] = age[:]

    cols = list(raw.columns)
    cols.sort()
    cols.remove('GAD')
    cols.remove('GEN')
    cols.remove('PHQ')

    cols = ['PHQ', 'GAD', 'GEN'] + cols

    raw = raw[cols]

    raw.replace(to_replace={
        'Social situation': 0,
        'Losing a major attachment figure': 1,
        'Open Space': 2,
        'Closed space': 3,
        'Any': 4,
        'None': 5,
    }, inplace=True)

    raw.replace(to_replace={
        'Yes': 1,
        'No': 0,
    }, inplace=True)
    raw.replace(to_replace={
        'Male': 0,
        'Female': 1,
        'Other': 2,
    }, inplace=True)

    case = list(raw.iloc[0])
    for i in range(2, 5):
        if 'NO' in case[-i].upper() or "N'T" in case[-i].upper() or "DONT" in case[-i].upper():
            # print(case[-i].upper())
            case[-i] = 0
        else:
            # print(case[-i].upper())
            case[-i] = 1

    return case
