"""
Purpose:
    Interact with the UPDATED OpenAI API Supports 1.2.3+
    Provide supporting prompt engineering functions.
"""

from dataclasses import dataclass
import json
import sys
from dotenv import load_dotenv
import os
from typing import Any, Dict, List, Callable
import openai
import tiktoken

# load .env file
load_dotenv()

assert os.environ.get("OPENAI_API_KEY")

# get openai api key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# ------------------ helpers ------------------

@dataclass
class TurboTool:
    name: str # function name
    config: dict # open ai config
    function: Callable # function



def safe_get(data, dot_chained_keys):
    """
    {'a': {'b': [{'c': 1}]}}
    safe_get(data, 'a.b.0.c') -> 1
    """
    keys = dot_chained_keys.split(".")
    for key in keys:
        try:
            if isinstance(data, list):
                data = data[int(key)]
            else:
                data = data[key]
        except (KeyError, TypeError, IndexError):
            return None
    return data


def response_parser(response: Dict[str, Any]):
    return safe_get(response, "choices.0.message.content")


# ------------------ content generators ------------------


def prompt(
    prompt: str,
    model: str = "gpt-3.5-turbo-0125",
    instructions: str = "You are a helpful assistant.",
) -> str:
    """
    Generate a response from a prompt using the OpenAI API.
    """

    if not openai.api_key:
        sys.exit(
            """
ERORR: OpenAI API key not found. Please export your key to OPENAI_API_KEY
Example bash command:
    export OPENAI_API_KEY=<your openai apikey>
            """
        )

    response = openai.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": instructions,  # Added instructions as a system message
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response_parser(response.model_dump())


def prompt_func(
    prompt: str,
    turbo_tools: List[TurboTool],
    model: str = "gpt-4-1106-preview",
    instructions: str = "You are a helpful assistant.",
) -> str:
    """
    Generate a response from a prompt using the OpenAI API.
    Force function calls to the provided turbo tools.
    :param prompt: The prompt to send to the model.
    :param turbo_tools: List of TurboTool objects each containing the tool's name, configuration, and function.
    :param model: The model version to use, default is 'gpt-4-1106-preview'.
    :return: The response generated by the model.
    """

    messages = [{"role": "user", "content": prompt}]
    tools = [turbo_tool.config for turbo_tool in turbo_tools]

    tool_choice = (
        "auto"
        if len(turbo_tools) > 1
        else {"type": "function", "function": {"name": turbo_tools[0].name}}
    )

    messages.insert(
        0, {"role": "system", "content": instructions}
    )  # Insert instructions as the first system message
    response = openai.chat.completions.create(
        model=model, messages=messages, tools=tools, tool_choice=tool_choice
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    func_responses = []

    if tool_calls:
        messages.append(response_message)

        for tool_call in tool_calls:
            for turbo_tool in turbo_tools:
                if tool_call.function.name == turbo_tool.name:
                    function_response = turbo_tool.function(
                        **json.loads(tool_call.function.arguments)
                    )

                    func_responses.append(function_response)

                    message_to_append = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": turbo_tool.name,
                        "content": function_response,
                    }
                    messages.append(message_to_append)
                    break

    return func_responses


def prompt_json_response(
    prompt: str,
    model: str = "gpt-4-1106-preview",
    instructions: str = "You are a helpful assistant.",
) -> str:
    """
    Generate a response from a prompt using the OpenAI API.
    Example:
        res = llm.prompt_json_response(
            f"You're a data innovator. You analyze SQL databases table structure and generate 3 novel insights for your team to reflect on and query.
            Generate insights for this this prompt: {prompt}.
            Format your insights in JSON format. Respond in this json format [{{insight, sql, actionable_business_value}}, ...]",
        )
    """

    if not openai.api_key:
        sys.exit(
            """
ERORR: OpenAI API key not found. Please export your key to OPENAI_API_KEY
Example bash command:
    export OPENAI_API_KEY=<your openai apikey>
            """
        )

    response = openai.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": instructions,  # Added instructions as a system message
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
    )

    return response_parser(response.model_dump())


def add_cap_ref(
    prompt: str, prompt_suffix: str, cap_ref: str, cap_ref_content: str
) -> str:
    """
    Attaches a capitalized reference to the prompt.
    Example
        prompt = 'Refactor this code.'
        prompt_suffix = 'Make it more readable using this EXAMPLE.'
        cap_ref = 'EXAMPLE'
        cap_ref_content = 'def foo():\n    return True'
        returns 'Refactor this code. Make it more readable using this EXAMPLE.\n\nEXAMPLE\n\ndef foo():\n    return True'
    """

    new_prompt = f"""{prompt} {prompt_suffix}\n\n{cap_ref}\n\n{cap_ref_content}"""

    return new_prompt


def count_tokens(text: str):
    """
    Count the number of tokens in a string.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


map_model_to_cost_per_1k_tokens = {
    "gpt-4": 0.075,  # ($0.03 Input Tokens + $0.06 Output Tokens) / 2
    "gpt-4-1106-preview": 0.02,  # ($0.01 Input Tokens + $0.03 Output Tokens) / 2
    "gpt-4-1106-vision-preview": 0.02,  # ($0.01 Input Tokens + $0.03 Output Tokens) / 2
    "gpt-3.5-turbo-1106": 0.0015,  # ($0.001 Input Tokens + $0.002 Output Tokens) / 2
}


def estimate_price_and_tokens(text, model="gpt-4"):
    """
    Conservative estimate the price and tokens for a given text.
    """
    # round up to the output tokens
    COST_PER_1k_TOKENS = map_model_to_cost_per_1k_tokens[model]

    tokens = count_tokens(text)

    estimated_cost = (tokens / 1000) * COST_PER_1k_TOKENS

    # round
    estimated_cost = round(estimated_cost, 2)

    return estimated_cost, tokens