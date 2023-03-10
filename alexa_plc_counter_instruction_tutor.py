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

def build_speechlet_response(title, speech_output, card_output, reprompt_text, should_end_session):
    """ Helper that builds the speechlet response. """

    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': speech_output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': card_output
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
            if current_total_correct % 4 == 0:
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
                    and current_total_correct % 4 != 0):
                increment_question_level(user_id)
                decrement_question_level(user_id)
            elif current_total_correct % 4 == 0 and current_total_incorrect % 3 == 0:
                decrement_question_level(user_id)
            elif current_total_correct % 4 == 0 and current_total_incorrect % 3 != 0:
                increment_question_level(user_id)
            elif current_total_correct % 4 != 0 and current_total_incorrect % 3 == 0:
                decrement_question_level(user_id)
            else:
                increment_question_level(user_id)
                decrement_question_level(user_id)

    # Keeps user level limited to 4
    if get_question_level(user_id) > 4:
        while (get_question_level(user_id) > 4):
            decrement_question_level(user_id)
    if get_question_level(user_id) < 1:
        while (get_question_level(user_id) < 1):
            increment_question_level(user_id)     
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

    match_found = False
    for index in range(0, len(all_output_question_values)):
        if all_output_question_parts[index] != output_question_part\
        and all_output_question_values[index] == output_question_value:
            match_found = True

    if match_found:
        output_question_answer = "Both"
    else:
        output_question_answer = output_question_part

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
    positive_feedback_responses = [
        "Nice work!",
        "Great job!",
        "Good job!",
        "Nice job!",
        "Very good!",
        "Great work!",
        "Good work!",
        "Awesome work!",
        "Superb!",
        "Excellent!",
        "Fantastic!",
        "Bullseye!",
        "Right on the money!",
        "Well done!",
        "Keep it up!",
        "Way to go!",
        "Nicely done!",
        "Good answer!",
        "Nice one!",
        "Outstanding!"
    ]
    if most_attributes_wrong == 0:
        feedback_statements["None"] = random.choice(positive_feedback_responses) + " You made no mistakes."
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

def card_text_format(speech_output):
    """ Formats speech output text into card format (basically removes
    the code-like SSML text)"""

    remove_words = [
        '<speak>',
        '</speak>',
        '"<prosody rate="90%" pitch="high">"',
        '</prosody>',
        '"<break time="0.75s"/>"',
        '"<prosody rate="90%">"'
    ]

    card_output = speech_output
    for index in range(0, len(remove_words)):
        card_output = card_output.replace(remove_words[index], "")
    return card_output
# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response(session):
    """ Standard welcome response to the skill, normally said by Alexa if
    a user invokes the skill without an intent.
    """

    card_title = "Welcome"
    session_attributes = {
        "CurrentStage": "WelcomeResponse",
    }
    session_user = session.get('user', {})
    user_id = session_user['userId']
    if user_exists(user_id):
        speech_output = (
            "<speak>" + "Welcome back! " +
            "Would you like me to quiz you, or tutor you? " + "</speak>"
        )
        card_output = card_text_format(speech_output)
    else:
        add_user(user_id)
        speech_output = (
            "<speak>" + "Welcome to the PLC Counter Instruction Tutor! " +
            "Would you like me to quiz you, or tutor you?" + "</speak>"
        )
        card_output = card_text_format(speech_output)

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "I didn't quite get that. I can either quiz you or tutor you. " \
                    "Which would you like me to do?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_output, reprompt_text, should_end_session))

def handle_session_end_request(session):
    """ Ends the Alexa session when a user requests it. """

    card_title = "Session Ended"
    speech_output = "<speak>" + "Thanks for trying out the PLC Counter Instruction Tutor. " \
                    "Have a nice day!" + "</speak>"
    card_output = card_text_format(speech_output)

    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, card_output, None, should_end_session))

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
        card_output = card_text_format(speech_output)
        reprompt_text = previous_attributes['RepromptText']
        should_end_session = False

        return build_response(previous_attributes, build_speechlet_response(
            card_title, speech_output, card_output, reprompt_text, should_end_session))

