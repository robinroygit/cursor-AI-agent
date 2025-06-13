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
    print(f"Command executed: {cmd}")
    return f"Command executed: {cmd}"

def get_weather(city: str):
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return f"The Weather in {city} is {response.text}"
    return "Something went wrong fetching weather."

def build_todo_app(_=None):
    app_name = "vite-todo-app"
    template = "react"

    # Remove existing folder if exists
    if os.path.exists(app_name):
        shutil.rmtree(app_name)

    try:
        # Create Vite app with React template
        subprocess.run(
            ["npm", "create", "vite@latest", app_name, "--", "--template", template],
            check=True
        )

        # Install dependencies
        subprocess.run(["npm", "install"], cwd=app_name, check=True)

        # Optional: Write basic Todo component to src/App.jsx
        todo_component = """
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
                <div style={{ padding: 20 }}>
                  <h1>Todo App</h1>
                  <input value={input} onChange={e => setInput(e.target.value)} />
                  <button onClick={addTodo}>Add</button>
                  <ul>
                    {todos.map((todo, index) => <li key={index}>{todo}</li>)}
                  </ul>
                </div>
              );
            }

            export default App;
            """
        with open(os.path.join(app_name, "src", "App.jsx"), "w") as f:
            f.write(todo_component)

        return f"Todo app created successfully in ./{app_name}"
    
    except subprocess.CalledProcessError as e:
        return f"Error during creation: {e}"


# Available tools
available_tools = {
    "get_weather": get_weather,
    "run_command": run_command,
    "build_todo_app": build_todo_app,

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
User Query: Create a todo app
Output: {{"step":"plan", "content": "User wants a new todo app project"}}
Output: {{"step":"plan", "content": "Call build_todo_app tool to scaffold project with working app"}}
Output: {{"step":"action", "function": "build_todo_app", "input": ""}}
Output: {{"step":"observe", "output": "Todo Vite project 'todo-app' created"}}
Output: {{"step":"output", "content": "Todo app initialized using Vite and has working code."}}

Example:
User Query: add a delete button
Output: {{"step":"plan", "content": "User wants to add a delete button"}}
Output: {{"step":"plan", "content": "first get the content from the file and modify the code 'modified_code"}}
Output: {{"step":"plan", "content": "From the available tools I should call run_command"}}
Output: {{"step":"action", "function": "run_command", "input":"cd vite-todo-app/src && echo 'modified_code' > App.jsx"}}
Output: {{"step":"observe", "output": "App.jsx is modified"}}
Output: {{"step":"output", "content": "App.jsx updated with added delete button and has working code."}}

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
