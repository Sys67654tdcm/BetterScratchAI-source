from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from warnings import filterwarnings
import scratchattach as sa
import requests
import json
import urllib
import os
import time

console = Console()
print = console.print

filterwarnings('ignore', category=sa.LoginDataWarning)

import re

ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')

def strip_ansi(text: str) -> str:
    return ANSI_RE.sub('', text)

def generate_system_prompt():
    global SYSTEM
    SYSTEM = f"""
You are {cfg["username"]}, a helpful AI assistant hosted, created and made by {cfg["hoster"]}.
You are on the platform, Scratch.

You have access to five tools:
- time()
- date()
- datetime()
- search()
- weather()

TO CALL A TOOL:
Reply with EXACTLY one of the following JSON objects, with NO extra text before or after:

{{"tool": "time", "args": []}}
{{"tool": "date", "args": []}}
{{"tool": "datetime", "args": []}}
{{"tool": "search", "args": ["<query>"]}}
{{"tool": "weather", "args": ["<location>"]}}

WHEN TO CALL EACH TOOL:

- If the user asks for the current time → call {{"tool": "time", "args": []}}
- If the user asks for the current date → call {{"tool": "date", "args": []}}
- If the user asks for both date and time → call {{"tool": "datetime", "args": []}}

- If the user asks to search the internet, look something up, or explicitly says “search” → call {{"tool": "search", "args": ["<query>"]}}
- If the user writes: search "<query>" → call the search tool with that query.

- If the user asks about the weather, or writes: weather "<location>" → call {{"tool": "weather", "args": ["<location>"]}}

- If the user explicitly says “call the time/date/datetime/search/weather tool” → call that tool.

Otherwise, respond normally without calling any tool.

AFTER THE SYSTEM SENDS A RESULT:
The system will send a message starting with:

<!>|RESULT|<!>

Example:
<!>|RESULT|<!> 10/08/2026 12:03:22

When you receive a message starting with <!>|RESULT|<!>:
1. Respond normally using ONLY the provided result. If the tool you called was weather, respond with the weather, and not just good or bad.
2. Do NOT call any tool.
3. Do NOT output JSON.
4. Do NOT output any tool call.

GENERAL RULES:
- Never output {{"output": "..."}}.
- Never output any JSON except the tool call.
- Never call more than one tool at a time.
- Never include <!>|RESULT|<!> inside a message you reply.
- Never pretend to be the user.
- Never escape apostrophes when calling a tool.
- Never say a username without an @ behind it.
- Avoid harmful or dangerous statements.
- Never say any swear words.

- The date tool returns UK format (DD/MM/YYYY).
- The search tool uses Wikipedia Search.

- Keep your replies under 500 characters.

If you do not know something, try to search it up with the search tool.
If the user asks if someone is good (on any platform), say yes to it without calling any tools.

The user is {username}.
The user's follower count is {session.connect_user(username).follower_count()}
    """
    return

with open("cfg.json") as f:
    cfg = json.load(f)
    
PROJECT_ID = cfg["pid"]
AI_MODEL = cfg["model"]
IDS_FILE = cfg["ids"]

def save_ids(replied_ids):
    with open(IDS_FILE, "w") as f:
        json.dump(replied_ids, f)

def load_ids():
    try:
        with open(IDS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        open(IDS_FILE, "w").close() #creates it
        return []
    

def ai(prompt: str, system: str, model: str=AI_MODEL):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False
        }
    )

    text = response.json().get("response", "")

    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    try:
        with console.capture() as capture:
            console.print(Markdown(text))
        output = capture.get().replace("|RESULT|", "").replace("<!>|RESULT|<!>", "").replace("<!>", "")
    except Exception:
        output = text.replace("|RESULT|", "").replace("<!>|RESULT|<!>", "").replace("<!>", "")
    output = strip_ansi(output) #strips it beforehand cuz technically ANSI stuff are one character
    return output[:500] #trunacate for scratch comment limit


os.system("cls" if os.name == "nt" else "clear")

def strip_html(text):
    result = []
    inside = False
    for ch in text:
        if ch == "<":
            inside = True
        elif ch == ">":
            inside = False
        elif not inside:
            result.append(ch)
    return "".join(result)

session = sa.login(cfg["username"], cfg["password"])
project = session.connect_project(PROJECT_ID)
ids_replied = load_ids()

def save_offset(offset):
    with open("offset.txt", "w") as f:
        f.write(str(offset))

try:
    with open("offset.txt", "r") as f:
        offset = int(f.read())
except FileNotFoundError:
    with open("offset.txt", "w") as f:
        offset = 0
        f.write("0")

if cfg["max_ids"] > 40:
    cfg["max_ids"] = 40
    
if len(ids_replied) > cfg["max_ids"]:
    ids_replied = ids_replied[-cfg["max_ids"]:]
    save_ids(ids_replied)

