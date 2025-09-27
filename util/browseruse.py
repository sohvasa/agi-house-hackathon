from browser_use_sdk import BrowserUse
import os
from dotenv import load_dotenv

load_dotenv()

class BrowserUseAgent:
    def __init__(self):
        self.client = BrowserUse(api_key=os.getenv("BROWSER_USE_API_KEY"))
    
    def run_browseruse(self, task): # task is the prompt
        task = self.client.tasks.create_task(task=task, llm="gpt-4.1")
        result = task.complete()
        return result.output
    