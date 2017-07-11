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

# --------------- Functions used by skill control functions for operations ------------------

def update_user_level():
    """ Keeps track of and updates the user's question difficulty level as they
    keep answering questions. """

    # Store previous totals
    previous_total_correct = update_user_database("GetPreviousTotalCorrect")
    previous_total_incorrect = update_user_database("GetPreviousTotalIncorrect")

    # Conditionals to update level, < 4 because 4 is the max difficulty level
    if update_user_database("GetLevel") < 4:
        # Get the current totals. These values differ from the previous total
        # values stored above because these values take into account the question the
        # user answered just before reaching this stage and asking for a new question.
        current_total_correct = update_user_database("GetTotalCorrect")
        current_total_incorrect = update_user_database("GetTotalIncorrect")

        # Conditionals to deal with initial conditions that could happen when
        # the user first starts answering questions.
        if current_total_correct == 0 and current_total_incorrect == 0:
            update_user_database("IncrementLevel")
            update_user_database("DecrementLevel")
        elif current_total_correct != 0 and current_total_incorrect == 0:
            if current_total_correct % 5 == 0:
                update_user_database("IncrementLevel")
            else:
                update_user_database("IncrementLevel")
                update_user_database("DecrementLevel")
        elif current_total_correct == 0 and current_total_incorrect != 0:
            if current_total_incorrect % 3 == 0:
                if update_user_database("GetLevel") == 1:
                    update_user_database("IncrementLevel")
                    update_user_database("DecrementLevel")
                else:
                    update_user_database("DecrementLevel")
            else:
                update_user_database("IncrementLevel")
                update_user_database("DecrementLevel")

        # The following conditionals deal with conditions that can happen after a user
        # has questions both right and wrong.
        else:
            if (previous_total_correct == current_total_correct
                    and current_total_incorrect % 3 != 0)\
                or (previous_total_incorrect == current_total_incorrect
                    and current_total_correct % 5 != 0):
                update_user_database("IncrementLevel")
                update_user_database("DecrementLevel")
            elif current_total_correct % 5 == 0 and current_total_incorrect % 3 == 0:
                update_user_database("DecrementLevel")
            elif current_total_correct % 5 == 0 and current_total_incorrect % 3 != 0:
                update_user_database("IncrementLevel")
            elif current_total_correct % 5 != 0 and current_total_incorrect % 3 == 0:
                update_user_database("DecrementLevel")
            else:
                update_user_database("IncrementLevel")
                update_user_database("DecrementLevel")

    # Update the previous totals to current totals
    update_user_database("UpdatePreviousTotalCorrect")
    update_user_database("UpdatePreviousTotalIncorrect")

    new_level = update_user_database("GetLevel")
    return new_level

