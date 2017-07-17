"""
An Alexa skill built to demonstrate an intelligent tutoring system prototype
for teaching about counters in ladder logic programming in PLCs. It builds upon
Amazon's Color Expert sample Python skill.
"""

import random
import difflib
import decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    """ Helper that builds the speechlet response. """

    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    """ Helper that builds the response. """

    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Functions used for user management --------------- #
def add_user(user_id):
    """ Adds a new user to the user database. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.put_item(
        Item={
            'UserID': user_id,
            'CounterCorrect': {
                'bit that is set when the counter limit is reached': decimal.Decimal(0),
                'can be used to': decimal.Decimal(0),
                'counts': decimal.Decimal(0),
                'DN bit is set': decimal.Decimal(0),
                'DN bit remains set until': decimal.Decimal(0),
                'enable bit is not set if': decimal.Decimal(0),
                'enable bit is set when': decimal.Decimal(0),
                'enable bit remains set until': decimal.Decimal(0),
                'if the rung goes False': decimal.Decimal(0),
                'overflow bit is set when': decimal.Decimal(0),
                'overflow bit remains set until': decimal.Decimal(0),
                'stands for': decimal.Decimal(0),
                'to reset AC': decimal.Decimal(0),
                'underflow bit is set when': decimal.Decimal(0),
                'underflow bit remains set until': decimal.Decimal(0),
                'when AC is equal to or greater than PR': decimal.Decimal(0),
                'when the rung goes from True to False and AC is greater than PR': decimal.Decimal(0),
                'when the rung goes True': decimal.Decimal(0)
            },
            'CounterIncorrect': {
                'bit that is set when the counter limit is reached': decimal.Decimal(0),
                'can be used to': decimal.Decimal(0),
                'counts': decimal.Decimal(0),
                'DN bit is set': decimal.Decimal(0),
                'DN bit remains set until': decimal.Decimal(0),
                'enable bit is not set if': decimal.Decimal(0),
                'enable bit is set when': decimal.Decimal(0),
                'enable bit remains set until': decimal.Decimal(0),
                'if the rung goes False': decimal.Decimal(0),
                'overflow bit is set when': decimal.Decimal(0),
                'overflow bit remains set until': decimal.Decimal(0),
                'stands for': decimal.Decimal(0),
                'to reset AC': decimal.Decimal(0),
                'underflow bit is set when': decimal.Decimal(0),
                'underflow bit remains set until': decimal.Decimal(0),
                'when AC is equal to or greater than PR': decimal.Decimal(0),
                'when the rung goes from True to False and AC is greater than PR': decimal.Decimal(0),
                'when the rung goes True': decimal.Decimal(0)
            },
            'PreviousTotalCorrect': decimal.Decimal(0),
            'PreviousTotalIncorrect': decimal.Decimal(0),
            'QuestionLevel': decimal.Decimal(1),
            'TutoringStatus': {
                'OrderLevel': decimal.Decimal(1),
                'StatementLevel': decimal.Decimal(1)
            }
        }
    )

def reset_user(user_id):
    """ Resets a user to new user state. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    user_db = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))

    # Resets CounterCorrect column
    for i in user_db['Items']:
        counter_correct = (i['CounterCorrect'])
    for key in counter_correct:
        response = user_data_dynamodb.update_item(
            Key={
                'UserID': user_id,
            },
            UpdateExpression="set #ctrcor.#atr = :atrreset",
            ExpressionAttributeValues={
                ':atrreset': decimal.Decimal(0)
            },
            ExpressionAttributeNames={
                '#ctrcor': "CounterCorrect",
                '#atr': key,
            },
            ReturnValues="UPDATED_NEW"
        )

    # Resets CounterIncorrect column
    for i in user_db['Items']:
        counter_incorrect = (i['CounterIncorrect'])
    for key in counter_incorrect:
        response = user_data_dynamodb.update_item(
            Key={
                'UserID': user_id,
            },
            UpdateExpression="set #ctrincor.#atr = :atrreset",
            ExpressionAttributeValues={
                ':atrreset': decimal.Decimal(0)
            },
            ExpressionAttributeNames={
                '#ctrincor': "CounterIncorrect",
                '#atr': key,
            },
            ReturnValues="UPDATED_NEW"
        )

    # Resets PreviousTotalCorrect, PreviousTotalIncorrect, and QuestionLevel columns
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set PreviousTotalCorrect = :val1, PreviousTotalIncorrect = :val1,"\
            + "QuestionLevel = :val2",
        ExpressionAttributeValues={
            ':val1': decimal.Decimal(0),
            ':val2': decimal.Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )

    # Resets TutoringStatus column
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set TutoringStatus.OrderLevel = :val,"\
            + "TutoringStatus.StatementLevel = :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )

def user_exists(user_id):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    user_id_query = user_data_dynamodb.query(
        KeyConditionExpression=Key('UserID').eq(user_id)
    )
    if len(user_id_query['Items']) == 0:
        return False
    else:
        return True

