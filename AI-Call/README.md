# AI Calling Agent

Overview

This project implements an AI-based screening system using WebSocket connections to handle voice calls, transcribe speech, process the transcription with a language model, and generate responses through text-to-speech. The system is designed to interact with multiple services like Twilio, Deepgram, ElevenLabs, AWS, and a language model processor.

Services Used:

Twilio: For initiating and managing phone calls.
Deepgram: For speech-to-text transcription.
ElevenLabs: For text-to-speech conversion.
AWS: For queuing messages and publishing notifications using SNS.
Language Model Processor: For generating responses to transcribed speech.

Features:

WebSocket Communication: A WebSocket server listens for incoming messages from the phone call through Twilio and handles audio streaming in real-time.
Speech-to-Text: Deepgram processes the incoming speech and transcribes it into text.
Language Model Processing: Once transcription exceeds a small silence threshold, the system sends the text to a language model to generate a response.
Text-to-Speech: The generated response is converted to speech using ElevenLabs and sent back to the phone call.
AWS Integration: The system integrates with AWS SQS for message queuing and SNS for sending notifications.

Modules:

TwilioService: Handles Twilio API interactions for call initiation and management.
ElevenLabsService: Handles text-to-speech conversion using ElevenLabs.
DeepgramService: Manages real-time audio transcription using Deepgram.
LanguageModelProcessor: Processes text input and generates responses using a language model.
WebSocketServer: Manages WebSocket connections and routes the incoming audio data for transcription, processing, and response generation.

Key Constants:

SILENCE_THRESHOLD: Defines the duration (in seconds) of silence after which the system triggers a response.
small_silence_threshold: The threshold to detect small silences in speech (0.2 seconds).
big_silence_threshold: The threshold to detect long silences (8 seconds).
stream_sid: Unique identifier for the WebSocket audio stream.

Running the Application:

We need a public url at local host 5000 and this must be listed in config.ini, please use url with "http://" as that will result in error , Directly type url .

To run the WebSocket server, execute the following command:

	conda deactivate
	python3 -m venv myenv
	source myenv/bin/activate
	pip install -r requirements.txt
	python3 Main_AI_Call.py

This starts the WebSocket server on localhost:5001 and begins polling the AWS SQS queue for new messages.

You will recieve calls and after the call is finished , You will get chat logs in AWS SNS topic.
