#!/usr/bin/env python3
from datetime import datetime, timedelta
from numpy import random as r
from operator import truediv, mul, add, sub
from optparse import OptionParser
import pandas as pd
import uuid

parser = OptionParser(
    usage="%prog [options] events attributes variants",
    description="Sythensize an Eventlog from a BPMN diagram",
    version="%prog v0.3.0",
    epilog="Sythensize an Eventlog from a BPMN diagram"
)
parser.add_option("-s", "--start", dest="start", help="Start",
                  default=datetime.now() - timedelta(days=150))
parser.add_option("-e", "--end", dest="end", help="End",
                  default=datetime.now() - timedelta(days=1))
parser.add_option("-c", "--number-of-cases", dest="number_of_cases", help="Number of Cases",
                  default=60000)
parser.add_option("-i", "--start-new-in", dest="start_new_in", help="Start new in",
                  default=0.1)
parser.add_option("-n", "--noise", dest="noise", help="Noise", action="store_true")
(options, args) = parser.parse_args()

def add_event(meta, event, attr_def):
    """Add event to event log."""
    reached_end = False

    if meta['idx'] == 0:
        timestamp = meta['first_stamp']
    else:
        duration = get_event_duration(event, case_attrs, attr_def, variant)
        timestamp = event_log[-1]['Timestamp'] + timedelta(hours=vary(duration, 20))

    if timestamp < meta['end']:
        new_event = {'CaseId': meta['case'],
                     'EventName': event['name'],
                     'Timestamp': timestamp.replace(microsecond=0)}

        if meta['noise'] == 'off':
            event_log.append(new_event)
        else:
            if chance(99):
                event_log.append(new_event)

        if 'attributeSubs' in event:
            sub_attributes(event['attributeSubs'])
    else:
        reached_end = True

    return reached_end


def create_logs(options, events, attributes, variants):
    """
    Main function to create the event and attribute log.
    Two nested for-loops are needed to do so:
        The first loop is iterating over cases. An attribute log is created
        for each case.
        Second loop is iterating over events found in a picked variant.
    """
    global case_attrs
    global start_date
    global variant
    check_user_input(options, variants)

    start_date = options['start']
    first_stamp = options['start']
    for case in range(options['number_of_cases']):
        if case != 0:
            first_stamp += timedelta(hours=options['start_new_in'])

        random_case_id = create_case_id()
        case_attrs = create_attributes(random_case_id, attributes, first_stamp)

        variant = pick_variant(variants)

        for idx, event_name in enumerate(variant['sequence']):
            meta = {'idx': idx, 'case': random_case_id, 'first_stamp': first_stamp,
                    'end': options['end'], 'noise': log_meta['noise']}

            reached_end = add_event(meta,
                                    get_event_by_name(event_name, events),
                                    attributes)

            if meta['noise'] == 'on':
                if chance(1):
                    break

            if reached_end:
                break

        if event_log[-1]['CaseId'] == case_attrs['CaseId']:
            attribute_log.append(case_attrs)

    parse_timestamps(event_log)
    if options['event_attributes']:
        add_event_attrs(event_log, events)

    for attribute in attributes:
        if attribute['type'] == 'check_overdue':
            for logged_attribute in attribute_log:
                if (datetime.now() - logged_attribute[attribute['value']]).days > 0:
                    logged_attribute[attribute['name']] = 'Yes'
                else:
                    logged_attribute[attribute['name']] = 'No'



    return pd.DataFrame(event_log), pd.DataFrame(attribute_log)