def update_user_level(user_id):
    """ Keeps track of and updates the user's question difficulty level as they
    keep answering questions. """

    # Store previous totals
    previous_total_correct = get_previous_total_correct(user_id)
    previous_total_incorrect = get_previous_total_incorrect(user_id)

    # Conditionals to update level, <= 4 because 4 is the max difficulty level
    if get_question_level(user_id) <= 4:
        # Get the current totals. These values differ from the previous total
        # values stored above because these values take into account the question the
        # user answered just before reaching this stage and asking for a new question.
        current_total_correct = get_total_correct(user_id)
        current_total_incorrect = get_total_incorrect(user_id)

        # Conditionals to deal with initial conditions that could happen when
        # the user first starts answering questions.
        if current_total_correct == 0 and current_total_incorrect == 0:
            increment_question_level(user_id)
            decrement_question_level(user_id)
        elif current_total_correct != 0 and current_total_incorrect == 0:
            if current_total_correct % 5 == 0:
                increment_question_level(user_id)
            else:
                increment_question_level(user_id)
                decrement_question_level(user_id)
        elif current_total_correct == 0 and current_total_incorrect != 0:
            if current_total_incorrect % 3 == 0:
                if get_question_level(user_id) == 1:
                    increment_question_level(user_id)
                    decrement_question_level(user_id)
                else:
                    decrement_question_level(user_id)
            else:
                increment_question_level(user_id)
                decrement_question_level(user_id)

        # The following conditionals deal with conditions that can happen after a user
        # has questions both right and wrong.
        else:
            if (previous_total_correct == current_total_correct
                    and current_total_incorrect % 3 != 0)\
                or (previous_total_incorrect == current_total_incorrect
                    and current_total_correct % 5 != 0):
                increment_question_level(user_id)
                decrement_question_level(user_id)
            elif current_total_correct % 5 == 0 and current_total_incorrect % 3 == 0:
                decrement_question_level(user_id)
            elif current_total_correct % 5 == 0 and current_total_incorrect % 3 != 0:
                increment_question_level(user_id)
            elif current_total_correct % 5 != 0 and current_total_incorrect % 3 == 0:
                decrement_question_level(user_id)
            else:
                increment_question_level(user_id)
                decrement_question_level(user_id)

    # Update the previous totals to current totals
    update_previous_total_correct(user_id)
    update_previous_total_incorrect(user_id)

    new_level = get_question_level(user_id)
    return new_level

# --------------- Functions used for tutoring statement generations
# ---------------

def increment_order_level(user_id):
    """ Increments the order level counter that allows statements within a
    certain statement level to be presented in order to the user. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set TutoringStatus.OrderLevel = TutoringStatus.OrderLevel + :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )

def reset_order_level(user_id):
    """ Resets the order level to 1. Generally reset at the beginning of
    a new statement level, since each statement level may have a different
    number of statements. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set TutoringStatus.OrderLevel = :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )

def get_order_level(user_id):
    """ Returns the current order level. Used to keep track of where the
    program is in presenting all the statements within a statement level. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    tutoring_status_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in tutoring_status_query['Items']:
        order_level = (i['TutoringStatus']['OrderLevel'])
    return order_level

def get_max_order_levels(statement_level):
    """ Returns the max limit of the order levels. Used to make sure the program
    doesn't try to exceed bounds of # of statements there are within a statement
    level. """

    filter_expression = Attr("StatementLevel").eq(statement_level)
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    tutor_table_dynamodb = dynamodb.Table('TutorTable')
    tutor_table = tutor_table_dynamodb.scan(
        FilterExpression=filter_expression,
    )
    order_levels_counter = 0
    for item in tutor_table['Items']:
        order_levels_counter += 1
    return order_levels_counter

def increment_statement_level(user_id):
    """ Increments the statement level counter that is used by the program
    to track where it is (statement level) in the tutoring process. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set TutoringStatus.StatementLevel = TutoringStatus.StatementLevel + :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )

def reset_statement_level(user_id):
    """ Resets the statement level counter to 1. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set TutoringStatus.StatementLevel = :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )

def get_statement_level(user_id):
    """ Returns the current statement level. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    tutoring_status_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in tutoring_status_query['Items']:
        statement_level = (i['TutoringStatus']['StatementLevel'])
    return statement_level