def handle_help_request(intent, session):
    """ Handles a user's request for help. """

    card_title = "Help"

    # Depending on the current stage of the interaction, a different
    # help response is provided to the user. 
    # Note to me: Improve these help responses in the future
    session_details = session.get('attributes', {})
    if session_details["CurrentStage"] == "WelcomeResponse":
        speech_output = (
            "<speak>" + "Welcome to PLC Counter Instruction Tutor. " +
            "I can either quiz you or tutor you. I recommend that " +
            "you start off with tutoring to go over the material, " +
            "and then test yourself with some questions." + '"<break time="0.75s"/>"' + 
            "Would you like me to tutor you or quiz you?" + "</speak>"
        )
        card_output = card_text_format(speech_output)
    elif session_details["CurrentStage"] == "GenerateQuestion":
        if session_details["QuestionType"] == "TrueFalse":
            speech_output = (
                "<speak>" + "For a true or false question, you need to reply " +
                "with either true, or false. Would you like another question?" + "</speak>"
            )
            card_output = card_text_format(speech_output)
        elif session_details["QuestionType"] == "SelectPart":
            speech_output = (
                "<speak>" + "For a select instruction question, you need to reply with " +
                "one of the provided answer choices. Would you like another question?" + "</speak>"
            )
            card_output = card_text_format(speech_output)
    elif session_details["CurrentStage"] == "CheckAnswer":
        if session_details["QuestionType"] == "TrueFalse":
            speech_output = (
                "<speak>" + "For a true or false question, you need to reply " +
                "with either true, or false. Would you like another question?" + "</speak>"
            )
            card_output = card_text_format(speech_output)
        elif session_details["QuestionType"] == "SelectPart":
            speech_output = (
                "<speak>" + "For a select instruction question, you need to reply with " +
                "one of the provided answer choices. Would you like another question?" + "</speak>"
            )
            card_output = card_text_format(speech_output)
    elif session_details["CurrentStage"] == "GiveQuizFeedback":
        speech_output = (
            "<speak>" + "The feedback stage is to help you improve on your weakest " +
            "areas. " + '"<break time="0.75s"/>"' + "Would you like me to tutor you, " +
            "quiz you again, or would you like to end this study session?" + "</speak>"
        )
        card_output = card_text_format(speech_output)    
    elif session_details["CurrentStage"] == "ReviewQuizFeedback":
        speech_output = (
            "<speak>" + "The feedback stage is to help you improve on your weakest " +
            "areas. " + '"<break time="0.75s"/>"' + "Would you like me to tutor you, " +
            "quiz you again, or would you like to end this study session?" + "</speak>"
        )
        card_output = card_text_format(speech_output)      
    elif session_details["CurrentStage"] == "Tutoring":
        speech_output = (
            "<speak>" + "During the tutoring stage I go over the basics of counter " +
            "instructions in PLC ladder logic programming. " + '"<break time="0.75s"/>"' + 
            "Would you like to return to tutoring, for me to quiz you, or would " +
            "you like to end this study session?" + "</speak>"
        )
        card_output = card_text_format(speech_output)  
    elif session_details["CurrentStage"] == "OptionsMenu":
        speech_output = (
            "<speak>" + "I can either quiz you or tutor you about counter " +
            "instructions in PLC ladder logic programming. " + '"<break time="0.75s"/>"' + 
            "Would you like me to tutor you, quiz you, or would " +
            "you like to end this study session?" + "</speak>"
        )
        card_output = card_text_format(speech_output)         
    reprompt_text = "I didn't quite get that; what would you like to do?"
    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "HelpRequest",
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_output, reprompt_text, should_end_session))

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
    question_type_num = random.randint(0, 1)

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
        card_output = card_text_format(speech_output)
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
            + " Is this CTU, CTD, or both?"
            + "</speak>"
        )
        card_output = card_text_format(speech_output)
        reprompt_text = (
            "I didn't get your answer. Please reply either CTD, "
            "CTU, or both."
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

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_output, reprompt_text, should_end_session))

