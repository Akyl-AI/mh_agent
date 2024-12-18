import json
import os
from typing import Union, List

from utils.mongodb_utils import get_database, user_insert, conv_insert

# connect to the database (save_user_info)
mh_agent_db = get_database()
user_id_collection = mh_agent_db["user"]
conversations_collection = mh_agent_db["conversation"]

# Path to the JSON file with the template for STAI scales (stai_assistant info)
stai_scales_template_path = "./app/templates/stai-template.json"
work_stai_scales_path = "./app/database/work_stai_scales.json"

# acquaintance_agent functions
def save_user_info(input_dict:dict) -> str:
    """
    Saves user information to a JSON file. JSON file shou,d be replaced with database.
    Args:
        - input_dict: Dictionary with user information, extracted by the acquaintance_agent. Format:{'user_id': user_id, 'name': 'patient's name', 'summary': 'patient's primary anxiety concern'}
        - user_id: to insert data to database.
    Returns: 
        - report and "TERMINATE". "TERMINATE" is a kye for chat termination.
    """
    user_id = input_dict.get("user_id")
    
    user_info = {
        "user_id": user_id,
        "name": input_dict['name'],
    }
    
    conversation_history = {
        "user_id": user_id,
        "summary": input_dict['summary'],
        "conversation": "No conversation yet."
        }
    
    user_insert(user_id_collection, user_info)
    conv_insert(conversations_collection, conversation_history)
    
    return "User info saved successfully. TERMINATE"
    
    
