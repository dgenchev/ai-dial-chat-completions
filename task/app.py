import asyncio

from task.clients.client import DialClient
from task.clients.custom_client import CustomDialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    #TODO:
    # 1.1. Create DialClient
    # (you can get available deployment_name via https://ai-proxy.lab.epam.com/openai/models
    #  you can import Postman collection to make a request, file in the project root `dial-basics.postman_collection.json`
    #  don't forget to add your API_KEY)
    deployment_name = "gpt-4o"  # Default deployment, can be changed
    dial_client = DialClient(deployment_name)
    
    # 1.2. Create CustomDialClient
    custom_dial_client = CustomDialClient(deployment_name)
    
    # For testing: use CustomDialClient to see request/response (TODO item 10)
    # To test with DialClient, change this to: client = dial_client
    client = custom_dial_client
    
    # 2. Create Conversation object
    conversation = Conversation()
    
    # 3. Get System prompt from console or use default -> constants.DEFAULT_SYSTEM_PROMPT and add to conversation
    #    messages.
    system_prompt = input("Provide System prompt or press 'enter' to continue.\n> ").strip()
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT
    
    system_message = Message(role=Role.SYSTEM, content=system_prompt)
    conversation.add_message(system_message)
    
    # 4. Use infinite cycle (while True) and get user message from console
    while True:
        user_input = input("\nType your question or 'exit' to quit.\n> ").strip()
        
        # 5. If user message is `exit` then stop the loop
        if user_input.lower() == "exit":
            print("Exiting the chat. Goodbye!")
            break
        
        # 6. Add user message to conversation history (role 'user')
        user_message = Message(role=Role.USER, content=user_input)
        conversation.add_message(user_message)
        
        # 7. If `stream` param is true -> call DialClient#stream_completion()
        #    else -> call DialClient#get_completion()
        print("AI: ", end='', flush=True)
        if stream:
            ai_message = await client.stream_completion(conversation.get_messages())
        else:
            ai_message = client.get_completion(conversation.get_messages())
        
        # 8. Add generated message to history
        conversation.add_message(ai_message)
    
    # 9. Test it with DialClient and CustomDialClient
    # (To test with DialClient, change client assignment above to: client = dial_client)
    # 10. In CustomDialClient add print of whole request and response to see what you send and what you get in response
    # (Already implemented in CustomDialClient methods)


asyncio.run(
    start(True)
)