def get_max_statement_level():
    """ Calculates and returns the max statement level from the
    tutoring database. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    tutor_table_dynamodb = dynamodb.Table('TutorTable')
    projection_expression = "StatementLevel"
    tutor_table = tutor_table_dynamodb.scan(
        ProjectionExpression=projection_expression,
    )
    max_statement_level = 0
    for item in tutor_table['Items']:
        if item['StatementLevel'] > max_statement_level:
            max_statement_level = item['StatementLevel']

    return max_statement_level

def get_tutoring_statement(statement_level=1, order_level=1, attribute=None):
    """ Returns a tutoring statement based on an input statement level and
    order level, or input attribute. """
    if attribute is None:
        # Allow for filtering of questions for a requested level
        filter_expression = Attr("StatementLevel").eq(statement_level)\
            & Attr("OrderLevel").eq(order_level)

        # List to store question details to be returned to caller function
        statement_details = []

        # Set up access to necessary databases from DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        tutor_table_dynamodb = dynamodb.Table('TutorTable')
        tutor_table = tutor_table_dynamodb.scan(
            FilterExpression=filter_expression,
        )

        # Obtain question template components from database
        for item in tutor_table['Items']:
            statement_details = item['TutoringStatements']

        return statement_details
    else:
        # List to store question details to be returned to caller function
        statement_details = []

        # Set up access to necessary databases from DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        tutor_table_dynamodb = dynamodb.Table('TutorTable')
        tutoring_statement_query = tutor_table_dynamodb.query(KeyConditionExpression=Key('Attribute')\
            .eq(attribute))

        # Obtain question template components from database
        for item in tutoring_statement_query['Items']:
            statement_details = item['TutoringStatements']

        return statement_details

# --------------- Functions used for question generation and testing operations
# ---------------

def get_total_correct(user_id):
    """ Returns the total number of questions the user has answered correctly. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in counter_current_value['Items']:
        counter_result = (i['CounterCorrect'])
    counter_result_sum = sum(counter_result.values())
    return counter_result_sum

def get_total_incorrect(user_id):
    """ Returns the total number of questions the user has answered incorrectly. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in counter_current_value['Items']:
        counter_result = (i['CounterIncorrect'])
    counter_result_sum = sum(counter_result.values())
    return counter_result_sum

def update_previous_total_correct(user_id):
    """ Updates the previous total correct tracker, which is used to deal with
    the scenario where a user is stuck on a certain correct total.
    Check update_user_level() function for a better understanding. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in counter_current_value['Items']:
        counter_result = (i['CounterCorrect'])
    counter_result_sum = sum(counter_result.values())

    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set PreviousTotalCorrect = :val",
        ExpressionAttributeValues={
            ':val': counter_result_sum
        },
        ReturnValues="UPDATED_NEW"
    )

def get_previous_total_correct(user_id):
    """ Returns the previous total correct value, sum of all of the individual
    attribute values. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    previous_total_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in previous_total_query['Items']:
        previous_total_correct = (i['PreviousTotalCorrect'])
    return previous_total_correct

def update_previous_total_incorrect(user_id):
    """ Updates the previous total incorrect tracker, which is used to deal with
    the scenario where a user is stuck on a incorrect total.
    Check update_user_level() function for a better understanding. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in counter_current_value['Items']:
        counter_result = (i['CounterIncorrect'])
    counter_result_sum = sum(counter_result.values())

    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set PreviousTotalIncorrect = :val",
        ExpressionAttributeValues={
            ':val': counter_result_sum
        },
        ReturnValues="UPDATED_NEW"
    )

def get_previous_total_incorrect(user_id):
    """ Returns the previous total incorrect value, sum of all of the individual
    attribute values. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    previous_total_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in previous_total_query['Items']:
        previous_total_incorrect = (i['PreviousTotalIncorrect'])
    return previous_total_incorrect

def increment_question_correct(user_id, attribute_type):
    """ Increments the correct tracker for the specific attribute type
    question a user answered correctly. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set #ctrcor.#atrval = #ctrcor.#atrval + :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ExpressionAttributeNames={
            '#ctrcor': "CounterCorrect",
            '#atrval': attribute_type
        },
        ReturnValues="UPDATED_NEW"
    )

def increment_question_incorrect(user_id, attribute_type):
    """ Increments the incorrect tracker for the specific attribute type
    question a user answered incorrectly. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set #ctrincor.#atrval = #ctrincor.#atrval + :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ExpressionAttributeNames={
            '#ctrincor': "CounterIncorrect",
            '#atrval': attribute_type
        },
        ReturnValues="UPDATED_NEW"
    )

def increment_question_level(user_id):
    """ Increments the question level tracker. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set QuestionLevel = QuestionLevel + :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )

