"""Prompt templates for Gemini LLM calls."""

CLASSIFICATION_PROMPT = """You are an email classification assistant. Analyze the following email and classify its intent.

Email Subject: {subject}
Email Body:
{body}
Sender: {sender}

Classify the email into exactly one of these categories:
- inquiry: General questions or information requests
- meeting_request: Requests to schedule meetings or calls
- complaint: Complaints, issues, or negative feedback
- follow_up: Follow-ups on previous conversations
- spam: Unsolicited or irrelevant messages
- other: Anything that doesn't fit above categories

Respond in JSON format:
{{
    "intent": "<category>",
    "confidence": <0.0-1.0>,
    "reasoning": "<brief explanation>"
}}
"""

RESPONSE_GENERATION_PROMPT = """You are a professional email assistant. Generate a response to the following email.

Original Email:
Subject: {subject}
From: {sender}
Body: {body}

Classification: {classification}
Context from past interactions:
{context}

Tool results (if any):
{tool_results}

Instructions:
- Write a professional, helpful response
- Keep it concise but thorough
- Address all points raised in the email
- If meeting-related, reference available times from tool results
- Match the appropriate tone for the classification type

Respond in JSON format:
{{
    "response": "<email response text>",
    "tone": "<professional|friendly|formal|empathetic>",
    "confidence": <0.0-1.0>
}}
"""

ENTITY_EXTRACTION_PROMPT = """Extract structured information from the following email text.

Text:
{text}

Extract and return in JSON format:
{{
    "dates": ["<any date references found>"],
    "people": ["<person names mentioned>"],
    "topics": ["<key topics discussed>"],
    "action_items": ["<any action items or requests>"]
}}
"""

DECISION_PROMPT = """You are a tool selection agent. Based on the email classification and context, decide which tools to invoke.

Email Classification: {classification}
Email Subject: {subject}
Email Body: {body}
Available Context: {context}

Available Tools:
- send_email: Send an email response
- create_draft: Create an email draft for review
- check_calendar: Check calendar availability
- create_event: Create a calendar event
- get_contact: Fetch CRM contact information
- update_contact: Update CRM contact data

Rules:
- For meeting_request: always use check_calendar, then create_draft
- For complaint: always use get_contact, then create_draft (never auto-send)
- For inquiry: use get_contact if sender is known, then create_draft
- For follow_up: use get_contact, then create_draft
- For spam: no tools needed

Respond in JSON format:
{{
    "selected_tools": ["<tool_name>", ...],
    "reasoning": "<why these tools>",
    "params": {{
        "<tool_name>": {{"<param>": "<value>"}},
        ...
    }}
}}
"""
