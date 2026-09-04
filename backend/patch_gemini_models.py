import re

def patch():
    filepath = '/Users/cheekatimallavikas/ClauseGuard/backend/agent_router.py'
    with open(filepath, 'r') as f:
        content = f.read()
    
    content = content.replace('"gemini-1.5-flash"', '"models/gemini-3.5-flash"')
    content = content.replace('"gemini-1.5-flash-8b"', '"models/gemini-3.5-flash-lite"')

    with open(filepath, 'w') as f:
        f.write(content)
    print("Patched agent_router.py")

patch()
