# ConversationForwarder
A Home Assistant custom component to route voice assistant conversations to an HTTP endpoint.

This code was copied from [conversation_fowarder by jimrush](https://github.com/jimrushPersonal/ConversationForwarder) and modified to meet my needs.

**Prerequisites:**
- Home Assistant 2025.4+. This integration uses the `ConversationEntity` API and returns the `continue_conversation` flag. Older versions will throw an error.

**Usage:**
- Copy the `conversation_forwarder` folder to your Home Assistant `custom_components` folder.
- Restart Home Assistant.
- Go to Settings → Integrations and add the Conversation Forwarder component.
- Configure the **endpoint URL** of your bot and whether to **verify SSL** (disabled for self-signed local endpoints).
- In Settings → Voice assistants, create an Assist entry using Conversation Forwarder as the conversation agent.

The endpoint URL and SSL setting can be changed later via the integration's **Options**.

**Format of HTTP Request**
Method: `POST`
Content-Type: `application/json`

```json
{
  "query": "string - the user's spoken text from the STT",
  "cid": "string - conversation id, present when a conversation_id is available"
}
```

**Format of HTTP Response**
The response must be valid JSON. Extra attributes are ignored.

```json
{
  "finish_reason": "string - \"error\" or any other value; when \"error\", continue_conversation is ignored",
  "message": "string - the message played back to the user",
  "continue_conversation": "boolean - true indicates the conversation should continue"
}
```

On connection errors, timeouts, or invalid JSON, a fallback error message is spoken and `finish_reason` is set to `"error"`.
