import re

def patch():
    filepath = '/Users/cheekatimallavikas/ClauseGuard/backend/agent_router.py'
    with open(filepath, 'r') as f:
        content = f.read()

    # Add asyncio import
    if "import asyncio" not in content:
        content = content.replace("import json", "import json\nimport asyncio")

    # Wrap the generate_content_async call in asyncio.wait_for
    old_call = """            response = await self._model.generate_content_async(
                combined_prompt,
                generation_config=config
            )"""
    new_call = """            # Prevent internal SDK retry sleep (on 429s) from hanging the backend
            response = await asyncio.wait_for(
                self._model.generate_content_async(
                    combined_prompt,
                    generation_config=config
                ),
                timeout=10.0
            )"""
    content = content.replace(old_call, new_call)
    
    # Change flash-lite to 2.5-flash to split the quota bucket
    content = content.replace('"models/gemini-3.5-flash-lite"', '"models/gemini-2.5-flash"')
    
    with open(filepath, 'w') as f:
        f.write(content)
    print("Patched agent_router.py")

patch()