def create_attributes(case_id, attr_def, case_start=None):
    """Define keys and values for the attribute log."""
    if case_id != 'sub':
        attributes = {'CaseId': case_id}
    else:
        attributes = {'CaseId': case_id}

    for attribute in attr_def:
        attributes[attribute['name']] = ''

    for attribute in attr_def:
        if 'conditions' in attribute:
            if not evaluate_conditions(attribute['conditions'], attributes):
                continue
        if attribute['type'] == 'number':
            if attribute['value']['type'] == 'normal':
                attributes[attribute['name']] = abs(r.normal(attribute['value']['input'][0],
                                                             attribute['value']['input'][1]))
            if attribute['value']['type'] == 'random':
                attributes[attribute['name']] = abs(r.randint(attribute['value']['input'][0],
                                                              attribute['value']['input'][1]))
            if attribute['value']['type'] == 'static':
                attributes[attribute['name']] = attribute['value']['input']
            if attribute['format'] == 'int':
                attributes[attribute['name']] = round(attributes[attribute['name']])
            if attribute['format'] == 'cur':
                attributes[attribute['name']] = round(attributes[attribute['name']], 2)
        elif attribute['type'] == 'choice':
            attributes[attribute['name']] = pick_from(attribute['value'])['name']
        elif attribute['type'] == 'random_choice':
            attributes[attribute['name']] = r.choice(attribute['value'])
        elif attribute['type'] == 'copy':
            attributes[attribute['name']] = attributes[attribute['value']]
        elif attribute['type'] == 'copy_case':
            attributes[attribute['name']] = case_attrs[attribute['value']]
        elif attribute['type'] == 'string':
            attributes[attribute['name']] = attribute['value']
        elif attribute['type'] == 'datetime_choice':
            date_time = case_start + timedelta(days=pick_from(attribute['value'])['diff'])
            attributes[attribute['name']] = date_time.replace(microsecond=0)
        elif attribute['type'] == 'datetime_number':
            date_time = case_start + timedelta(days=r.normal(attribute['value']['input'][0],
                                                             attribute['value']['input'][1]))
            attributes[attribute['name']] = date_time.replace(microsecond=0)
        elif attribute['type'] == 'calc':
            if attributes['CaseId'] == 'sub':
                attributes[attribute['name']] = round(calculator(attribute['eq'], case_attrs), 2)
            else:
                attributes[attribute['name']] = round(calculator(attribute['eq'], attributes), 2)
        elif attribute['type'] == 'ui':
            attributes[attribute['name']] = uuid.uuid4().hex[:8]
        elif attribute['type'] == 'over_time':
            attributes[attribute['name']] = round(calc_over_time(attribute['eq'], case_start), 2)

    return attributes


def vary(number, variance):
    """Randomize number within given variance in %."""
    return r.uniform(number * (1 - variance / 100), number * (1 + variance / 100))


def pick_from(data):
    """Pick an item from a dataset with given probabilities."""
    winner = r.uniform(0, 1)
    threshold = 0

    for item in data:
        threshold += float(item['prob'])
        if threshold > winner:
            return item


def parse_timestamps(log):
    """Timestamps are pared to ISO format before written to the event log."""
    for event in log:
        event['Timestamp'] = event['Timestamp'].isoformat()


def chance(prob):
    """Evaluate a probability."""
    return prob > r.random() * 100


def get_event_by_name(name, events):
    """Required for add_event function."""
    for event in events:
        if event['name'] == name:
            return event


def evaluate_conditions(conditions, case_attributes):
    """Evaluate conditions for attribute-, variant-, or event manipulation."""
    binaries = []
    comp = True

    for condition in conditions:
        if condition['op'] == 'greater':
            binaries.append(float(case_attributes[condition['attribute']]) > float(condition['value']))
        if condition['op'] == 'less':
            binaries.append(float(case_attributes[condition['attribute']]) < float(condition['value']))
        if condition['op'] == 'equals':
            binaries.append(float(case_attributes[condition['attribute']]) == float(condition['value']))
        if condition['op'] == 'is':
            binaries.append(case_attributes[condition['attribute']] == condition['value'])
        if condition['op'] == 'is not':
            binaries.append(case_attributes[condition['attribute']] != condition['value'])
        if condition['op'] == 'include_all':
            binaries.append(all(elem in variant['sequence'] for elem in condition['events']))
        if condition['op'] == 'include':
            binaries.append(any(elem in variant['sequence'] for elem in condition['events']))
        if condition['op'] == 'exclude':
            binaries.append(any(elem not in variant['sequence'] for elem in condition['events']))
        if condition['op'] == 'exclude_all':
            binaries.append(all(elem not in variant['sequence'] for elem in condition['events']))

    if False in binaries:
        comp = False

    return comp


def sub_attributes(sub_items):
    """Change the value of a case attribute."""
    for item in sub_items:
        new = create_attributes('sub', [item])
        if 'subConditions' in item:
            if not evaluate_conditions(item['subConditions'], case_attrs):
                if 'else' in item:
                    new[item['name']] = item['else']
                else:
                    continue
        if 'subProb' in item:
            if not chance(item['subProb']):
                continue

        case_attrs[item['name']] = new[item['name']]


