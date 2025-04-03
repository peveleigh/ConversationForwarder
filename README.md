# ConversationForwarder
A Home Assistant custom component to voice assistant conversations to an HTTP endpoint. 

This code was copied from [nodered_conversation](https://github.com/roblandry/nodered_conversation) and modified to meet my needs. There are lots of remnants of the original code and decisions. This was meant to be a quick and dirty solution to get my voice assistant bot up and working. I am hoping, one day, there is an official component that does this.  I have no intention of converting this into an official component or even providing any significant support for this one, but I'm sharing as others might find it useful. Additionally, I'm not really a Python developer. I've worked in a dozen other languages, but Python work has been mostly things like this...modifying something that already works to do what I need it to.

**Prerequisites:**
- Home Assistant 2025.4. This code returns the new continue_conversation flag. If used with an older Home Assistant, an error will be thrown.

**Usage:**
- Copy conversation_forwarder folder to your Home Assistant custom_components folder.
- Restart Home Assistant
- Go to settings->integrations and add the Conversation Forwarder component.
- The configuration requires a URL. This is your bot HTTP endpoint. Note, the call is made from the Home Assistant runtime so account for DNS or reference limitations (ie localhost may not be what you expect).
- You can specify a username and password if desired. This is coded to go into an Authorization header, but I've never tested it.
- In Settings->Voice assistants, create an assist entry using the conversation_forwarder as the Conversation agent.

**Format of HTTP Request**
Method: POST
Authentication: standard http Authorization header
Body: JSON data structure

```
  {
    text: string - The user's spoken text from the STT
    conversation_id: string - HA's conversation ID
    device_id: string - The voice assistant's device id. Note, this will be null if using the built in web conversation feature.
    language: string - Language. ie 'en'
    agent_id: string - The id given to the Conversation Forwarder component (I think)
    extra_system_prompt: string - I've never used this. I think it is or will be an option set within the Assistant.
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

**Some thoughts regarding how I use it and how you might**
- This code does not provide history. My bot uses the conversation_id as a key to that session data. The original nodered_conversation did support history.
- On an HTTP/Connection error, the message back is: "Sorry, unable to connect to endpoint. Check settings and try again."
- On a JSON parsing issue, the message back is: "Sorry, I didn't get a response from endpoint. Check your logs for possible issues."
- I don't let HA process the request first (there's a setting when setting up the Assistant for that). This code doesn't care about that, but while I really like what the Home Assistant team has built, I wanted to override some of the basic logic. In particular, how area choices are handled.
- If you don't already know, the Home Assistant HTTP API doesn't give you everything that Home Assistant knows. This has been a bit frustrating forcing me to have some configuration data on my side, but I've been able to work around any issue that's gotten in my way.
- This will be slower than Alexa. Noticeably. I haven't done a lot of performance metrics, but it looks like the significant gap is in the Speech to Text (STT) layer. Until all of the speech is captured and it is sure the speaker is done, none of the audio is processed. Alexa, most phone systems (IVRs) and others process streaming audio as it is provided.  My LLM is still small and if in memory, the LLM and action code usually executes in under a second.  TTS generation seems to be fairly quick.

**My architecture at the time of writing this README.**
- Primary hardware(I have a nas and another small server for other self hosting). An older PC with the specifications below. It is never significantly taxed.
  - 1080ti NVidia card
  - i7-7700 @ 4.2GHZ
  - 16GB Memory
- Home Assistant running in Docker
- STT: wyoming-whisper, using GPU, large model
- TTS: wyoming-piper, using GPU using one of the higher quality voices. I'm still exploring voices.
- LLM: Ollama, using GPU and running LLama 3.1 with some template modifications for using tools. I'll probably test with other models.
- ConversationBot: Written in Javascript (NodeJS). Mostly because that's what I've been using for my home projects for the last decade or so.