def decrement_question_level(user_id):
    """ Decrements the question level tracker. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.update_item(
        Key={
            'UserID': user_id,
        },
        UpdateExpression="set QuestionLevel = QuestionLevel - :val",
        ExpressionAttributeValues={
            ':val': decimal.Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )

def get_question_level(user_id):
    """ Returns the current question level. """
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    current_level_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))
    for i in current_level_query['Items']:
        current_level = (i['QuestionLevel'])
    return current_level

def generate_select_value():
    """ Generates a random select value question, its answer, and returns
    the full details of the question to the caller function as a List.
    """

    # List to store question details to be returned to function caller
    question_details = []

    # Store components of question templates
    question_attributes = []
    question_templates = []

    # Set up access to necessary databases from DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    select_value_table_dynamodb = dynamodb.Table('QuestionTemplate_SelectValue')
    answer_table = dynamodb.Table('FactTable')

    select_value_table = select_value_table_dynamodb.scan()

    # Obtain question template components from database
    for item in select_value_table['Items']:
        question_attributes.append(item['Attribute'])
        question_templates.append(item['SelectValue'])

    # Store possible output variables for output question
    all_available_parts = ["CTU", "CTD"]
    part_ctu_answers = []
    part_ctd_answers = []


    # Randomly generate question's attribute
    output_question_attribute_num = random.randint(0, 17)
    output_question_attribute = question_attributes[output_question_attribute_num]

    # Once attribute is generated, finds and stores all matching values for every
    # respective part (i.e. the possible answer values)
    for part in all_available_parts:
        value = answer_table.query(KeyConditionExpression=Key('Part & Attribute')\
            .eq(part + " " + output_question_attribute))
        if (len(value['Items']) != 0) and (part == "CTU"):
            for i in value['Items']:
                part_ctu_answers.append(i['Value'].lower())
        if (len(value['Items']) != 0) and (part == "CTD"):
            for i in value['Items']:
                part_ctd_answers.append(i['Value'].lower())

    # Pick a part, but make sure that part has at least one value to go with it
    # as an answer.
    if len(part_ctu_answers) != 0 and len(part_ctd_answers) != 0:
        output_question_part = random.choice(all_available_parts)
    elif len(part_ctu_answers) != 0 and len(part_ctd_answers) == 0:
        output_question_part = all_available_parts[0]
    elif len(part_ctu_answers) == 0 and len(part_ctd_answers) != 0:
        output_question_part = all_available_parts[1]
    else:
        print("Error! part_ctu_answers and part_ctd_answers lists are both empty.")

    # Depending on which part is generated, find all possible answers that go with
    # that part + attribute and store into a respective array
    if output_question_part == all_available_parts[0]:
        output_question = question_templates[output_question_attribute_num].replace("<PART>", \
            output_question_part).replace("<ATTRIBUTE>", output_question_attribute)
        question_details.append(output_question)
        question_details.append(part_ctu_answers)
    else:
        output_question = question_templates[output_question_attribute_num].replace("<PART>", \
            output_question_part).replace("<ATTRIBUTE>", output_question_attribute)
        question_details.append(output_question)
        question_details.append(part_ctd_answers)

    return question_details

def generate_select_part(question_level):
    """ Generates a random select part question. """

    # Allow for filtering of questions for a requested level
    filter_expression = Attr("Level").eq(question_level)

    # List to store question details to be returned to caller function
    question_details = []

    # Store components of question templates
    question_attributes = []
    question_templates = []

    # Keeps track of the total number of attributes.
    # Useful since filtering for level leads to different available
    # attributes based on the level of question requested.
    total_attribute_num = 0

    # Set up access to necessary databases from DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    select_part_table_dynamodb = dynamodb.Table('QuestionTemplate_SelectPart')
    answer_table = dynamodb.Table('FactTable')
    select_part_table = select_part_table_dynamodb.scan(
        FilterExpression=filter_expression,
    )

    # Obtain question template components from database
    for item in select_part_table['Items']:
        question_attributes.append(item['Attribute'])
        question_templates.append(item['SelectPart'])
        total_attribute_num += 1

    # Store possible output variables for output question
    all_available_parts = ["CTU", "CTD"]
    all_output_question_values = []
    all_output_question_parts = []

    # Randomly generate question's attribute, then get its respective output
    # question template.
    output_question_attribute_num = random.randint(0, total_attribute_num-1)
    output_question_attribute = question_attributes[output_question_attribute_num]
    output_question_template = question_templates[output_question_attribute_num]
    question_details.append(output_question_attribute)

    # Once attribute is generated, generate all possible values to go with attribute
    # based on possible parts.
    for part in all_available_parts:
        value = answer_table.query(KeyConditionExpression=Key('Part & Attribute')\
            .eq(part + " " + output_question_attribute))
        if len(value['Items']) != 0:
            for i in value['Items']:
                all_output_question_values.append(i['Value'])
                all_output_question_parts.append(part)

    # Pick a part and the value that goes with it so that a question can be formed.
    # For loop makes sure that if both CTD and CTU have the same value for the same
    # attribute, then the final question answer is both, and not just one of CTD
    # or CTU.
    output_question_part_index = random.randint(0, len(all_output_question_parts)-1)
    output_question_part = all_output_question_parts[output_question_part_index]
    output_question_value = all_output_question_values[output_question_part_index]
    output_question_answer = output_question_part
    for index in range(0, len(all_output_question_values)-1):
        if all_output_question_parts[index] != output_question_part\
        and all_output_question_values[index] == output_question_value:
            output_question_answer = "Both"

    output_question = output_question_template.replace("<ATTRIBUTE>", output_question_attribute)\
        .replace("<VALUE>", output_question_value)

    question_details.append(output_question)
    question_details.append(output_question_answer)

    return question_details

def generate_true_false(question_level):
    """ Generates a random true and false question, its answer, and returns
    the full details of the question to the caller function as a List.
    """
    # Allow for filtering of questions for a requested level
    filter_expression = Attr("QuestionLevel").eq(question_level)

    # List to store question details to be returned to caller function
    question_details = []

    # Store components of question templates
    question_attributes = []
    question_templates = []

    # Keeps track of the total number of attributes.
    # Useful since filtering for level leads to different available
    # attributes based on the level of question requested.
    total_attribute_num = 0

    # Set up access to necessary databases from DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    true_false_table_dynamodb = dynamodb.Table('QuestionTemplate_TrueFalse')
    answer_table = dynamodb.Table('FactTable')
    true_false_table = true_false_table_dynamodb.scan(
        FilterExpression=filter_expression,
    )

    # Obtain question template components from database
    for item in true_false_table['Items']:
        question_attributes.append(item['Attribute'])
        question_templates.append(item['TrueFalse'])
        total_attribute_num += 1

    # Store possible output variables for output question
    all_available_parts = ["CTU", "CTD"]
    all_output_question_values = []

    # Randomly generate question's attribute
    output_question_attribute_num = random.randint(0, total_attribute_num-1)
    output_question_attribute = question_attributes[output_question_attribute_num]
    question_details.append(output_question_attribute)

    # Once attribute is generated, generate all possible values to go with attribute
    # based on possible parts.
    for part in all_available_parts:
        value = answer_table.query(KeyConditionExpression=Key('Part & Attribute')\
            .eq(part + " " + output_question_attribute))
        if len(value['Items']) != 0:
            for i in value['Items']:
                all_output_question_values.append(i['Value'])

    # Queries DynamoDB fact table to get all valid answers that match for a given attribute
    attribute_valid_answers = []
    for counter in range(len(all_available_parts)):
        value = answer_table.query(KeyConditionExpression=Key('Part & Attribute')\
            .eq(all_available_parts[counter] + " " + output_question_attribute))
        for i in value['Items']:
            attribute_valid_answers.append(question_templates[output_question_attribute_num] \
                .replace("<PART>", all_available_parts[counter]).replace("<ATTRIBUTE>", \
                output_question_attribute).replace("<VALUE>", i['Value']))

    # Output question that gets relayed to the user, pick random part and val to match
    # with a chosen attribute to generate a random (but reasonable) question
    output_question_part = random.choice(all_available_parts)
    output_question_value = random.choice(all_output_question_values)

    output_question = question_templates[output_question_attribute_num]\
        .replace("<PART>", output_question_part).replace("<ATTRIBUTE>",\
        output_question_attribute).replace("<VALUE>", output_question_value)
    question_details.append(output_question)

    # If the answer to the generated question is false, we generate a True version to teach user
    output_closest_answer = difflib.get_close_matches(output_question,\
        attribute_valid_answers, n=1, cutoff=0.8)

    # Query fact table for output question, if present then True, else False
    output_question_query = answer_table.query(KeyConditionExpression=Key('Part & Attribute')\
        .eq(output_question_part + " " + output_question_attribute) & Key('Value')\
        .eq(output_question_value))

    if len(output_question_query['Items']) == 0:
        question_details.append("false")
        output_corrected_answer = output_closest_answer[0]
        question_details.append(output_corrected_answer)
    else:
        question_details.append("true")
        output_true_answer = output_question
        question_details.append(output_true_answer)

    return question_details

def get_attribute_feedback(user_id):
    """ Returns the attributes the user has performed the worst on for feedback. """

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')
    response = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
        .eq(user_id))

    worst_attributes = {}

    for i in response['Items']:
        incorrect_results = (i['CounterIncorrect'])

    # Find the highest value of attributes a user has gotten wrong
    most_attributes_wrong = 0
    for key in incorrect_results:
        if incorrect_results[key] > most_attributes_wrong:
            most_attributes_wrong = incorrect_results[key]

    feedback_statements = {}
    no_mistakes_feedback = ["Great job!", "Nice work!", "Well done!", "Nicely done!", "Great work!"]
    if most_attributes_wrong == 0:
        feedback_statements["None"] = random.choice(no_mistakes_feedback) + " You made no mistakes!"
    else:
        # Search attribute records and get which attributes match with
        # the previously calculated highest mistake count.
        for key in incorrect_results:
            if incorrect_results[key] == most_attributes_wrong:
                worst_attributes[key] = most_attributes_wrong

        # Get feedback statement for each attribute
        user_data_dynamodb = dynamodb.Table('TutorTable')
        for key in worst_attributes:
            response = user_data_dynamodb.query(KeyConditionExpression=Key('Attribute')\
                .eq(key))
            for i in response['Items']:
                feedback_statement = i['FeedbackStatement']
            feedback_statements[key] = feedback_statement

    return feedback_statements

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response(session):
    """ Standard welcome response to the skill, normally said by Alexa if
    a user invokes the skill without an intent.
    """

    card_title = "Welcome"
    session_attributes = {}
    session_user = session.get('user', {})
    user_id = session_user['userId']
    if user_exists(user_id):
        speech_output = (
            "<speak>" + "Welcome back! " +
            "I can either quiz you or tutor you. If you want questions " +
            "just say quiz me, or if you want tutoring, say teach me." + "</speak>"
        )
    else:
        add_user(user_id)
        speech_output = (
            "<speak>" + "Welcome to the PLC Counter Instruction Tutor! " +
            "I can either quiz you or tutor you. If you want questions " +
            "just say quiz me, or if you want tutoring, say teach me." + "</speak>"
        )

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "I didn't quite get that. I can either quiz you or tutor you. " \
                    "Which would you like me to do?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request(session):
    """ Ends the Alexa session when a user requests it. """
    session_user = session.get('user', {})
    user_id = session_user['userId']
    reset_user(user_id)

    card_title = "Session Ended"
    speech_output = "<speak>" + "Thanks for trying out the Alexa PLC counter instruction tutor. " \
                    "Have a nice day!" + "</speak>"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def handle_repeat_request(intent, session):
    """ Repeats the previous speech output. If there is a previous
    session to repeat from, it will be repeated. Otherwise a new
    session will be started. """

    if 'attributes' not in session or 'SpeechOutput' not in session['attributes']:
        return get_welcome_response(session)
    else:
        previous_attributes = session.get('attributes', {})
        card_title = previous_attributes['CardTitle']
        speech_output = previous_attributes['SpeechOutput']
        reprompt_text = previous_attributes['RepromptText']
        should_end_session = False

        return build_response(previous_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

def handle_help_request(intent, session):
    """ Handles a user's request for help. """

    card_title = "Help"

    # Depending on the current stage of the interaction, a different
    # help response is provided to the user.
    session_details = session.get('attributes', {})
    if session_details["QuestionType"] == "TrueFalse":
        speech_output = (
            "<speak>" + "For a true or false question, you simply need to reply "
            "with either the word true, or the word false. Would you like "
            "another question?" + "</speak>"
        )
    elif session_details["QuestionType"] == "SelectValue":
        speech_output = (
            "<speak>" + "For a short answer question, you need to reply with the "
            "correct answer, which I will be able to recognize. "
            "Would you like another question?" + "</speak>"
        )
    reprompt_text = "I didn't quite get that; would you like another question?"
    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "HelpRequest",
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_question_from_session(intent, session):
    """ Randomly generates question and prepares the speech with
    question to reply to the user.
    """
    session_user = session.get('user', {})
    user_id = session_user['userId']
    if user_exists(user_id):
        pass
    else:
        add_user(user_id)

    # Check user's status with correct/incorrect questions and update level
    # accordingly before generating a new question.
    current_user_level = update_user_level(user_id)

    # Generate either a True/False or Select Value type question and relay it
    # back to the user.
    #question_type_num = random.randint(0, 1)
    question_type_num = 0

    if question_type_num == 0:
        question_full = generate_true_false(current_user_level)

        card_title = "True or False Question"
        #speech_output = (
        #    "<speak>" + '"<prosody rate="slow">"' + "True or False? "
        #    + question_full[1] + "</prosody>" + "</speak>"
        #)
        speech_output = (
            "<speak>" + "True or False? "
            + question_full[1] + "</speak>"
        )
        reprompt_text = (
            "I didn't get your answer. Please reply True or "
            "False about this statement: " + question_full[1]
        )
        session_attributes = {
            "CardTitle": card_title,
            "SpeechOutput": speech_output,
            "RepromptText": reprompt_text,
            "CurrentStage": "GenerateQuestion",
            "QuestionType": "TrueFalse",
            "QuestionAttribute": question_full[0],
            "Question": question_full[1],
            "PartialAnswer": question_full[2],
            "FullAnswer": question_full[3],
        }
        should_end_session = False

    elif question_type_num == 1:
        question_full = generate_select_part(current_user_level)

        card_title = "Select Part Question"
        speech_output = (
            "<speak>" + question_full[1]
            + " Your options are: Counter Down (CTD), Counter Up (CTU), or both."
            + "</speak>"
        )
        reprompt_text = (
            "I didn't get your answer. Please reply either Counter Down (CTD), "
            "Counter Up (CTU), or both."
        )
        session_attributes = {
            "CardTitle": card_title,
            "SpeechOutput": speech_output,
            "RepromptText": reprompt_text,
            "CurrentStage": "GenerateQuestion",
            "QuestionType": "SelectPart",
            "QuestionAttribute": question_full[0],
            "Question": question_full[1],
            "Answer": question_full[2],
        }
        should_end_session = False

    elif question_type_num == 2:
        question_full = generate_select_value()

        card_title = "Short Answer Question"
        speech_output = (
            "<speak>" + question_full[0]
            + "</speak>"
        )
        reprompt_text = (
            "I didn't get your answer. Please answer the following question: "
            + question_full[0]
        )
        session_attributes = {
            "CardTitle": card_title,
            "SpeechOutput": speech_output,
            "RepromptText": reprompt_text,
            "CurrentStage": "GenerateQuestion",
            "QuestionType": "SelectValue",
            "Question": question_full[0],
            "Answer": question_full[1],
        }
        should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def check_answer_in_session(intent, session):
    """ Takes in user's answer to question, checks answer, and preps
    output speech to tell user if they are correct or not.
    """

    card_title = "Answer Response"
    session_user = session.get('user', {})
    user_id = session_user['userId']

    # Depending on whether the user is responding to a True/False
    # question or a SelectValue question, the user's answer is checked
    # vs. the actual answer to the question and informed whether
    # they are correct or incorrect.
    user_answer = intent['slots']['Answer']['value']
    question_details = session.get('attributes', {})
    if question_details["QuestionType"] == "TrueFalse":
        if (question_details["PartialAnswer"] == "true") \
            and (user_answer == "true"):
            speech_output = (
                "<speak>" + "True is correct. " +
                question_details["FullAnswer"] + '"<break time="0.75s"/>"' +
                "Would you like another question?" + "</speak>"
            )
            increment_question_correct(user_id, question_details["QuestionAttribute"])
        elif (question_details["PartialAnswer"] == "false") \
            and (user_answer == "false"):
            speech_output = (
                "<speak>" + "False is correct. " +
                question_details["FullAnswer"] + '"<break time="0.75s"/>"' +
                "Would you like another question?" + "</speak>"
            )
            increment_question_correct(user_id, question_details["QuestionAttribute"])
        elif (question_details["PartialAnswer"] == "true") \
            and (user_answer == "false"):
            speech_output = (
                "<speak>" + "Sorry, the correct answer is True. " +
                question_details["FullAnswer"] + '"<break time="0.75s"/>"' +
                "Would you like another question?" + "</speak>"
            )
            increment_question_incorrect(user_id, question_details["QuestionAttribute"])
        elif (question_details["PartialAnswer"] == "false") \
            and (user_answer == "true"):
            speech_output = (
                "<speak>" + "Sorry, the correct answer is False. " +
                question_details["FullAnswer"] + '"<break time="0.75s"/>"' +
                "Would you like another question?" + "</speak>"
            )
            increment_question_incorrect(user_id, question_details["QuestionAttribute"])
    elif question_details["QuestionType"] == "SelectPart":
        if (question_details['Answer'] == "CTU")\
        and (user_answer == "counter up" or user_answer == "CTU"):
            speech_output = (
                "<speak> Counter Up is the correct answer. " + '"<break time="0.75s"/>"' +
                "Would you like another question? </speak>"
            )
            increment_question_correct(user_id, question_details["QuestionAttribute"])
        elif (question_details['Answer'] == "CTD")\
        and (user_answer == "counter down" or user_answer == "CTD"):
            speech_output = (
                "<speak> Counter Down is the correct answer. " + '"<break time="0.75s"/>"' +
                "Would you like another question? </speak>"
            )
            increment_question_correct(user_id, question_details["QuestionAttribute"])
        elif (question_details['Answer'] == "Both")\
        and (user_answer == "both" or user_answer == "both counter up and counter down"\
            or user_answer == "both CTU and CTD"):
            speech_output = (
                "<speak> Both is the correct answer. " + '"<break time="0.75s"/>"' +
                "Would you like another question? </speak>"
            )
            increment_question_correct(user_id, question_details["QuestionAttribute"])
        else:
            speech_output = (
                "<speak>" + user_answer + " is incorrect." + '"<break time="0.75s"/>"' +
                "Would you like another question? </speak>"
            )
            increment_question_incorrect(user_id, question_details["QuestionAttribute"])
    elif question_details["QuestionType"] == "SelectValue":
        if user_answer in question_details["Answer"]:
            speech_output = (
                "<speak>" + "Your answer is correct. " +
                user_answer + '"<break time="0.75s"/>"' +
                "Would you like another question?" + "</speak>"
            )
        else:
            speech_output = (
                "<speak>" + "Your answer is incorrect. "
                + '"<break time="0.75s"/>"' + "Would you like another question?" + "</speak>"
            )
    reprompt_text = "I didn't quite catch that. Can you repeat your answer?"
    should_end_session = False

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "CheckAnswer",
        "QuestionType": question_details["QuestionType"]
    }

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def give_quiz_feedback(session):
    """ Provides feedback to the user after they finish a question session
    in the form of telling them what attribute(s) of question they got
    wrong the most, and asks if they want to review them. """

    card_title = "Quiz Feedback"
    session_user = session.get('user', {})
    user_id = session_user['userId']

    feedback_statements = get_attribute_feedback(user_id)
    if "None" in feedback_statements:
        speech_output = "<speak>" + feedback_statements["None"] + " "
        speech_output += "If you want to be quizzed more, say quiz me; "
        speech_output += "if you want to be tutored, say tutor me; "
        speech_output += "if you want to quit, say 'I'm done.'" + "</speak>"

        reprompt_text = "I didn't quite get that. Would you like me to quiz you, "\
        + "or tutor you? Or if you would like to quit, say 'I'm done.'"
    else:
        speech_output = "<speak>" + "I think you should take a look at: "
        for key in feedback_statements:
            speech_output += feedback_statements[key] + ", and "
        speech_output = speech_output.rstrip(", and")
        speech_output += ". Would you like to review?" + "</speak>"

        reprompt_text = "I didn't quite catch that. If you would like to review "\
            + "say yes. If not, say no."

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "GiveQuizFeedback",
        "QuizFeedback": feedback_statements
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def review_quiz_feedback(session):
    """ Provides the user with review for the material they're the weakest on. """

    card_title = "Quiz Review"

    speech_output = "<speak>"
    feedback_statements = session['attributes']["QuizFeedback"]
    print(feedback_statements)
    for key in feedback_statements:
        tutoring_statements = get_tutoring_statement(attribute=key)
        print(tutoring_statements)
        for index in range(len(tutoring_statements)):
            speech_output += tutoring_statements[index] + " "
    speech_output = speech_output.rstrip(" ")
    speech_output += '"<break time="0.75s"/>"'
    speech_output += ". Would you like me to quiz you, or tutor you? "
    speech_output += "Or if you would like to quit instead, say 'I'm done.'"
    speech_output += "</speak>"

    reprompt_text = "I didn't quite get that. Would you like me to quiz you, "\
        + "or tutor you? Or if you would like to quit, say 'I'm done.'"

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "ReviewQuizFeedback"
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_tutor_request(intent, session):
    """ Provides tutoring information output. """

    card_title = "Teaching Counter Instructions"
    session_user = session.get('user', {})
    user_id = session_user['userId']

    current_statement_level = get_statement_level(user_id)
    current_order_level = get_order_level(user_id)
    max_order_level = get_max_order_levels(current_statement_level)
    max_statement_level = get_max_statement_level()

    if current_statement_level <= max_statement_level:
        # This if statement essentially loops through all the orders of
        # a given level while a user keeps requesting it.
        if current_order_level <= max_order_level:
            tutoring_statement = get_tutoring_statement(
                current_statement_level,
                current_order_level
            )
            increment_order_level(user_id)
            speech_output = "<speak>"
            for index in range(len(tutoring_statement)):
                speech_output += tutoring_statement[index] + " "
            speech_output += '"<break time="0.75s"/>"'
            speech_output += "Say next to go to the next statement."
            speech_output += "</speak>"
            reprompt_text = "I didn't quite catch that. Say next to go to the "\
                + "next tutoring statement."
        else:
            # If we've reached the max order, then we know we have to
            # move the statement level up by 1, so we do that and
            # reset the order to start from the beginning.
            reset_order_level(user_id)
            increment_statement_level(user_id)
            current_statement_level = get_statement_level(user_id)
            current_order_level = get_order_level(user_id)
            # This particular if statement is for checking if we've reached
            # the max level, which signifies the end of the tutoring session
            if current_statement_level <= max_statement_level:
                if current_order_level <= max_order_level:
                    tutoring_statement = get_tutoring_statement(
                        current_statement_level,
                        current_order_level
                    )
                    increment_order_level(user_id)
                    speech_output = "<speak>"
                    for index in range(len(tutoring_statement)):
                        speech_output += tutoring_statement[index] + " "
                    speech_output += '"<break time="0.75s"/>"'
                    speech_output += "Say next to go to the next statement."
                    speech_output += "</speak>"
                    reprompt_text = "I didn't quite catch that. Say next to go to the "\
                        + "next tutoring statement."
            else:
                reset_statement_level(user_id)
                reset_order_level(user_id)
                speech_output = (
                    "<speak>" + "You've reached the end of the " +
                    "tutoring session. Great work! I can now quiz you if you say quiz me, " +
                    "tutor you again if you say tutor me, or you can quit by saying 'I'm done.'" +
                    "</speak>"
                )
                reprompt_text = "I didn't quite catch that. Would you like me to tutor you again, "\
                    + "or quiz you? If you want to quit instead, say 'I'm done.'"

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "Tutoring"
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_options_menu():
    """ A voice-based options menu. """

    card_title = "What would you like to do?"

    speech_output = (
        "<speak> Would you like me to quiz you, or tutor you? " +
        "If you would like to quit, say 'I'm done'.</speak>"
    )

    reprompt_text = "I didn't quite get that. Would you like me to quiz you, "\
        + "or tutor you? If you would like to quit, say 'I'm done'."

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "OptionsMenu"
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response(session)

