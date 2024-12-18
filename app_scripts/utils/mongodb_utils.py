from pymongo import MongoClient
import datetime

def get_database():

    user='timur'
    password='NQx59uIMjA21FKsC'

    CONNECTION_STRING = f"mongodb+srv://{user}:{password}@clustertimur.jy7mc.mongodb.net/?retryWrites=true&w=majority&appName=ClusterTimur"

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    # print("all dbs: ", client.list_database_names())

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['mh_db']


# inserting user info
def user_insert(collection_name, user_info: dict) -> str:

    """
    user db has following columns:
    - user_id
    - name
    - regist_timestamp
    """

    regist_timestamp = datetime.datetime.now() #server time
    
    user_info["regist_timestamp"] = regist_timestamp

    collection_name.insert_one(user_info)
    
    return print("User info inserted successfully")
  
  
# inserting conversation history
def conv_insert(collection_name, user_id: str, conversation_history: list, conversation_summary: str) -> str:

    """
    user db has following columns:
    user_id
    convercation_history
    conversation_summary
    conv_timestamp

    """

    conv_timestamp = datetime.datetime.now() #server time

    item = {
        "user_id" : user_id,
        "convercation_history" : conversation_history,
        "conversation_summary": conversation_summary,
        "conv_timestamp" : conv_timestamp
    }

    collection_name.insert_one(item) #or collection.insert_many([item_1,item_2])
    
    return print("Conversation history inserted successfully")