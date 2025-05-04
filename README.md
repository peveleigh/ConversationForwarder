# ConversationForwarder
A Home Assistant custom component to route voice assistant conversations to an HTTP endpoint. 

This code was copied from [conversation_fowarder by jimrush](https://github.com/jimrushPersonal/ConversationForwarder) and modified to meet my needs.

**Prerequisites:**
- Home Assistant 2025.4. This code returns the new continue_conversation flag. If used with an older Home Assistant, an error will be thrown.

**Usage:**
- Copy conversation_forwarder folder to your Home Assistant custom_components folder.
- Restart Home Assistant
- Go to settings->integrations and add the Conversation Forwarder component.
- The configuration requires a URL. This is your bot HTTP endpoint. Note, the call is made from the Home Assistant runtime so account for DNS or reference limitations (ie localhost may not be what you expect).
- In Settings->Voice assistants, create an assist entry using the conversation_forwarder as the Conversation agent.

**Format of HTTP Request**
Method: GET
Body: JSON data structure

```
  {
    query: string - The user's spoken text from the STT
  }
```

**Format of HTTP Response**
The response needs to be valid JSON. Extra attributes may be added as they will be ignored (I put internal and diagnostic data for my test cases in the structure).

```
  {
    finish_reason: string - error or any other value. If error, the continuation_conversation flag will be ignored. I've come to the conclusion that the endpoint should handle all of the errors, if possible. HA doesn't really need to know. This is really left over logic I never removed.
    message: string - The message to play back to the user.
    continue_conversation: boolean - true indicates the conversation should continue
  }
```