def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handler
    if intent_name == "TutorIntent":
        return handle_tutor_request(intent, session)
    elif intent_name == "QuestionIntent":
        return get_question_from_session(intent, session)
    elif intent_name == "AnswerIntent":
        return check_answer_in_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return handle_help_request(intent, session)
    elif intent_name == "AMAZON.RepeatIntent":
        return handle_repeat_request(intent, session)
    elif intent_name == "AMAZON.StartOverIntent":
        reset_user(session['user']['userId'])
        return get_welcome_response(session)
    elif intent_name == "AMAZON.NextIntent":
        if session['attributes']['CurrentStage'] == "Tutoring":
            return handle_tutor_request(intent, session)
    elif intent_name == "AMAZON.YesIntent":
        if session['attributes']['CurrentStage'] == "CheckAnswer":
            return get_question_from_session(intent, session)
        elif session['attributes']['CurrentStage'] == "HelpRequest":
            return get_question_from_session(intent, session)
        elif session['attributes']['CurrentStage'] == "GiveQuizFeedback":
            return review_quiz_feedback(session)
    elif intent_name == "AMAZON.NoIntent":
        if session['attributes']['CurrentStage'] == "CheckAnswer":
            return give_quiz_feedback(session)
        elif session['attributes']['CurrentStage'] == "HelpRequest":
            return handle_session_end_request(session)
        elif session['attributes']['CurrentStage'] == "GiveQuizFeedback":
            return get_options_menu()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request(session)
    else:
        reset_user(session['user']['userId'])
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here
    reset_user(session['user']['userId'])

# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
