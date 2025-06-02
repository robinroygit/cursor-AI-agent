from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import json
import requests
import os


load_dotenv()

client = OpenAI()

print(os)

def run_command(cmd: str):
    result = os.system(cmd)
    return result

run_command("touch test.txt")

def get_weather(city:str):
    # api call 
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The Weather in {city} is {response.text}"

    return "something went wrong"

available_tools = {
    "get_weather":get_weather,
    "run_command":run_command
}

SYSTEM_PROMPT = f"""
        You are a helpfull Ai Assistant Who is specialized in resolving users query.
        You work on start, plan, action, observe mod.

        For the given user query and available tools, plan the step by step execution, based on the planning, 
        select the relevant tool from the available tools and based on the tool selection you perform an action to call the tool.

        wait for the observation and based on the observation from the tool call resolve the user query.

        Rules:
        - Follow the Output JSON Format.
        - Always perform one step at a time and wait for the next input.
        - Carefully analyse the user query.

        Output JSON Format:
        {{
            "step":"string"
            "content":"string"
            "funtion":"The name of the function if the step is action"
            "input":"The input parameter for the function"
        }}

        Available Tools:
        - "get_weather": Takes a city name as an input and returns the current weather of the city.
        - "run_command": Takes linux command as a string and executes the command and returns the output after executing it.

        Example:
        User Query: What is the weather of new york?
        Output:{{"step":"plan", "content": "The User is interested in weather data of new york"}}
        Output:{{"step":"plan", "content": "From the available tools I should call get_weather"}}
        Output:{{"step":"action", "function": "get_weather", "input": "new york"}}
        Output:{{"step":"observe", "output": "12 degree c"}}
        Output:{{"step":"output", "content": "The Weather of New York seems to be 12 degrees."}}

        Example:
        User Query: create a file with name weather.txt
        Output:{{"step":"plan", "content": "The User is interested to create a file"}}
        Output:{{"step":"plan", "content": "From the available tools I should call run_command"}}
        Output:{{"step":"action", "function": "run_command", "input": "touch weather.txt"}}
        Output:{{"step":"observe", "output": "weather.txt"}}
        Output:{{"step":"output", "content": "weather.txt file has been created"}}



        Today Date is {datetime.now()}
"""



messages = [
        {"role": "system", "content": SYSTEM_PROMPT }
]


while True:
    query = input(">")
    messages.append({"role":"user","content":query})


    while True:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type":"json_object"},
            messages=messages
        )

        messages.append({"role":"assistant", "content": response.choices[0].message.content})
        parsed_response = json.loads(response.choices[0].message.content)

        if parsed_response.get("step") == "plan":
            print(f"🔴:{parsed_response.get("content")}")
            continue
        if parsed_response.get("step") == "action":
            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input")
            print(f"Calling Tool: {tool_name} with input {tool_input} ")

            # print(f"☏ {parsed_response.get("content")}")

            if available_tools.get(tool_name) != False:
                output = available_tools[tool_name](tool_input)
                messages.append({"role":"user","content":json.dumps({"step":"observe","output":output})})
                continue

        if parsed_response.get("step") == "output":
            print(f"👽 {parsed_response.get("content")}")
            break





