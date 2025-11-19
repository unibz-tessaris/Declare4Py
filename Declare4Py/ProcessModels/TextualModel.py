from abc import ABC
from Declare4Py.ProcessModels import DeclareModel
from Declare4Py.Utils.Declare import DeclarePrompts
from Declare4Py.ProcessModels.AbstractModel import ProcessModel
from typing import List
from groq import Groq, GroqError
import os


class TextualModel(ProcessModel, ABC):
    def __init__(self, textual_description: str):
        super().__init__()
        self.textual_description = textual_description
        
        # Load prompts for the LLM   
        self.prompt_instructions: str = DeclarePrompts.INSTRUCTIONS_AND_TEMPLATES
        self.prompt_instructions = self.prompt_instructions + DeclarePrompts.ADDITIONAL_TEMPLATES
        self.prompt_meta_constraints: str = DeclarePrompts.META_CONSTRAINTS
        self.prompt_formatting_information: str = DeclarePrompts.DESCRIPTION_AND_FORMATTING_INFORMATION
        
        
    def parse_form_file (self, model_path: str, **kwargs):
        # Load the process description from a textual file
        self.textual_description = TextualModel.read_file(model_path)


    def to_decl (self, api_key, interactive : bool = False, llm_model : str = "meta-llama/llama-4-scout-17b-16e-instruct", **kwargs) -> DeclareModel:
        """
        This method handles, with a LLM, the textual description of the process to extract the declarative constraints,
        Then represents it as instance of the object Model and returns
        """
        # if interactive is not a boolean, set it to its default value False
        if not isinstance(interactive, bool):
            interactive = False
        
        # Set up API key and model name
        os.environ["GROQ_API_KEY"] = api_key #set environment variable
        
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
        formatted_prompt_formatting_information = self.prompt_formatting_information.format(textual_description=self.textual_description)
        interaction_statuses = ["Consider this text and extract highly reliable declarative constraints. No interaction with the user will be available, so please be as precise as possible in your response.", "Consider this text and, if you find it necessary, ask me questions to clary whatever may be unclear and the extract highly reliable declarative constraints."]
        if interactive:
            formatted_prompt_formatting_information = formatted_prompt_formatting_information.format(interaction_status=interaction_statuses[1])
        else:
            formatted_prompt_formatting_information = formatted_prompt_formatting_information.format(interaction_status=interaction_statuses[0])

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
            'content': formatted_prompt_formatting_information})
    

        try:
            # Initialize client for Groq API using the API key
            # Note: Ensure you have the Groq library installed and configured correctly
            client = Groq()

            # Since the user is available to interact with the LLM we start a cmd line chat
            if interactive:
                # Introduce chat
                print(f"This is a new chat with Ollama model {llm_model} \n   Once you are satisfied with the results, please type 'exit' to close the chat")

                # While loop to handle interactions user-LLM
                while True:
                    # Retrive LLM's reply
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

            # Without interactions the LLM result should be directly saved into the model 
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

            # Save the last LLM reply
            last_reply = conversation[-1]['content']

            # Parse the LLM result to extract activities and constraints, then format them following syntax rules
            parsed_content = TextualModel.parse_llm_result(last_reply)

            # Generate model from parsed string
            model = DeclareModel.parse_from_string(self, content=parsed_content) 

            return model
        
        except GroqError as e:
            print(f" Invalid API key or connection issue: {e}")

    # Support method to parse results of the LLM
    def parse_llm_result (response: str) -> str:
        # Extract constraints from the LLM response
        constraints = TextualModel.parse_response_constraints(response)

        # From constraints find the activities
        activities = TextualModel.parse_response_activities(constraints)

        # If activities are not found, try to parse them from constraints
        str = "No activities found in the LLM reply."
        if activities == [str]:
            activities = TextualModel.parse_activities(constraints)
        
        # Combine activities and constraints into a parsed string compatible with .decl syntax
        parsed_content = TextualModel.parse_string_to_decl(constraints, activities)
        
        return parsed_content

    # Support method: finds constraints in the LLM response
    def parse_response_constraints (llm_reply: str) -> List[str]:
        import re
        constraints = []
        str = "Final Formal Declarative Constraints"

        # Split the string after the last instace of "Final Formal Declarative Constraints:"
        index = llm_reply.rfind(str)
        if index == -1:
            return ["No constraints found in the AI reply."]
        else:
            # Split the string so that it contains only the constraints
            split_string = llm_reply[index + len(str):].strip()

            # Define all available regex to find constraints
            # Unary constraints
            at_most_regex = re.compile(
                r"at-most\s*\(\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            existence_regex = re.compile(
                r"existence\s*\(\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            init_regex = re.compile(
                r"init\s*\(\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )

            # Binary constraints with exclusions
            response_regex = re.compile(
                r"(?<!not-)(?<!chain-)(?<!alternate-)response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            precedence_regex = re.compile(
                r"(?<!not-)(?<!chain-)(?<!alternate-)precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            succession_regex = re.compile(
                r"(?<!not-)(?<!chain-)(?<!alternate-)succession\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            choice_regex = re.compile(
                r"(?<!exclusive-)choice\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            chain_succession_regex = re.compile(
                r"(?<!not-)chain-succession\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            chain_response_regex = re.compile(
                r"(?<!not-)chain-response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            chain_precedence_regex = re.compile(
                r"(?<!not-)chain-precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            co_existence_regex = re.compile(
                r"(?<!not-)co-existence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            exclusive_choice_regex = re.compile(
                r"(?<!not-)exclusive-choice\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            responded_existence_regex = re.compile(
                r"(?<!not-)responded-existence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )

            # Binary constraints with no exclusions
            alternate_response_regex = re.compile(
                r"alternate-response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            alternate_precedence_regex = re.compile(
                r"alternate-precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            alternate_succession_regex = re.compile(
                r"alternate-succession\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )


            # Negative constraints
            not_response_regex = re.compile(
                r"not-response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_precedence_regex = re.compile(
                r"not-precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_chain_response_regex = re.compile(
                r"not-chain-response\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_chain_precedence_regex = re.compile(
                r"not-chain-precedence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_chain_succession_regex = re.compile(
                r"not-chain-succession\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_co_existence_regex = re.compile(
                r"not-co-existence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_exclusive_choice_regex = re.compile(
                r"not-exclusive-choice\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_responded_existence_regex = re.compile(
                r"not-responded-existence\s*\(\s*([\w\s\-]+?)\s*,\s*([\w\s\-]+?)\s*\)",
                re.IGNORECASE
            )
            not_succession_regex = re.compile(
                r"not-succession\s*\(\s*([A-Za-z_ ]+)\s*,\s*([A-Za-z_ ]+)\s*\)", re.IGNORECASE)


            regexes = [at_most_regex, existence_regex, response_regex, precedence_regex, co_existence_regex, not_co_existence_regex, not_succession_regex, responded_existence_regex, alternate_succession_regex, init_regex, not_responded_existence_regex, not_response_regex, not_precedence_regex, not_chain_response_regex, not_chain_precedence_regex, succession_regex, choice_regex, exclusive_choice_regex, not_exclusive_choice_regex, not_chain_succession_regex, chain_succession_regex, chain_response_regex, chain_precedence_regex, alternate_response_regex, alternate_precedence_regex]
            constraints = ["at-most", "existence", "response", "precedence", "co-existence", "not-co-existence", "not-succession", "responded-existence", "alternate-succession", "Init", "not-responded-existence", "not-response", "not-precedence", "not-chain-response", "not-chain-precedence", "succession", "choice", "exclusive-choice", "not-exclusive-choice", "not-chain-succession", "chain-succession", "chain-response", "chain-precedence", "alternate-response", "alternate-precedence"]

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

    # Support method: parses activities from constraints - used if parse_response_activities is unable to find activities in the LLM response
    def parse_activities (constraints: List[str]) -> List[str]:
        activities = []
        for constraint in constraints:
            # Remove the constraint type and parentheses 
            # Be careful with the order of replacements, not-template should be done before template, symilarly co-template and template
            constraint  = constraint.replace("at-most(", "").replace("Init(", "").replace("not-responded-existence(", "").replace("responded-existence(", "").replace("not-co-existence(", "").replace("co-existence(", "").replace("existence(", "").replace("alternate-response(", "").replace("not-chain-response(", "").replace("chain-response(", "").replace("not-response(", "").replace("response(", "").replace("alternate-precedence(", "").replace("not-chain-precedence(", "").replace("chain-precedence(", "").replace("not-precedence(", "").replace("precedence(", "").replace("alternate-succession(", "").replace("not-chain-succession(", "").replace("chain-succession(", "").replace("not-succession(", "").replace("succession(", "").replace("not-exclusive-choice(", "").replace("exclusive-choice(", "").replace("choice(", "").replace(")", "").replace(" ", "")

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

    # Support method: finds activities in the LLM response
    def parse_response_activities(llm_reply):
        activities = []
        str = "Activities: "

        # Split the string after the last instace of "Final Formal Declarative Constraints:"
        index = llm_reply.rfind(str)
        if index == -1:
            return ["No activities found in the LLM reply."]
        else:
            # Extract the line containing the activities
            lines = llm_reply[index:].split('\n')
            if lines:
                activity_line = lines[0]
                # Remove the "Activities: " part
                activity_line = activity_line.replace(str, "").strip()
                # Split by comma and strip whitespace
                activities = [act.strip() for act in activity_line.split(",") if act.strip()]    
        return activities

    # Support method: converts constraints and activities into a parsed strinc compaible with .decl syntax for model analysis
    def parse_string_to_decl(constrains: List[str], activities: List[str]) -> str:
        parsed_content = ""

        for activity in activities:
            parsed_content += f"activity {activity}\n"

        for constraint in constrains:
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
        
    # Support method: reads a file and return its content
    def read_file(filename):
        with open(filename, "r", encoding="utf8", errors='ignore') as file:
            content = file.read()
        return content