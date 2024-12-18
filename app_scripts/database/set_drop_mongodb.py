from utils.mongodb_utils import get_database

if __name__ == "__main__":
    # Set MongoDB
    mh_agent_db = get_database()
    
    # This creates a collection named user in the mh_db database.
    user_collection = mh_agent_db["user"]

    # This creates a collection named conv in the mh_db database.
    conv_collection = mh_agent_db["conv"]
    
    # # droping collection by name
    # user_collection.drop()
    # conv_collection.drop()   