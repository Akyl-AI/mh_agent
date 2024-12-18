# LLM Agents Mental Health Support Application

## 1. Problem Description

Mental health is a critical aspect of overall well-being, yet many individuals face barriers when seeking professional help. These barriers include stigma, financial constraints, and a lack of awareness or access to resources. As a result, many people struggle in silence, unable to find the support they need.

## 2. Project Description

The motivation behind creating this application comes from understanding the importance of mental health and addressing the barriers to professional help. Our application leverages Large Language Model (LLM) agents to provide initial mental health support. It is designed to:

- Offer guidance and emotional assistance.
- Serve as a helpful first step for individuals in need.

### Key Features

- **Conversational Support**: Users can interact with the application to express their thoughts and feelings.
- **Guidance and Resources**: Provides helpful information and resources for managing mental health challenges.
- **Privacy Focused**: Ensures user data is handled securely and respectfully.

**While the application is designed to provide initial support, we strongly advocate consulting a professional for long-term or serious mental health issues.**

## 3. Technologies

The project is built using the following technologies:

- **Programming Languages**: Python
- **Frameworks**: Autogen, Flask
- **LLM Integration**: OpenAI and Anthropic models
- **Database**: MongoDB
- **Environment Management**: Pipenv

## 4. Instructions to Run and Use the Application

### 4.1. Environment Preparation and Configurations

1. Create a folder and clone the GitHub repository.
   ```bash
   git clone git@github.com:Akyl-AI/mh_agent.git
   cd mh_agent
   ```

2. Set up API keys for LLM integration:

    2.1. You can use OpenAI or Anthropic. 
    
    You can choose LLM that will be used and configure other settings in `.\app_scripts\utils\config.yaml`
    
    2.2. Rename the `.env_template` file to `.env`.
    
    2.3. Add necessary keys to a `.env` file in the project directory:
     ```env
     OPENAI_API_KEY=your_openai_api_key
     ANTHROPIC_API_KEY=your_anthropic_api_key
     ```


3. Create an environment:
   
    3.1. Make sure you have pipenv installed:

    ```bash
    pip install pipenv
    ```

    3.2. Install the app dependencies:

    ```bash
    pipenv install --dev
    ```

    3.3. Activate the virtual environment:
    ```bash
    pipenv shell
    ```

### 4.2. Running the Application

1.  Start the Flask server:
    ```bash
    python app.py
    ```

2. Start the Agents server:
    ```bash
    python app_scripts\mh_assessment.py
    ```

3. Access the application in your web browser at `http://127.0.0.1:5000`.

### 4.3. Using the Application

1. Open the application in your browser `http://127.0.0.1:5000`.
2. Start a conversation by typing your thoughts or questions.
3. Receive guidance, resources, and emotional support.
4. To finish conversation type `exit`.

Here is a demonstration video of the application in use:  
[Watch on YouTube](https://youtu.be/ir7LuSGNzFs)


## 5. Contributors

- Timur Turatali ([GitHub](https://github.com/golden-ratio))
- Rustem Izmailov ([GitHub](https://github.com/RKIzmailov))
- Den Pavlof ([GitHub](https://github.com/simonlobgromov))

## 6. Next Steps

1. **Enhancements**:
   - Implement advanced privacy and encryption measures.
   - Add more tools.

2. **Integration**:
   - Collaborate with mental health professionals to refine the application.

3. **Deployment**:
   - Host the application on a cloud platform for wider accessibility.