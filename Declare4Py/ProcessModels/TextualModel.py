# Implementation of AI extraction process
from abc import ABC

from Declare4Py.ProcessModels import DeclareModel
from Declare4Py.Utils.Declare import DeclarePrompts
from logaut import ltl2dfa

from Declare4Py.ProcessModels.AbstractModel import ProcessModel
from pylogics.parsers import parse_ltl
from Declare4Py.Utils.utils import Utils
from typing import List

# My imports
from groq import Groq



# Support method to parse results from AI
def parse_ai_result (response: str) -> str:
    # Extract constraints from the AI response
    constraints = parse_response_constraints(response)

    # From constraints find the activities
    activities = parse_response_activities(constraints)

    # If activities are not found, try to parse them from constraints
    str = "No activities found in the AI reply."
    if activities == [str]:
        activities = parse_activities(constraints)
    
    # Combine activities and constraints into a parsed string compatible with .decl syntax
    parsed_content = parse_string_to_decl(constraints, activities)
    
    return parsed_content

# Support method to find constraints in the AI response
def parse_response_constraints (ai_reply: str) -> List[str]:
    import re
    constraints = []
    str = "Final Formal Declarative Constraints"

    # Split the string after the last instace of "Final Formal Declarative Constraints:"
    index = ai_reply.rfind(str)
    if index == -1:
        return ["No constraints found in the AI reply."]
    else:
        # Split the string so that it contains only the constraints
        split_string = ai_reply[index + len(str):].strip()

        # Define all available regex to find constraints
        at_most_regex = re.compile(r"at-most\s*\(\s*([A-Za-z_ ]+)\s*\)")
        existence_regex = re.compile(r"existence\s*\(\s*([A-Za-z_ ]+)\s*\)")
        response_regex = re.compile(r"response\s*\(\s*([A-Za-z_ ]+)\s*,\s*([A-Za-z_ ]+)\s*\)")
        precedence_regex = re.compile(r"precedence\s*\(\s*([A-Za-z_ ]+)\s*,\s*([A-Za-z_ ]+)\s*\)")
        co_existence_regex = re.compile(r"(?<!not-)co-existence\s*\(\s*([A-Za-z_ ]+)\s*,\s*([A-Za-z_ ]+)\s*\)")
        not_co_existence_regex = re.compile(r"not-co-existence\s*\(\s*([A-Za-z_ ]+)\s*,\s*([A-Za-z_ ]+)\s*\)")
        not_succession_regex = re.compile(r"not-succession\s*\(\s*([A-Za-z_ ]+)\s*,\s*([A-Za-z_ ]+)\s*\)")
        responded_existence_regex = re.compile(r"responded-existence\s*\(\s*([A-Za-z_ ]+)\s*,\s*([A-Za-z_ ]+)\s*\)")


        #(?<!not-)(?<!co-)

        regexes = [at_most_regex, existence_regex, response_regex, precedence_regex, co_existence_regex, not_co_existence_regex, not_succession_regex, responded_existence_regex]
        # constraints = ["at-most", "existence", "response", "precedence", "co-existence", "not-co-existence", "not-succession", "responded-existence"]
        constraints = ["At Most", "Existence", "Response", "Precedence", "Co Existence", "Not Co Existence", "Not Succession", "Responded Existence"]

        found_constraints = []
        for i in range(len(regexes)):
            regex = regexes[i]
            matches = re.findall(regex, split_string)
            # if there are no matches for this regex, continue to the next one
            if not matches:
                continue
            for match in matches:
                # If the match is a tuple (for existence_pair), format it accordingly
                if isinstance(match, tuple):
                    formatted_match = constraints[i] + "(" + ", ".join(match) + ")"
                else:
                    formatted_match = constraints[i] + "(" + match + ")"
                
                found_constraints.append(formatted_match)
                formatted_match=""

        return found_constraints

# Support method to parse activities from constraints - used if parse_response_activities is unable to find activities in the AI response
def parse_activities (constraints: List[str]) -> List[str]:
    activities = []
    for constraint in constraints:
        # Remove the constraint type and parentheses 
        # Be careful with the order of replacements, not-template should be done before template, symilarly co-template and template
        constraint  = constraint.replace("At Most(", "").replace("Response(", "").replace("Precedence(", "").replace("Not Co Existence(", "").replace("Co Existence(", "").replace("Responded Existence(", "").replace("Existence(", "").replace("Not Succession(", "").replace(")", "").replace(" ", "")

        # Split process based on whether the constraint is unary or binary
        if "," in constraint:
            # Binary constraint
            parts = constraint.split(",")
            activities.append(parts[0])
            activities.append(parts[1])
        else:
            # Unary constraint
            activities.append(constraint)
    
    return list(set(activities))

# Support method to find activities in the AI response
def parse_response_activities (ai_reply):
    activities = []
    str = "Activities: "

    # Split the string after the last instace of "Final Formal Declarative Constraints:"
    index = ai_reply.rfind(str)
    if index == -1:
        return ["No activities found in the AI reply."]
    else:
        # Extract the line containing the activities
        lines = ai_reply[index:].split('\n')
        if lines:
            activity_line = lines[0]
            # Remove the "Activities: " part
            activity_line = activity_line.replace(str, "").strip()
            # Split by comma and strip whitespace
            activities = [act.strip() for act in activity_line.split(",") if act.strip()]    
    return activities

