from dotenv import load_dotenv
load_dotenv()

from backend.agents.knowledge import knowledge_agent

state = {
    "user_input": "What does this document say I need to bring?",
    "uploaded_files": [r"C:\Users\user\OneDrive\Documents\PakAssist\pakassist_rag\2.jpeg"],
}
result = knowledge_agent(state)

print("RESPONSE:\n", result["response"])
print("\nSOURCES:")
for s in result["sources"]:
    print(" -", s["label"], f"(confidence: {s['confidence']})")

    