# stai_assistant functions
def get_ras_tas_questions(user_id: int = 123) -> Union[str, List[str]]:
    """
    Checks the JSON file for all fields and their values.
    Args:
        - user_id: Not used. Should be implemented in the future if stai scales are saved in the database.
    Returns: 
        - Message about the check results or the first empty field.
    """
    
    user_id = user_id
    
    # Checking work_stai_scales_path
    if not os.path.exists(work_stai_scales_path):
        print(f"{work_stai_scales_path} not found. Creating from template...")
        try:
            with open(stai_scales_template_path, 'r', encoding='utf-8') as template_file:
                template_data = json.load(template_file)
            
            with open(work_stai_scales_path, 'w', encoding='utf-8') as work_file:
                json.dump(template_data, work_file, ensure_ascii=False, indent=4)

        except FileNotFoundError:
            return f"Template file {stai_scales_template_path} not found."
        except json.JSONDecodeError:
            return f"Error decoding JSON from {stai_scales_template_path}."

    # Gettting questions
    try:
        with open(work_stai_scales_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        empty_values = []
        for items in data.values():
            for question, value in items.items():
                if value is None or value == "" or (not (value.isdigit() and int(value) in {1, 2, 3, 4})):
                    empty_values.append(question)

        if empty_values:
            return empty_values[:1]

        return "All fields are filled in correctly."
    except FileNotFoundError:
        return f"File {work_stai_scales_path} not found."
    except json.JSONDecodeError:
        return f"Error decoding JSON from {work_stai_scales_path}."

def update_json_with_dict(input_dict:dict, user_id:int = 123) -> str:
    """
    Updates a JSON file using the values ​​from the passed dictionary.

    Args:
        - input_dict: Dictionary with keys (questions) and values ​​(1, 2, 3 or 4).
        - user_id: Not used. Should be implemented in the future if stai scales are saved in the database.
    Returns:
        - Message about the operation status.
    """
    for key, value in input_dict.items():
        if not isinstance(value, int) or value not in {1, 2, 3, 4}:
            return f"Invalid value for key '{key}': {value}. The numbers expected were 1, 2, 3 or 4."

    try:
        with open(work_stai_scales_path, 'r', encoding='utf-8') as f:
            data = json.load(f)


        for key, value in input_dict.items():
            updated = False
            for section, questions in data.items():
                if key in questions:
                    questions[key] = str(value)  # Преобразуем значение в строку
                    updated = True
                    break
            if not updated:
                return f"'{key}' doesn't exists in JSON."

        # Сохранение обновленного JSON файла
        with open(work_stai_scales_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return "JSON file updated."

    except FileNotFoundError:
        return "File not found. Make sure the path is correct."
    except json.JSONDecodeError:
        return "Error reading JSON file. Check format."

def calculate_anxiety_scores(user_id: int = 123) -> dict:
    """
    Calculate Reactive (State) and Trait Anxiety scores based on Spielberger's inventory.
    
    Args:
        - user_id: Not used. Should be implemented in the future if stai scales are saved in the database.
        
    Returns:
        dict: Dictionary containing scores and interpretations for both scales.
    """
    
    user_id = user_id
    
    try:
        with open(work_stai_scales_path, 'r', encoding='utf-8') as f:
            responses = json.load(f)
    except FileNotFoundError:
        return "File not found. Make sure the path is correct."
    except json.JSONDecodeError:
        return "Error reading JSON file. Check format."

    def interpret_score(score):
        if score <= 30:
            return {
                "level": "Low",
                "interpretation": "Indicates a need to increase sense of responsibility and attention to motives of activity. In some cases, very low anxiety might indicate active suppression of high anxiety in an attempt to appear in a 'better light'."
            }
        elif score <= 45:
            return {
                "level": "Moderate",
                "interpretation": "Normal anxiety level."
            }
        else:
            return {
                "level": "High",
                "interpretation": "Indicates a tendency to perceive many situations as threatening. Recommendation: Reduce the subjective significance of situations and shift focus to activity analysis and building confidence in success."
            }

    def safe_sum(responses, questions):
        """Safely calculate the sum of responses for given questions."""
        total = 0
        for q in questions:
            value = responses.get(q, "").strip()
            if value.isdigit():
                total += int(value)
            elif value == "":
                total += 0  # Treat empty responses as 0
            else:
                raise ValueError(f"Invalid response for question '{q}': '{value}'")
        return total

    ras_sum1_questions = [
        "I'm under stress", "I feel regret", "I am upset",
        "I am worried about possible failures", "I am dissatisfied with myself",
        "I am nervous", "I am restless", "I am wound up",
        "I am worried", "I am too excited and feel uncomfortable"
    ]

    tas_sum1_questions = [
        "I get tired very quickly", "I can cry easily", "I wish I could be as happy as others",
        "I often lose because I don't make decisions quickly enough",
        "Expected difficulties usually worry me very much",
        "I worry too much over something that doesn't really matter",
        "I take everything too close to heart", "I lack self-confidence",
        "I try to avoid critical situations", "I feel blue",
        "Some unimportant thought runs through my mind and bothers me",
        "I take disappointments so keenly that I can't put them out of my mind",
        "I get in a state of tension or turmoil as I think over my recent concerns and interests"
    ]

    try:
        # Calculate Reactive Anxiety
        ras_responses = responses["Reactive Anxiety Scale (RAS)"]
        ras_sum1 = safe_sum(ras_responses, ras_sum1_questions)
        ras_sum2 = safe_sum(ras_responses, [q for q in ras_responses.keys() if q not in ras_sum1_questions])
        ras_score = ras_sum1 - ras_sum2 + 35

        # Calculate Trait Anxiety
        tas_responses = responses["Trait Anxiety Scale (TAS)"]
        tas_sum1 = safe_sum(tas_responses, tas_sum1_questions)
        tas_sum2 = safe_sum(tas_responses, [q for q in tas_responses.keys() if q not in tas_sum1_questions])
        tas_score = tas_sum1 - tas_sum2 + 35

        evaluate_summary = {
            "reactive_anxiety": {
                "score": ras_score,
                **interpret_score(ras_score)
            },
            "trait_anxiety": {
                "score": tas_score,
                **interpret_score(tas_score)
            }
        }

        return (evaluate_summary, "\nRAS and TAS scores calculated successfully and saved to 'evaluate_summary.json'.")
    
    except ValueError as ve:
        return {"error": str(ve)}
    except Exception as e:
        return {"error": str(e)}