# Support method that converts constraints and activities into a parsed strinc compaible with .decl syntax for model analysis
def parse_string_to_decl(constrains: List[str], activities: List[str]) -> str:
    parsed_content = ""

    for activity in activities:
        parsed_content += f"activity {activity}\n"

    for constraint in constrains:
        # Q3: need to replace constraint names?

        # Replace () with [] to follow .decl syntax
        constraint = constraint.replace("(", "[").replace(")", "]")
        # Split process based on whether the constraint is unary or binary
        if "," in constraint:
            # Binary constraint
            parsed_content += f"{constraint} | | |\n"
            
        else:
            # Unary constraint
            parsed_content += f"{constraint} | |\n"
            
    return parsed_content

# Support method to save results into a .decl file
def save_result (file_path: str, content: str):
    with open(file_path, 'w') as file:
        file.write(content)

# Support method reads content from a file
def read_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()

class TextualModel(ProcessModel, ABC):
    def __init__(self, textual_description: str):
        super().__init__()
        self.textual_description = textual_description
        
        # Load p0rompts for the LLM   
        self.prompt_instructions: str = DeclarePrompts.INSTRUCTIONS_AND_TEMPLATES
        #self.prompt_instructions = self.prompt_instructions + DeclarePrompts.ADDITIONAL_TEMPLATES
        #self.prompt_meta_constraints: str = DeclarePrompts.META_CONSTRAINTS
        self.prompt_formatting_information: str = DeclarePrompts.DESCRIPTION_AND_FORMATTING_INFORMATION
        
        
    def parse_form_file (self, model_path: str, **kwargs):
        # Load the process description from a textual file
        self.textual_description = read_file(model_path)


    def to_dec (self, interactive : bool = False, llm_model : str = "meta-llama/llama-4-maverick-17b-128e-instruct"):
        """
        This method handles, with a LLM, the textual description of the process to extract the declarative constraints,
        Then represents it as instance of the object Model and returns
        
        """
        
        # Define API key and model name
        API_KEY = "your_api_key_here"  # Replace with your actual API key 
        
        # Check if the provided model is available
        # Note: The list of available models should be updated based on the actual models available on Groq
        available_models = ["qwen-qwq-32b",
            "deepseek-r1-distill-llama-70b",
            "gemma2-9b-it",
            "compound-beta",
            "compound-beta-mini",
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "llama-guard-3-8b",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-guard-4-12b",
            "meta-llama/llama-prompt-guard-2-22m",
            "meta-llama/llama-prompt-guard-2-86m",
            "mistral-saba-24b"]
        if llm_model not in available_models:
            raise ValueError(f"The model {llm_model} is not available. Please choose from the available ones and try again.\n Available models: {available_models}.")

        # Format the prompt with the textual description and interaction status
        formatted_prompt = self.prompt_formatting_information.format(textual_description=self.textual_description)
        interaction_statuses = ["Consider this text and extract highly reliable declarative constraints. No interaction with the user will be available, so please be as precise as possible in your response.", "Consider this text and, if you find it necessary, ask me questions to clary whatever may be unclear and the extract highly reliable declarative constraints."]
        if interactive:
            formatted_prompt = formatted_prompt.format(interaction_status=interaction_statuses[1])
        else:
            formatted_prompt = formatted_prompt.format(interaction_status=interaction_statuses[0])

        # Load pre-set promt into the conversation
        conversation = []
        conversation.append(
            {'role': 'system',
            'content': self.prompt_instructions})
        conversation.append(
            {'role': 'system',
            'content': self.prompt_meta_constraints})
        conversation.append(
            {'role': 'system',
            'content': formatted_prompt})

        # Initialize client for Groq API using the API key
        # Note: Ensure you have the Groq library installed and configured correctly
        client = Groq(api_key=API_KEY)

        # Since the user is available to interact with the LLM we start a cmd line chat
        if interactive:
            # Introduce chat
            print(f"This is a new chat with Ollama model {llm_model} \n   Once you are satisfied with the results, please type 'exit' to close the chat")

            # While loop to handle interactions user-LLM
            while True:
                # Retrive AI's reply
                response = client.chat.completions.create(
                    model=llm_model,
                    messages=conversation
                )

                # Extract and display model's reply
                response_dict = dict(response)
                choices = response_dict.get("choices", [])

                reply = "The model did not return a valid response."
                if choices:
                    reply = choices[0].message.content
                
                # print result
                print(f"\n\n   AI: {reply}")

                # Add model's response to the conversation
                conversation.append({'role': 'assistant', 'content': reply})

                user_input = input("\n\n   You: ")
                interaction_counter = interaction_counter + 1

                if user_input.lower() in ['exit',]:
                    last_reply = reply
                    break

        # Without interactions the AI result should be directly saved into the model 
        else: 
            # Retrive AI's reply
            response = client.chat.completions.create(
                model=llm_model,
                messages=conversation
            )

            # Extract and display model's reply
            response_dict = dict(response)
            choices = response_dict.get("choices", [])

            reply = "The model did not return a valid response."
            if choices:
                reply = choices[0].message.content

            # Add model's response to the conversation
            conversation.append({'role': 'assistant', 'content': reply})

        # Save the last AI reply
        last_reply = conversation[-1]['content']

        # Parse the AI result to extract activities and constraints, then format them following syntax rules
        parsed_content = parse_ai_result(last_reply)

        # Generate model from parsed string
        model = DeclareModel.parse_from_string(self, content=parsed_content) 

        return model
        