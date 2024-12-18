from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from autogen import ConversableAgent, UserProxyAgent, AssistantAgent, runtime_logging, Agent

import os
import re
import queue
import datetime
import time
import asyncio
import threading
from dotenv import load_dotenv

from utils.yaml_util import load_config
from utils.mongodb_utils import get_database, user_insert, conv_insert
from utils.agent_tools import save_user_info, get_ras_tas_questions, update_json_with_dict, calculate_anxiety_scores
from utils.chat_utils import register_nested_chat_with_stai_assistant


# loading configurations
load_dotenv()
config = load_config()
language = config["Language"]

openai_config={"config_list": [
    {
        "model": config["OpenAI_configs"]["model"], 
        "api_key": os.environ.get("OPENAI_API_KEY"), 
        "max_tokens": config["OpenAI_configs"]["max_tokens"], 
        "temperature": config["OpenAI_configs"]["temperature"], 
        "top_p": config["OpenAI_configs"]["top_p"]
     }]}
anthropic_config = {"config_list": [
    {
        "model": config["Anthropic_configs"]["model"],
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "api_type": "anthropic",
        "seed": config["Anthropic_configs"]["seed"],
        "temperature": config["Anthropic_configs"]["temperature"]
    }]}

llm_configs = openai_config if config["LLM"] == "OpenAI" else anthropic_config

# connect to the database
mh_agent_db = get_database()
user_id_collection = mh_agent_db["user"]
conversations_collection = mh_agent_db["conversation"]

app = Flask(__name__)
cors=CORS(app)

chat_status = "ended" 

# Queues for single-user setup
print_queue = queue.Queue()
user_queue = queue.Queue()

# user_id = '1' # input parameter from Ulan

class MyConversableAgent(ConversableAgent):
    async def a_get_human_input(self, prompt: str) -> str:
        input_prompt = "Please input your further direction, or type 'exit' to end the conversation"
        print_queue.put({'user': "System", 'message': input_prompt})

        start_time = time.time()
        global chat_status
        chat_status = "inputting"
        while True:
            if not user_queue.empty():
                input_value = user_queue.get()
                chat_status = "Chat ongoing"
                print("input message: ", input_value)
                return input_value

            if time.time() - start_time > 600:  
                chat_status = "ended"
                return "exit"

            await asyncio.sleep(1) 


async def initiate_chat(agent, recipient, message, summary_method=None):
    result = await agent.a_initiate_chat(recipient, message=message, clear_history=False)

    return result


def prepare_acquaintance_agent():
    """
    Prepares the acquaintance agent and user.
    Parameters:
        user_info (dict): User information.
    Returns:
        tuple: Psychotherapist assistant and user agent.
    """

    acquaintance_agent = AssistantAgent(
        name="acquaintance_agent",
        system_message = config["Prompt_templates"]["acquaintance_system_message"].format(
            user_id=123,
            language=config['Language']
            ),
        llm_config=llm_configs,
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
        description= "Conducts conversations, collects the necessary diagnostic information.",
    )

    user_acquaintance = MyConversableAgent(
        name="user",
        llm_config=False,  
        human_input_mode="TERMINATE",
        is_termination_msg=lambda msg: msg.get("tool_calls") == None,
        code_execution_config=False,
        description= "Real user who interacts with the system.",
        )
    
    acquaintance_agent.register_for_llm(
        name="save_user_info",
        description="Saves user_info to the JSON file."
    )(save_user_info)

    user_acquaintance.register_for_execution(
        name="save_user_info",
    )(save_user_info)
    
    return acquaintance_agent, user_acquaintance


def prepare_psychotherapist_agent(user_name: str, last_user_summary: list, last_conversation_date: datetime = None):
    """
    Prepares the psychotherapist agent and user.
    Parameters:
        user_name (str): User name.
        last_user_summary (list): Summary of the last conversation with user.
    Returns:
        tuple: Psychotherapist assistant and user agent.
    """        
    
    system_message = config["Prompt_templates"]["psychotherapist_system_message"].format(
            user_name = user_name,
            last_user_summary = last_user_summary,
            last_conversation_date = last_conversation_date,
            language=config['Language'],
        )
    
    psychotherapist_agent = AssistantAgent(
        name="psychotherapist_agent",
        system_message = system_message,
        llm_config=llm_configs,
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: "goodbye" in msg["content"].lower(),
        description= "Conducts conversations, collects the necessary diagnostic information and makes summary.",
    )
    
    user = MyConversableAgent(
        name="user",
        llm_config=False,  
        human_input_mode="TERMINATE",
        is_termination_msg=lambda msg: msg.get("tool_calls") == None,
        code_execution_config=False,
        description= "Real user who interacts with the psychotherapist.",
    )

    return psychotherapist_agent, user


