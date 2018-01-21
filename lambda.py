import random

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
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
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Functions that control the skill's behavior ------------------

words = {
    "kevin" : "the best",
    "alice" : "the worst",
    "jamie" : "the false queen",
}

def get_welcome_response():
    global words
    
    session_attributes = {
        "questions_asked" : 0,
        "words_used" : [],
        "current_correct_def" : 1,
        "points" : 0,
        "waiting_for_def" : False,
    }
    
    card_title = "Welcome"
    speech_output = "I'll give you three words, and two definitions for each. "\
                    "For each word you must tell me if the first or second definition is the correct one. "\
                    "You need two points to win! "\
                    "Say 'next word' when you're ready for the first word."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Say 'next word'!"
    #session_attributes["words"] = initialize_dictionary("scrabble_words.txt")
    words = initialize_words("balderdash.txt")
    
    should_end_session = False
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def give_move(intent, session):
    global words
    card_title = intent['name']
    should_end_session = False
    session_attributes = session["attributes"]

    if session_attributes['waiting_for_def'] == True:
        speech_output = "Say 'First' or 'Second'! to choose a definition!"
        reprompt_text = "Say 'First' or 'Second'! to choose a definition!"
    else:
        word = random.choice(list(words.keys()))
        while word in session_attributes["words_used"]:
            word = random.choice(words.keys())
        correct_def = words[word]

        session_attributes["words_used"].append(word)
        
        incorrect_word = word
        while incorrect_word in session_attributes["words_used"]:
            incorrect_word = random.choice(list(words.keys()))
        incorrect_def = words[incorrect_word]

        session_attributes["words_used"].append(incorrect_word)

        defs = [correct_def, incorrect_def]
        random.shuffle(defs)

        speech_output = "The word is {}. Does that mean '{}', or does it mean '{}'?".format(word, defs[0],defs[1])
        reprompt_text = "Say 'First' or 'Second'!"

        if defs[0] == correct_def:
            session_attributes["current_correct_def"] = 1
        elif defs[1] == correct_def:
            session_attributes["current_correct_def"] = 2
        else:
            speech_output = "Error!!"
            should_end_session = True

        session_attributes['waiting_for_def'] = True

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def check_answer(intent, session):
    card_title = intent['name']
    should_end_session = False
    session_attributes = session["attributes"]

    if not session_attributes['waiting_for_def']:
        speech_output = "Say 'next word' first!"
        reprompt_text = "Say 'next word' first!"
    elif "Selection" in intent['slots']:
        if intent['slots']['Selection']['value'].lower() in ["first", "1st"]:
            selection = 1
        else:
            selection = 2
            
        session_attributes["questions_asked"] += 1
        
        if selection == session_attributes["current_correct_def"]:
            # Correct decision
            session_attributes["points"] += 1
            speech_output = "Correct! "
            reprompt_text = ""
        else:
            speech_output = "Wrong! "
            reprompt_text = ""

    else:
        speech_output = "I didn't catch that."
        reprompt_text = "I didn't catch that."

    if session_attributes["questions_asked"] == 3:
        # Game over!
        should_end_session = True
        if session_attributes["points"] >= 2:
            speech_output += "You got {} points and won!".format(session_attributes["points"])
        else:
            speech_output += "You got {} point{} and lost! You're not very good at this, are you!?".format(session_attributes["points"], '' if session_attributes["points"] == 1 else 's')
    else:
        if session_attributes['waiting_for_def']:
            speech_output += "Say 'next word' again for the next word."
            reprompt_text = "Say 'next word' again for the next word."
    
    session_attributes['waiting_for_def'] = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# ------ Helpers

def initialize_words(fname="balderdash.txt"):
    words = {}
    
    with open(fname,'r') as f:
        is_word = True
        my_word = ''

        for line in f.readlines():
            if line.strip() == "":
                continue
            if is_word:
                my_word = line.strip().lower()
                is_word = False
            else:
                words[my_word] = line.strip().lower()
                is_word = True
    return words

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

    # Dispatch to your skill's intent handlers
    if intent_name == "ReadyIntent":
        return give_move(intent, session)
    elif intent_name == "DefinitionSelectIntent":
        return check_answer(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
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
