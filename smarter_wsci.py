from pathlib import Path
from ollama import chat
import json


question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

FILE_KEYWORDS = {
    "wifi_setup.txt": ["wifi", "wi-fi", "eduroam", "network", "connect", "windows"],
    "password_changes.txt": ["password", "credential", "cached", "change"],
    "service_status.txt": ["operational", "status", "outage", "wi-fi"],
    "email_setup.txt": ["email"],
    "vpn.txt": ["vpn"],
    "printing.txt": ["print", "printer"],
    "classroom_projectors.txt": ["projector", "display"],
}


def select_context(question):
    query = question.lower()
    return [
        f"knowledge/{name}"
        for name, keywords in FILE_KEYWORDS.items()
        if any(keyword in query for keyword in keywords)
    ]


selected_files = select_context(question)

context = ""
for file in selected_files:
    context += Path(file).read_text()
    context += "\n\n"


def compress_context(context, question):
    response = chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "system",
                "content": "Extract only the information relevant to the student's question from the given context. Return only the relevant text.",
            },
            {
                "role": "user",
                "content": f"Question:\n{question}\n\nContext:\n{context}",
            },
        ],
    )
    return response.message.content


compressed_context = compress_context(context, question)

print(len(compressed_context))

state = {
    "problem": question,
    "service_status": {"wifi": "operational"},
    "diagnostic_context": {
        "device": "Windows laptop",
        "wifi_status": "operational",
        "phone_works": True,
    },
}

with open("state.json", "w") as file:
    json.dump(state, file, indent=2)

with open("state.json", "r") as file:
    state = json.load(file)

relevant_state = {
    "service_status": state["service_status"],
    "diagnostic_context": state["diagnostic_context"],
}

response = chat(
    model="qwen2.5:1.5b",
    format="json",
    messages=[
        {
            "role": "system",
            "content": "You are a university IT support assistant. Using only the provided context, answer the student's question. Respond with structured JSON containing 'diagnosis' and 'solution'.",
        },
        {
            "role": "user",
            "content": (
                f"Relevant state:\n{json.dumps(relevant_state)}\n\n"
                f"Context:\n{compressed_context}\n\n"
                f"Student question:\n{question}"
            ),
        },
    ],
)

print(response.message.content)

state["answer"] = response.message.content

with open("state.json", "w") as file:
    json.dump(state, file, indent=2)
