import sys, os
sys.path.insert(0, os.getcwd())
import path_setup
from plugin.session_analyzer import SiliconFlowLLMClient

client = SiliconFlowLLMClient()
result = client.generate("Say 'hello world' in exactly those words")
if result:
    print("API call successful!")
    print(result)
else:
    print("API call failed")