def prepare_stai_assistant_and_user(user_name: str, user_id: str):
    """
    Prepares the STAI diagnostics assistant and the user proxy agent.
    Parameters:
        user_name (str): User name,
        user_id (str): User id.
    Returns:
        tuple: STAI diagnostics assistant and user agent.
    """
    
    stai_diagnostics_assistant = AssistantAgent(
        name="STAI assessment diagnostics",
        system_message = config["Prompt_templates"]["stai_diagnostics_assistant_system_message"].format(
            user_name = user_name,
            user_id = user_id,
            language = language,
        ),
        llm_config=llm_configs,
        is_termination_msg=lambda msg: "successfully" in msg["content"].lower(),
        human_input_mode="NEVER",
        description= "Conducts conversations, makes State-Trait Anxiety Inventory (STAI) assessment, calculates anxiety assessment scores, provides anxiety assessment scores.",
    )
    
    user_stai = MyConversableAgent(
        name="user",
        llm_config=False,  
        human_input_mode="TERMINATE",
        is_termination_msg=lambda msg: msg.get("tool_calls") == None or "terminate" in msg["content"].lower(),
        code_execution_config=False,
        description= "Real user who interacts with the system.",
    )

    stai_diagnostics_assistant.register_for_llm(
        name="get_ras_tas_questions",
        description="Checks the JSON file with Reactive (State) and Trait Anxiety scores for all fields and their values."
    )(get_ras_tas_questions)

    user_stai.register_for_execution(
        name="get_ras_tas_questions",
    )(get_ras_tas_questions)

    stai_diagnostics_assistant.register_for_llm(
        name="update_json_with_dict",
        description="Updates a JSON file with Reactive (State) and Trait Anxiety scores using the values ​​from the passed dictionary."
    )(update_json_with_dict)

    user_stai.register_for_execution(
        name="update_json_with_dict",
    )(update_json_with_dict)

    stai_diagnostics_assistant.register_for_llm(
        name="calculate_anxiety_scores",
        description="Calculates Reactive (State) and Trait Anxiety scores based on Spielberger's inventory."
    )(calculate_anxiety_scores)

    user_stai.register_for_execution(
        name="calculate_anxiety_scores",
    )(calculate_anxiety_scores)
    
    return stai_diagnostics_assistant, user_stai


def prepare_summary_agent(user_name:str, last_user_summary: str, current_conversation: list):
    """
    Prepares the conversation summary agent and the user proxy agent.
    Parameters:
        user_name (str): User name.
        last_user_summary (str): Summary of the last conversation with user.
        current_conversation (List): List of current conversation messages.
    Returns:
        tuple: Conversation summary agent and user agent
    """
    
    summary_agent = AssistantAgent(
        name="conversation_summary",
        system_message = config["Prompt_templates"]["conversation_summary_prompt_template"].format(
            user_name=user_name,
            last_user_summary=last_user_summary,
            conversation_history=current_conversation,
            language=language
            ),
        llm_config=llm_configs,
        human_input_mode="NEVER",
        description= "Makes summary.",
    )

    user_proxy = UserProxyAgent(
        name="User_proxy",
        llm_config=False,
        human_input_mode="TERMINATE",
        code_execution_config=False,
        description= "Real user who interacts with the system.",
    )

    return summary_agent, user_proxy


# chat functions
def save_and_print_messages(recipient, messages, sender, config):
    content = messages[-1].get('content')
    timestemp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    current_conversation.append(
        {
            "date":timestemp, 
            "sender": sender.name, 
            "recipient": recipient.name, 
            "message": content
            }
        )
    # # Print the message 
    # print(f"Sender: {sender.name} | Recipient: {recipient.name} | Message: {messages[-1].get('content')}")
    # print("--------------------------------------------------------------------------------")
    
    if all(key in messages[-1] for key in ['name']):
        print_queue.put({'user': messages[-1]['name'], 'message': content})
    elif messages[-1]['role'] == 'user':
        print_queue.put({'user': sender.name, 'message': content})
    else:
        print_queue.put({'user': recipient.name, 'message': content})

    return False, None  # Required to ensure the agent communication flow continues