def update_user_database(info_request, attribute_type="None"):
    """ Allows caller to obtain information about a user and modify attributes
    of said user."""

    # Set up access to the user information database on DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_data_dynamodb = dynamodb.Table('LLPTutor_UserData')

    # Depending on the type of user information request, perform different
    # action.
    # If the request is IncrementCorrect or IncrementIncorrect, then
    # whichever type of question (attribute) the user got right or wrong is
    # incremented, and the total sum of correct or incorrect over all the
    # attributes is returned.
    if info_request == "GetTotalCorrect":
        counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in counter_current_value['Items']:
            counter_result = (i['CounterCorrect'])
        counter_result_sum = sum(counter_result.values())
        return counter_result_sum
    elif info_request == "GetTotalIncorrect":
        counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in counter_current_value['Items']:
            counter_result = (i['CounterIncorrect'])
        counter_result_sum = sum(counter_result.values())
        return counter_result_sum
    elif info_request == "UpdatePreviousTotalCorrect":
        counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in counter_current_value['Items']:
            counter_result = (i['CounterCorrect'])
        counter_result_sum = sum(counter_result.values())

        response = user_data_dynamodb.update_item(
            Key={
                'UserID': "Tester",
            },
            UpdateExpression="set PreviousTotalCorrect = :val",
            ExpressionAttributeValues={
                ':val': counter_result_sum
            },
            ReturnValues="UPDATED_NEW"
        )
    elif info_request == "UpdatePreviousTotalIncorrect":
        counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in counter_current_value['Items']:
            counter_result = (i['CounterIncorrect'])
        counter_result_sum = sum(counter_result.values())

        response = user_data_dynamodb.update_item(
            Key={
                'UserID': "Tester",
            },
            UpdateExpression="set PreviousTotalIncorrect = :val",
            ExpressionAttributeValues={
                ':val': counter_result_sum
            },
            ReturnValues="UPDATED_NEW"
        )
    elif info_request == "GetPreviousTotalCorrect":
        previous_total_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in previous_total_query['Items']:
            previous_total_query = (i['PreviousTotalCorrect'])
        return previous_total_query
    elif info_request == "GetPreviousTotalIncorrect":
        previous_total_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in previous_total_query['Items']:
            previous_total_query = (i['PreviousTotalCorrect'])
        return previous_total_query
    elif info_request == "IncrementCorrect":
        response = user_data_dynamodb.update_item(
            Key={
                'UserID': "Tester",
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
        counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in counter_current_value['Items']:
            counter_result = (i['CounterCorrect'])
        counter_result_sum = sum(counter_result.values())
        return counter_result_sum
    elif info_request == "IncrementIncorrect":
        response = user_data_dynamodb.update_item(
            Key={
                'UserID': "Tester",
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
        counter_current_value = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in counter_current_value['Items']:
            counter_result = (i['CounterIncorrect'])
        counter_result_sum = sum(counter_result.values())
        return counter_result_sum
    elif info_request == "GetLevel":
        current_level_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in current_level_query['Items']:
            current_level = (i['QuestionLevel'])
        return current_level
    elif info_request == "IncrementLevel":
        response = user_data_dynamodb.update_item(
            Key={
                'UserID': "Tester",
            },
            UpdateExpression="set QuestionLevel = QuestionLevel + :val",
            ExpressionAttributeValues={
                ':val': decimal.Decimal(1)
            },
            ReturnValues="UPDATED_NEW"
        )
        current_level_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
        for i in current_level_query['Items']:
            current_level = (i['QuestionLevel'])
        return current_level
    elif info_request == "DecrementLevel":
        response = user_data_dynamodb.update_item(
            Key={
                'UserID': "Tester",
            },
            UpdateExpression="set QuestionLevel = QuestionLevel - :val",
            ExpressionAttributeValues={
                ':val': decimal.Decimal(1)
            },
            ReturnValues="UPDATED_NEW"
        )
        current_level_query = user_data_dynamodb.query(KeyConditionExpression=Key('UserID')\
            .eq("Tester"))
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

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ Standard welcome response to the skill, normally said by Alexa if
    a user invokes the skill without an intent.
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Alexa PLC counter instruction tutor. " \
                    "Please ask me a question by saying something like, " \
                    "quiz me, or give me a question."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please ask me a question by saying something like, " \
                    "quiz me, give me a question, or ask me a question."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    """ Ends the Alexa session when a user requests it. """

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
        return get_welcome_response()
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
    reprompt_text = None
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
    # Check user's status with correct/incorrect questions and update level
    # accordingly before generating a new question.
    current_user_level = update_user_level()

    # Generate either a True/False or Select Value type question and relay it
    # back to the user.
    #question_type_num = random.randint(0, 1)
    question_type_num = 0

    if question_type_num == 0:
        question_full = generate_true_false(current_user_level)

        card_title = "True or False Question"
        speech_output = (
            "<speak>" + '"<prosody rate="slow">"' + "True or False? "
            + question_full[1] + "</prosody>" + "</speak>"
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
        question_full = generate_select_value()

        card_title = "Short Answer Question"
        speech_output = (
            "<speak>" + '"<prosody rate="slow">"' + question_full[0]
            + "</prosody>" + "</speak>"
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

    # If a user's answer matches a slot value, depending on whether
    # the user is responding to a True/False question or a SelectValue
    # question, the user's answer is checked vs. the actual answer to the
    # question and informed whether they are correct or incorrect.
    if 'Answer' in intent['slots']:
        user_answer = intent['slots']['Answer']['value']
        question_details = session.get('attributes', {})
        if question_details["QuestionType"] == "TrueFalse":
            if (question_details["PartialAnswer"] == "true") \
                and (user_answer == "true"):
                speech_output = (
                    "<speak>" + "True is correct. " +
                    question_details["FullAnswer"] + '"<break time="2s"/>"' +
                    "Do you want another question?" + "</speak>"
                )
                update_user_database("IncrementCorrect", question_details["QuestionAttribute"])
            elif (question_details["PartialAnswer"] == "false") \
                and (user_answer == "false"):
                speech_output = (
                    "<speak>" + "False is correct. " +
                    question_details["FullAnswer"] + '"<break time="2s"/>"' +
                    "Do you want another question?" + "</speak>"
                )
                update_user_database("IncrementCorrect", question_details["QuestionAttribute"])
            elif (question_details["PartialAnswer"] == "true") \
                and (user_answer == "false"):
                speech_output = (
                    "<speak>" + "Sorry, the correct answer is True. " +
                    question_details["FullAnswer"] + '"<break time="2s"/>"' +
                    "Do you want another question?" + "</speak>"
                )
                update_user_database("IncrementIncorrect", question_details["QuestionAttribute"])
            elif (question_details["PartialAnswer"] == "false") \
                and (user_answer == "true"):
                speech_output = (
                    "<speak>" + "Sorry, the correct answer is False. " +
                    question_details["FullAnswer"] + '"<break time="2s"/>"' +
                    "Do you want another question?" + "</speak>"
                )
                update_user_database("IncrementIncorrect", question_details["QuestionAttribute"])
        elif question_details["QuestionType"] == "SelectValue":
            if user_answer in question_details["Answer"]:
                speech_output = (
                    "<speak>" + "Your answer is correct. " +
                    user_answer + '"<break time="2s"/>"' +
                    "Do you want another question?" + "</speak>"
                )
            else:
                speech_output = (
                    "<speak>" + "Your answer is incorrect. "
                    + '"<break time="2s"/>"' + "Do you want another question?" + "</speak>"
                )
        reprompt_text = None
        should_end_session = False
    else:
        speech_output = (
            "<speak>" + "I'm not sure what your answer is. Please try again." + "</speak>"
        )
        reprompt_text = "I'm not sure what your answer is. Please try again."
        should_end_session = False

    session_attributes = {
        "CardTitle": card_title,
        "SpeechOutput": speech_output,
        "RepromptText": reprompt_text,
        "CurrentStage": "CheckAnswer",
        "QuestionType": question_details["QuestionType"],
    }

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
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handler
    if intent_name == "QuestionIntent":
        return get_question_from_session(intent, session)
    elif intent_name == "AnswerIntent":
        return check_answer_in_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return handle_help_request(intent, session)
    elif intent_name == "AMAZON.RepeatIntent":
        return handle_repeat_request(intent, session)
    elif intent_name == "AMAZON.StartOverIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.YesIntent":
        if session['attributes']['CurrentStage'] == "CheckAnswer":
            return get_question_from_session(intent, session)
        elif session['attributes']['CurrentStage'] == "HelpRequest":
            return get_question_from_session(intent, session)
    elif intent_name == "AMAZON.NoIntent":
        if session['attributes']['CurrentStage'] == "CheckAnswer":
            return handle_session_end_request()
        if session['attributes']['CurrentStage'] == "HelpRequest":
            return handle_session_end_request()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
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