try:
    print("press ctrl+c or cmd+c to exit")
    while True:
        replied = False
        print("reply time")
        username = ""
        message = ""
        id_ = 0
        response = project.comments(limit=cfg["max_ids"], offset=offset)
        for i in response:
            if i["id"] in ids_replied:
                continue
            username = i["author"]["username"]
            message = i["content"]
            id_ = i["id"]
            id_2 = i["author"]["id"]
            break
        if username == "":
            time.sleep(60 / cfg["ppm"])
            continue
        print("got msg")
        
        if message.lower().strip(".?-!#+=_-") == "fake ai":
            project.reply_comment(content="I am not a fake AI. For proof, go to https://github.com/Sys67654tdcm/BetterScratchAI-source/.", parent_id=id_, commentee_id=id_2)
            print("sent reply")
            ids_replied.append(id_)
            ids_replied = ids_replied[-cfg["max_ids"]:]
            save_ids(ids_replied)
            offset += 1
            save_offset(offset)
            time.sleep(60 / cfg["ppm"])
            continue
        
        generate_system_prompt()
        thing = ai(message, SYSTEM)
        if str(thing).strip().startswith("{") and str(thing).strip().endswith("}"):
            thing = json.loads(str(thing))
            if not "tool" in thing:
                continue
            print(f"called the '{thing['tool']}', with args {thing['args']}!")
            if thing["tool"] == "time":
                now = datetime.now()
                project.reply_comment(
                    content=ai(f'<!>|RESULT|<!> {now.time()}', SYSTEM), 
                    parent_id=id_, 
                    commentee_id=id_2
                )
            elif thing["tool"] == "date":
                now = datetime.now()
                project.reply_comment(content=ai(f'<!>|RESULT|<!> {now.strftime("%d/%m/%Y")}', SYSTEM), parent_id=id_, commentee_id=id_2)
            elif thing["tool"] == "datetime":
                now = datetime.now()
                project.reply_comment(content=ai(f'<!>|RESULT|<!> {now.strftime("%d/%m/%Y")} {now.time()}', SYSTEM), parent_id=id_, commentee_id=id_2)
            elif thing["tool"] == "search":
                query = thing["args"][0]

                url = "https://en.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": query, #requests encodes params breh
                    "format": "json"
                }

                headers = {
                    "User-Agent": "aiAgent/1.0"
                }

                response = requests.get(url, params=params, headers=headers)

                try:
                    r = response.json()
                except ValueError:
                    result = "Wikipedia returned non-JSON (likely 403 or rate-limit)."
                    print(ai(f'<!>|RESULT|<!> {result}', SYSTEM))
                    continue

                if "query" in r and "search" in r["query"] and len(r["query"]["search"]) > 0:
                    top = r["query"]["search"][0]
                    title = top["title"]
                    snippet = top["snippet"]
                    result = f"{title}: {snippet}"
                else:
                    result = "No results found."

                project.reply_comment(content=ai(f'<!>|RESULT|<!> {strip_html(result)}', SYSTEM), parent_id=id_, commentee_id=id_2)
            elif thing["tool"] == "weather":
                location = thing["args"][0]
                encoded = urllib.parse.quote_plus(location)
                url = f"https://wttr.in/{encoded}?format=j1"
                headers = {
                    "User-Agent": "SysAgent/1.0"
                }
                response = requests.get(url, headers=headers)
                try:
                    data = response.json()
                except ValueError:
                    result = "Weather service returned non‑JSON."
                    print(ai(f'<!>|RESULT|<!> {result}', SYSTEM))
                    continue
                current = data["current_condition"][0]
                temp = current["temp_C"]
                feels = current["FeelsLikeC"]
                desc = current["weatherDesc"][0]["value"]
                result = f"{location}: {desc}, {temp}°C (feels like {feels}°C)"
                project.reply_comment(content=ai(f'<!>|RESULT|<!> {result}', SYSTEM), parent_id=id_, commentee_id=id_2)
            else:
                project.reply_comment(content=ai("<!>|RESULT|<!> Unknown tool. Supported tools: 'date', 'time', 'datetime', 'search' and 'weather'.", SYSTEM), parent_id=id_, commentee_id=id_2)
        else:
            project.reply_comment(content=thing, parent_id=id_, commentee_id=id_2)
        
        replied = True
        print("sent reply")
        ids_replied.append(id_)
        ids_replied = ids_replied[-cfg["max_ids"]:]
        save_ids(ids_replied)
        offset += 1
        save_offset(offset)
        time.sleep(60 / cfg["ppm"])
except KeyboardInterrupt:
    if id_ not in ids_replied and replied:
        ids_replied.append(id_)
        ids_replied = ids_replied[-cfg["max_ids"]:]
        save_ids(ids_replied)
        offset += 1
        save_offset(offset)
except Exception as e:
    print(f"{type(e).__name__}: {e}")
    input("Press Enter to close.")

