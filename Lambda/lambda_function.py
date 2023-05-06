# Required Libraries
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetches all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


### Validation rules ###
def data_validation(intent_request, age, investment_amount):
    """
    Validate the user input
    """
    # Validate the age input. It should be over 0 and under 65
    if age is not None:
        age = parse_int(age)
        if age not in range(0, 65):
            return build_validation_result(
                False,
                "age",
                "Required age must be larger than 0 and under 65 years.",
            )

    # Validate the amount of investment entered. Should be less than 5000
    if investment_amount is not None:
        investment_amount = parse_int(investment_amount)
        if investment_amount < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "The amount of investment must be greater than $5000",
            )
    # Return True result if inputs are valid
    return build_validation_result(True, None, None)


def select_risk_level(risk_level):
    """
    Takes a risk_level as input and returns a portfolio recommendation
    based on the risk tolerance. Make the risk_level input is case-insensitive.
    """
    # Convert risk_level input to lowercase
    risk_level = risk_level.lower()

    if risk_level == "none":
        portfolio = "100% bonds (AGG), 0% equities (SPY)"
    elif risk_level == "low":
        portfolio = "60% bonds (AGG), 40% equities (SPY)"
    elif risk_level == "medium":
        portfolio = "40% bonds (AGG), 60% equities (SPY)"
    elif risk_level == "high":
        portfolio = "20% bonds (AGG), 80% equities (SPY)"
    else:
        portfolio = "Invalid risk level. Please enter 'none', 'low', 'medium', or 'high'."

    return portfolio


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio based on the user's risk level.
    Validating user input, and returns the recommended portfolio allocation.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        slots = get_slots(intent_request)
        validation_result = data_validation(intent_request, age, investment_amount)

        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        output_session_attributes = intent_request["sessionAttributes"]
        return delegate(output_session_attributes, get_slots(intent_request))

    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Thank you for your information;
            your recommended portfolio is {}.
            """.format(
                select_risk_level(risk_level)
            ),
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)

