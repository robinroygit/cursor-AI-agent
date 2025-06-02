from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import json
import requests
import os
import subprocess
import shutil

# Load environment variables
load_dotenv()

client = OpenAI()

def run_command(cmd: str):
    result = os.system(cmd)
    return f"Command executed: {cmd}"

def get_weather(city: str):
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return f"The Weather in {city} is {response.text}"
    return "Something went wrong fetching weather."

def build_todo_app(_: str = ""):
    project_name = "todo-app"

    # Remove if folder exists
    if os.path.exists(project_name):
        shutil.rmtree(project_name)

    # Create Vite + React app
    subprocess.run(f"npm create vite@latest {project_name} -- --template react", shell=True)

    # Install dependencies
    subprocess.run(f"cd {project_name} && npm install", shell=True)

    # Basic Todo App code
    app_code = '''
import { useState } from 'react';
import './App.css';

function App() {
  const [todos, setTodos] = useState([]);
  const [input, setInput] = useState("");

  const addTodo = () => {
    if (!input) return;
    setTodos([...todos, input]);
    setInput("");
  };

  return (
    <div className="App">
      <h1>Todo App</h1>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={addTodo}>Add</button>
      <ul>
        {todos.map((todo, idx) => (
          <li key={idx}>{todo}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;
'''

    app_path = os.path.join(project_name, "src", "App.jsx")
    with open(app_path, "w") as f:
        f.write(app_code)

    return f"Todo app created successfully in ./{project_name} folder."


# Available tools
available_tools = {
    "get_weather": get_weather,
    "run_command": run_command,
    "build_todo_app": build_todo_app
}

# System prompt
SYSTEM_PROMPT = f"""
You are a helpful AI Assistant specialized in resolving user queries.
You work on start, plan, action, observe, and output mode.

For the given user query and available tools, plan the step-by-step execution.
Based on the planning, select the relevant tool from the available tools.
Then perform an action to call the tool.

Wait for the observation and based on the output, resolve the user query.

Rules:
- Follow the Output JSON Format.
- Always perform one step at a time and wait for the next input.
- Carefully analyze the user query.

Output JSON Format:
{{
    "step":"string",
    "content":"string",
    "function":"The name of the function if the step is action",
    "input":"The input parameter for the function"
}}

Available Tools:
- "get_weather": Takes a city name as input and returns the current weather.
- "run_command": Takes a Linux command as a string, executes it, and returns output.
- "build_todo_app": Takes no input and creates a basic todo app in a folder using Vite and React.

Example:
User Query: What is the weather of new york?
Output:{{"step":"plan", "content": "The User is interested in weather data of new york"}}
Output:{{"step":"plan", "content": "From the available tools I should call get_weather"}}
Output:{{"step":"action", "function": "get_weather", "input": "new york"}}
Output:{{"step":"observe", "output": "Partly cloudy +18°C"}}
Output:{{"step":"output", "content": "The Weather of New York seems to be partly cloudy and 18°C."}}

Example:
User Query: create a file with name weather.txt
Output:{{"step":"plan", "content": "The User is interested to create a file"}}
Output:{{"step":"plan", "content": "From the available tools I should call run_command"}}
Output:{{"step":"action", "function": "run_command", "input": "touch weather.txt"}}
Output:{{"step":"observe", "output": "weather.txt"}}
Output:{{"step":"output", "content": "weather.txt file has been created"}}

Example:
User Query: build todo app
Output:{{"step":"plan", "content": "The user wants to build a todo app."}}
Output:{{"step":"plan", "content": "From the available tools I should call build_todo_app."}}
Output:{{"step":"action", "function": "build_todo_app", "input": ""}}
Output:{{"step":"observe", "output": "Todo app created successfully in ./todo-app folder."}}
Output:{{"step":"output", "content": "The Todo App has been created successfully in the todo-app directory."}}

Today Date is {datetime.now()}
"""

# Chat loop
messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

while True:
    query = input("🧠 User > ")
    messages.append({"role": "user", "content": query})

    while True:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=messages
        )

        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})
        parsed_response = json.loads(content)

        if parsed_response.get("step") == "plan":
            print(f"🧩 Plan: {parsed_response.get('content')}")
            continue

        if parsed_response.get("step") == "action":
            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input")
            print(f"⚙️ Action: Calling `{tool_name}` with input: {tool_input}")

            if available_tools.get(tool_name):
                output = available_tools[tool_name](tool_input)
                messages.append({"role": "user", "content": json.dumps({"step": "observe", "output": output})})
                continue

        if parsed_response.get("step") == "output":
            print(f"✅ Output: {parsed_response.get('content')}")
            break