def run_chat(request_json):
    global chat_status
    global current_conversation
    try:
        # a) Data structure for the request
        user_input = request_json.get('message')
        user_id = request_json.get('user_id')

        
        # b) internal logs and current conversation history
        current_conversation = [] # list of dictionaries with messages created by save_messages()
        
        logging_session_id = runtime_logging.start(config={"dbname": "logs.db"})
        print("Started Logging session ID: " + str(logging_session_id))
        
        
        # c) get user info
        if user_id:
            # user_id - input parametr
            user_info = user_id_collection.find_one({"user_id": user_id})
            user_name = user_info['name']
            print('*'*50)        
            print(f'User successfully found:\nuser_id: {user_id}, name: {user_name}')
            print('*'*50)
            
            user_conversations = list(conversations_collection.find({"user_id": user_id}))
            last_user_conversation = user_conversations[-1]
            
            last_user_summary = last_user_conversation.get('conversation_summary')
            last_user_conversation_history = last_user_conversation.get('convercation_history')
            last_conversation_date = last_user_conversation.get('conv_timestamp').strftime("%Y-%m-%d %H:%M:%S")

        else:
            user_info = None
            user_name = None
            last_user_summary = None
            last_user_conversation_history = None
            last_conversation_date = None
        
        
        # d) prepare agents
        psychotherapist_agent, user = prepare_psychotherapist_agent(
            user_name=user_name, 
            last_user_summary=last_user_summary, 
            last_conversation_date=last_conversation_date
            )
        print('*'*50)
        print("User and psychotherapist agents are ready.")
        
        stai_assistant, user_stai = prepare_stai_assistant_and_user(
            user_name=user_name, 
            user_id=user_id
            )
        print('*'*50)
        print("STAI assistant and user agents are ready.")

        # save_messages - function that saves messages to the current_conversation
        for agent in [psychotherapist_agent, stai_assistant, user, user_stai]:
            agent.register_reply([ConversableAgent, None], reply_func=save_and_print_messages, config=None) 
        
        # register nested chat with STAI assistant
        register_nested_chat_with_stai_assistant(user, stai_assistant, user_stai)
        print('*'*50)
        print("Nested chat with STAI assistant is registered.")
        
        # result = user.initiate_chat(
        #     psychotherapist_agent, 
        #     message=user_input,
        #     summary_method="last_msg",
        # )
        result = asyncio.run(initiate_chat(
            agent=user,
            recipient=psychotherapist_agent,
            message=user_input,
            summary_method="last_msg"
        ))

        summary_agent, user_proxy = prepare_summary_agent(
            user_name=user_name,
            last_user_summary=last_user_summary,
            current_conversation = result.chat_history
            )

        # save_messages - function that saves messages to the current_conversation
        for agent in [summary_agent, user_proxy]:
            agent.register_reply([ConversableAgent, None], reply_func=save_and_print_messages, config=None)
            
        summary_result = user_proxy.initiate_chat(
            summary_agent,
            message="Make summary",
            max_turns=2,
            summary_method="last_msg",    
            )
        
        new_conversation_summary = summary_result.chat_history[-1].get('content')

        # save the conversation to the database
        conv_insert(conversations_collection, 
                    user_id=user_id,
                    conversation_history = current_conversation,
                    conversation_summary = new_conversation_summary
                    )
        
        print('*'*50)
        print('*'*50)
        print(result.chat_history)
        print('*'*50)
        print('*'*50)
        
        chat_status = "ended"
        runtime_logging.stop()
        
               
    except Exception as e:
        chat_status = "error"
        print_queue.put({'user': "System", 'message': f"An error occurred: {str(e)}"})



@app.route('/api/start_chat', methods=['POST', 'OPTIONS']) 
def start_chat():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    elif request.method == 'POST':
        global chat_status
        try:

            if chat_status == 'error':
                chat_status = 'ended' 

            with print_queue.mutex:
                print_queue.queue.clear()
            with user_queue.mutex:
                user_queue.queue.clear()

            chat_status = 'Chat ongoing'

            thread = threading.Thread(
                target=run_chat, 
                args=(request.json,)
            )
            thread.start()
    
            return jsonify({'status': chat_status})
        except Exception as e:
            return jsonify({'status': 'Error occurred', 'error': str(e)})
       
 
@app.route('/api/send_message', methods=['POST'])
def send_message():
    # Add print statements for debugging
    print("Received message request")
    print("Request JSON:", request.json)
    
    user_input = request.json['message']
    print("User input:", user_input)
    
    user_queue.put(user_input)
    return jsonify({'status': 'Message Received'})


@app.route('/api/get_message', methods=['GET'])
def get_messages():
    global chat_status 

    if not print_queue.empty():
        msg = print_queue.get()        
        # print("Message to return:", msg)
        
        text = msg.get('message')
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r"<tone>.*?</tone>", "", text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        msg['message'] = text.strip()
        # print("Message to return after processing:", msg)        
        
        return jsonify({'message': msg, 'chat_status': chat_status}), 200
    else:
        return jsonify({'message': None, 'chat_status': chat_status}), 200


if __name__ == "__main__":
        app.run(host='0.0.0.0', port=5008, debug=True)