def check_answer_in_session(intent, session):
    """ Takes in user's answer to question, checks answer, and preps
    output speech to tell user if they are correct or not.
    """

    card_title = "Answer Response"
    session_user = session.get('user', {})
    user_id = session_user['userId']

    positive_feedback_responses = [
        "Nice work!",
        "Great job!",
        "Good job!",
        "Nice job!",
        "Very good!",
        "Great work!",
        "Good work!",
        "Awesome work!",
        "Superb!",
        "Excellent!",
        "Fantastic!",
        "Bullseye!",
        "Right on the money!",
        "Well done!",
        "Keep it up!",
        "Way to go!",
        "Nicely done!",
        "Good answer!",
        "Nice one!",
        "Outstanding!"
    ]
    more_question_responses = [
        "Would you like another question?",
        "Do you want another question?",
        "Do you want to try another one?",
        "Would you like to try another one?",
        "Would you like a new question?",
        "Do you want a new question?",
    ]

    # Check if there's no value provided for the answer in the JSON request.
    # If there is a value provided, but it's not a valid answer, then that
    # issue is handled in the question feedback section below.
    try:
        user_answer = intent['slots']['Answer']['value']
    except KeyError:
        user_answer = "NoValue"
    if user_answer is None:
        user_answer = "NoValue"

    # User's answer is checked depending on the type of question they're
    # answering and given feedback about whether they are correct/incorrect.
    question_details = session.get('attributes', {})
    if question_details["QuestionType"] == "TrueFalse":
        if user_answer == "true" or user_answer == "false":
            if (question_details["PartialAnswer"] == "true") \
                and (user_answer == "true"):
                speech_output = (
                    "<speak>" + '"<prosody rate="90%" pitch="high">"'+ random.choice(positive_feedback_responses) +
                    "</prosody>" + " True is correct. " +
                    question_details["FullAnswer"] + '"<break time="0.75s"/>"' + " " +
                    random.choice(more_question_responses) + "</speak>"
                )
                card_output = card_text_format(speech_output)
                increment_question_correct(user_id, question_details["QuestionAttribute"])
            elif (question_details["PartialAnswer"] == "false") \
                and (user_answer == "false"):
                speech_output = (
                    "<speak>" + '"<prosody rate="90%" pitch="high">"'+ random.choice(positive_feedback_responses) +
                    "</prosody>" + " False is correct. " +
                    question_details["FullAnswer"] + '"<break time="0.75s"/>"' + " " +
                    random.choice(more_question_responses) + "</speak>"
                )
                card_output = card_text_format(speech_output)
                increment_question_correct(user_id, question_details["QuestionAttribute"])
            elif (question_details["PartialAnswer"] == "true") \
                and (user_answer == "false"):
                speech_output = (
                    "<speak>" + "Sorry, the correct answer is True. " +
                    question_details["FullAnswer"] + " " +
                    random.choice(more_question_responses) + "</speak>"
                )
                card_output = card_text_format(speech_output)
                increment_question_incorrect(user_id, question_details["QuestionAttribute"])
            elif (question_details["PartialAnswer"] == "false") \
                and (user_answer == "true"):
                speech_output = (
                    "<speak>" + "Sorry, the correct answer is False. " +
                    question_details["FullAnswer"] + " " +
                    random.choice(more_question_responses) + "</speak>"
                )
                card_output = card_text_format(speech_output)
                increment_question_incorrect(user_id, question_details["QuestionAttribute"])
        else:
            speech_output = (
                "<speak>" + "Sorry, your answer is invalid. For a true or false question, " +
                "please make sure your answer is either true or false. " + '"<break time="0.75s"/>"' +
                "Would you like another question? </speak>"
            )
            card_output = card_text_format(speech_output)
    elif question_details["QuestionType"] == "SelectPart":
        user_answer = user_answer.replace("&", "and")
        if (
                user_answer == "counter up" or
                user_answer == "CTU" or
                user_answer == "counter down" or
                user_answer == "CTD" or
                user_answer == "both" or
                user_answer == "both counter up and counter down" or
                user_answer == "both CTUandC TD"
        ):
            if (question_details['Answer'] == "CTU")\
            and (user_answer == "counter up" or user_answer == "CTU"):
                speech_output = (
                    "<speak>" + '"<prosody rate="90%" pitch="high">"'+ random.choice(positive_feedback_responses) +
                    "</prosody>" + " CTU is the correct answer. " + '"<break time="0.75s"/>"' +
                    "Would you like another question? </speak>"
                )
                card_output = card_text_format(speech_output)
                increment_question_correct(user_id, question_details["QuestionAttribute"])
            elif (question_details['Answer'] == "CTD")\
            and (user_answer == "counter down" or user_answer == "CTD"):
                speech_output = (
                    "<speak>" + '"<prosody rate="90%" pitch="high">"'+ random.choice(positive_feedback_responses) +
                    "</prosody>" + " CTD is the correct answer. " + '"<break time="0.75s"/>"' +
                    "Would you like another question? </speak>"
                )
                card_output = card_text_format(speech_output)
                increment_question_correct(user_id, question_details["QuestionAttribute"])
            elif (question_details['Answer'] == "Both")\
            and (user_answer == "both" or user_answer == "both counter up and counter down"\
                or user_answer == "both CTUandC TD"):
                speech_output = (
                    "<speak>" + '"<prosody rate="90%" pitch="high">"'+ random.choice(positive_feedback_responses) +
                    "</prosody>" + " Both is the correct answer. " + '"<break time="0.75s"/>"' +
                    "Would you like another question? </speak>"
                )
                card_output = card_text_format(speech_output)
                increment_question_correct(user_id, question_details["QuestionAttribute"])
            else:
                speech_output = (
                    "<speak>" + "Sorry, your answer is incorrect. " + '"<break time="0.75s"/>"' +
                    " The correct answer is " + question_details['Answer'] + ". " +
                    "Would you like another question? </speak>"
                )
                card_output = card_text_format(speech_output)
                increment_question_incorrect(user_id, question_details["QuestionAttribute"])
        else:
            speech_output = (
                "<speak>" + "Sorry, your answer is invalid. Please make sure to pick one of the " +
                "listed options for a select instruction question. " + '"<break time="0.75s"/>"' +
                "Would you like another question? </speak>"
            )
            card_output = card_text_format(speech_output)
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
        card_title, speech_output, card_output, reprompt_text, should_end_session))

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
        speech_output += "Would you like me to quiz you again, "
        speech_output += "tutor you, or would you like to end this study session? "
        speech_output += "</speak>"
        card_output = card_text_format(speech_output)
        reprompt_text = "I didn't quite get that. Would you like me to quiz you, "\
        + "tutor you, or would you like to end this study session?"
    else:
        speech_output = "<speak>" + "I think you should take a look at: "
        for key in feedback_statements:
            speech_output += feedback_statements[key] + ", and "
        speech_output = speech_output.rstrip(", and")
        speech_output += ". Would you like to review?" + "</speak>"
        card_output = card_text_format(speech_output)
        reprompt_text = "I didn't quite catch that. Would you like to review?"

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "GiveQuizFeedback",
        "QuizFeedback": feedback_statements
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_output, reprompt_text, should_end_session))

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
    speech_output += "Would you like me to quiz you again, "
    speech_output += "tutor you, or would you like to end this study session? "
    speech_output += "</speak>"
    card_output = card_text_format(speech_output)
    reprompt_text = "I didn't quite get that. Would you like me to quiz you, "\
        + "tutor you, or would you like to end this study session?"

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "ReviewQuizFeedback"
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_output, reprompt_text, should_end_session))

