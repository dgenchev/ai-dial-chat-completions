import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    _endpoint: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def get_completion(self, messages: list[Message]) -> Message:
        #TODO:
        # Take a look at README.md of how the request and regular response are looks like!
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "Api-Key": self._api_key,
            "Content-Type": "application/json"
        }
        # 2. Create request_data dictionary with:
        #   - "messages": convert messages list to dict format using msg.to_dict() for each message
        request_data = {
            "messages": [msg.to_dict() for msg in messages]
        }
        # Print request for debugging (TODO item 10)
        print("=== REQUEST ===")
        print(json.dumps(request_data, indent=2))
        print("===============")
        
        # 3. Make POST request using requests.post() with:
        #   - URL: self._endpoint
        #   - headers: headers from step 1
        #   - json: request_data from step 2
        response = requests.post(
            url=self._endpoint,
            headers=headers,
            json=request_data
        )
        
        # Print response for debugging (TODO item 10)
        print("=== RESPONSE ===")
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        print("================")
        
        # 5. If status code != 200 then raise Exception with format: f"HTTP {response.status_code}: {response.text}"
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
        # 4. Get content from response, print it and return message with assistant role and content
        response_json = response.json()
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            raise Exception("No choices in response found")
        
        content = response_json["choices"][0]["message"]["content"]
        print(content)
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        #TODO:
        # Take a look at README.md of how the request and streamed response chunks are looks like!
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "Api-Key": self._api_key,
            "Content-Type": "application/json"
        }
        # 2. Create request_data dictionary with:
        #    - "stream": True  (enable streaming)
        #    - "messages": convert messages list to dict format using msg.to_dict() for each message
        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages]
        }
        
        # Print request for debugging (TODO item 10)
        print("=== REQUEST ===")
        print(json.dumps(request_data, indent=2))
        print("===============")
        
        # 3. Create empty list called 'contents' to store content snippets
        contents = []
        
        # 4. Create aiohttp.ClientSession() using 'async with' context manager
        async with aiohttp.ClientSession() as session:
            # 5. Inside session, make POST request using session.post() with:
            #    - URL: self._endpoint
            #    - json: request_data from step 2
            #    - headers: headers from step 1
            #    - Use 'async with' context manager for response
            async with session.post(
                url=self._endpoint,
                json=request_data,
                headers=headers
            ) as response:
                # Print response status for debugging (TODO item 10)
                print("=== RESPONSE (Streaming) ===")
                print(f"Status Code: {response.status}")
                
                # Check for error status codes
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Error Response: {error_text}")
                    print("===========================")
                    raise Exception(f"HTTP {response.status}: {error_text}")
                
                # 6. Get content from chunks (don't forget that chunk start with `data: `, final chunk is `data: [DONE]`), print
                #    chunks, collect them and return as assistant message
                buffer = ""
                async for chunk_bytes in response.content.iter_any():
                    buffer += chunk_bytes.decode('utf-8')
                    
                    # Process complete lines from buffer
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                        
                        # Check for [DONE]
                        if line == "data: [DONE]":
                            break
                        
                        # Check if line starts with "data: "
                        if line.startswith("data: "):
                            chunk_data = line[6:]  # Remove "data: " prefix
                            
                            try:
                                chunk_json = json.loads(chunk_data)
                                if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                                    delta = chunk_json["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        content_chunk = delta["content"]
                                        print(content_chunk, end='', flush=True)  # Print content as it streams
                                        contents.append(content_chunk)
                            except json.JSONDecodeError:
                                pass
                
                print()  # New line after streaming
                print("===========================")
        
        # Return message with collected content
        content = "".join(contents)
        return Message(role=Role.AI, content=content)