def get_event_duration(event, attributes, attr_def, variant):
    """Durations might be manipulated if
    specified in certain events or variants. """
    duration = float(event['duration'])
    scale_from_attr = 1
    scale_from_variant = 1
    for def_item in attr_def:
        if 'eventSubs' in def_item:
            for e_sub in def_item['eventSubs']:
                if attributes[def_item['name']] == e_sub['trigger']:
                    if e_sub['eventName'] == event['name'] or e_sub['eventName'] == "all":
                        scale_from_attr = e_sub['duration'] / 100
    if 'eventSubs' in variant:
        for e_sub in variant['eventSubs']:
            if e_sub['eventName'] == event['name'] or e_sub['eventName'] == "all":
                scale_from_variant = e_sub['duration'] / 100

    return duration * scale_from_attr * scale_from_variant


def add_event_attrs(event_log, event_def):
    """Interim solution for event attributes"""

    for event in event_log:
        for def_item in event_def:
            if def_item['name'] == event['EventName']:
                if 'eventAttributes' in def_item:
                    for key, value in def_item['eventAttributes'].items():
                        event[key] = value
                        if key == 'automationrate':
                            if r.random() * 100 < float(def_item['eventAttributes']['automationrate']):
                                auto_rate = 'BATCH_JOB'
                            else:
                                auto_rate = 'USER'
                            event['User Type'] = auto_rate


def check_user_input(log_meta, variants):
    """Check user input before creating logs. Still a to-do."""

    # Check log_meta
    for meta in log_meta:
        if not meta:
            print("Meta missing.")
    # Check Event Definition
    # Check Variant Definition
    sum_variant_prob = 0
    for variant in variants:
        sum_variant_prob += variant['prob']
    # print(sum_variant_prob)
    test = round(sum_variant_prob, 6) == 1
    # Check Attribute Definition


def create_case_id():
    """Create unique identifier for a case."""
    case_id = 'oc' + str(uuid.uuid4().hex[:8])
    return case_id


def pick_variant(variants):
    """Pick a variant by probability from variants definition."""
    forcing_variants = get_forcing_variants(variants)
    if len(forcing_variants) > 0:
        variant = pick_from(forcing_variants)
    else:
        variant = pick_from(variants)
        if 'conditions' in variant:
            if not evaluate_conditions(variant['conditions'], case_attrs):
                variant = pick_variant(variants)
    if 'attributeSubs' in variant:
        sub_attributes(variant['attributeSubs'])
    return variant


def get_forcing_variants(variants):
    """If a condition is forcing, a variant will be picked
    when meeting the condition."""
    forcing_variants = []

    for variant in variants:
        if 'conditions' in variant:
            if evaluate_conditions(variant['conditions'], case_attrs):
                for condition in variant['conditions']:
                    if 'forcing' in condition:
                        if chance(condition['forcing']):
                            forcing_variants.append(variant.copy())

    for variant in forcing_variants:
        variant['prob'] = 1 / len(forcing_variants)

    return forcing_variants


def calculator(eq, attributes):
    """For function input. To be replace with eval function."""
    operators = {
        '+': add,
        '-': sub,
        '*': mul,
        '/': truediv
    }

    def calculate(s):
        try:
            return float(s)
        except:
            if s.isdigit():
                return float(s)
            if s in attributes:
                return float(attributes[s])
            for c in operators.keys():
                left, operator, right = s.partition(c)
                if operator in operators:
                    return operators[operator](calculate(left), calculate(right))

    return calculate(eq)


def calc_over_time(eq, time_stamp):
    """Determine values for over time widgets."""
    global start_date

    delta = time_stamp - start_date
    eq = eq.replace("x_t_d", str(delta.days))
    eq = eq.replace("x_t_w", str(delta.days / 7) if delta.days != 0 else str(0))
    eq = eq.replace("x_t_m", str(round(delta.days / 30, 2)) if delta.days != 0 else str(0))

    attribute_value = calculator(eq, [])

    return attribute_value

def run():
    if len(args) < 2:
        parser.print_help()
        sys.exit(1)
    events = []
    attributes = []
    variants = []
    with open(args.pop(0)) as event_fh:
        events = json.load(event_fh)
    with open(args.pop(0)) as attributes_fh:
        attributes = json.load(attributes_fh)
    with open(args.pop(0)) as variants_fh:
        attributes = json.load(variants_fh)
    event_log, attribute_log = create_logs(events, attributes, variants)
    event_log.to_csv('eventlog.csv', encoding='utf-8', index=False)
    attribute_log.to_csv('attributes.csv', encoding='utf-8', index=False)

if __name__ == "__main__":
    run()