def handle_tutor_request(intent, session):
    """ Provides tutoring information output. """

    card_title = "Teaching Counter Instructions"
    session_user = session.get('user', {})
    user_id = session_user['userId']

    tutoring_intro = [
        "Let's begin!",
        "Let's get started!"
    ]

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
            if current_statement_level == 1 and current_order_level == 1:
                speech_output += random.choice(tutoring_intro) + " "
            for index in range(len(tutoring_statement)):
                speech_output += tutoring_statement[index] + " "
            speech_output += '"<break time="0.75s"/>"'
            if max_order_level - current_order_level == 0:
                speech_output += "There are no statements left in this level. "
                speech_output += "Would you like me to go to the next statement level, or repeat this statement?"
                reprompt_text = "I didn't quite catch that. Would you like me "\
                    + "to go to the next tutoring statement level, or repeat this statement?"
            else:
                speech_output += "There are " + str(max_order_level-current_order_level) + " statements left. "
                speech_output += "Would you like me to go to the next statement, or repeat this statement?"
                reprompt_text = "I didn't quite catch that. Would you like me to go to the "\
                    + "next tutoring statement, or repeat this statement?"
            speech_output += "</speak>"
            card_output = card_text_format(speech_output)
        else:
            # If we've reached the max order, then we know we have to
            # move the statement level up by 1, so we do that and
            # reset the order to start from the beginning.
            reset_order_level(user_id)
            increment_statement_level(user_id)
            current_statement_level = get_statement_level(user_id)
            current_order_level = get_order_level(user_id)
            max_order_level = get_max_order_levels(current_statement_level)
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
                    if max_order_level - current_order_level == 0:
                        speech_output += "There are no statements left in this level. "
                        speech_output += "Would you like me to go to the next statement level, or repeat this statement?"
                        reprompt_text = "I didn't quite catch that. Would you like me "\
                            + "to go to the next tutoring statement level, or repeat this statement?"
                    else:
                        speech_output += "There are " + str(max_order_level-current_order_level) + " statements left. "
                        speech_output += "Would you like me to go to the next statement, or repeat this statement?"
                        reprompt_text = "I didn't quite catch that. Would you like me to go to the "\
                            + "next tutoring statement, or repeat this statement?"
                    speech_output += "</speak>"
                    card_output = card_text_format(speech_output)
            else:
                reset_statement_level(user_id)
                reset_order_level(user_id)
                speech_output = (
                    "<speak>" + "You've reached the end of the tutoring session. Great work! " +
                    "Would you like me to quiz you now, tutor you again, or would you like to end this study session?" +
                    "</speak>"
                )
                card_output = card_text_format(speech_output)
                reprompt_text = "I didn't quite catch that. Would you like me to tutor you again, "\
                    + ", quiz you, or would you like to end this study session?"

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "Tutoring"
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_output, reprompt_text, should_end_session))

def get_options_menu():
    """ A voice-based options menu. """

    card_title = "What would you like to do?"

    speech_output = (
        "<speak> Would you like me to quiz you, tutor you, " +
        "or would you like to end this study session? </speak>"
    )
    card_output = card_text_format(speech_output)
    reprompt_text = "I didn't quite get that. Would you like me to quiz you, "\
        + "tutor you, or do you want to end this study session?"

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "OptionsMenu"
    }
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_output, reprompt_text, should_end_session))

def handle_dont_know(session):
    session_user = session.get('user', {})
    user_id = session_user['userId']

    question_details = session.get('attributes', {})
    increment_question_incorrect(user_id, question_details["QuestionAttribute"])

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
    elif intent_name == "DontKnowIntent":
        if session['attributes']['CurrentStage'] == "GenerateQuestion":
            handle_dont_know(session)
            return get_question_from_session(intent, session)
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
            return get_options_menu()
        elif session['attributes']['CurrentStage'] == "GiveQuizFeedback":
            return get_options_menu()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request(session)
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

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
    if (event['session']['application']['applicationId'] != "amzn1.ask.skill.c32dfdf8-721b-4772-a801-98941de04300"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
