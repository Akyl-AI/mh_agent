from typing import Union

async def check_for_run_stai_assessment(last_msg: Union[dict, None]) -> bool:
    """
    Check if the message contains the trigger phrase for STAI assessment.
    The function handles different message formats that might come from the chat system.
    
    Args:
        msg: Message object or dictionary containing the message content
        
    Returns:
        bool: True if trigger phrase is found, False otherwise
    """

    # print(f"Checking message: {last_msg}")  # Для отладки
    if not last_msg:
        print("No last message found.")
        return False

    if isinstance(last_msg, dict):
        return "run stai assessment" in last_msg.get("content", "").lower()
    print(f"Message does not match expected structure: {last_msg}")
    return False


async def register_nested_chat_with_stai_assistant(user, stai_diagnostics_assistant, user_stai) -> None:
    """
    Register a nested chat between the user and the STAI assistant.
    Args:
        user (UserProxyAgent): User agent.
        stai_diagnostics_assistant (AssistantAgent): STAI assistant agent.
        user_stai (UserProxyAgent): User agent for STAI assistant.
    """
    
    user.register_nested_chats(
    [
        {
            "sender": user_stai,
            "recipient": stai_diagnostics_assistant,
            "message": "run stai assessment",
            "summary_method": "last_msg",
            # "max_turns": 3
         }
    ],
    trigger=lambda msg: check_for_run_stai_assessment(msg.last_message()),
    use_async=True,
    )
    
    return None