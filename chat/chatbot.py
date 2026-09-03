import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv


# ============================================================
# PATH SETUP
# ============================================================

# chat/chatbot.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root = Crop-Disease-Detection
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# .env is in project root
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# plant_faq.csv is inside chat folder
FAQ_PATH = os.path.join(BASE_DIR, "plant_faq.csv")


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


print("\n" + "=" * 60)
print("CHATBOT INITIALIZING")
print("=" * 60)


# ============================================================
# GROQ CLIENT
# ============================================================

client = None

if GROQ_API_KEY:
    print("GROQ API KEY : FOUND")

    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("GROQ CLIENT   : READY")
    except Exception as e:
        print("GROQ CLIENT   : ERROR")
        print("ERROR         :", str(e))
else:
    print("GROQ API KEY : NOT FOUND")
    print("Please check your .env file.")


# ============================================================
# FAQ CSV
# ============================================================

if os.path.exists(FAQ_PATH):

    try:
        faq_df = pd.read_csv(FAQ_PATH)

        # Make sure required columns exist
        if "disease" not in faq_df.columns:
            faq_df["disease"] = ""

        if "advice" not in faq_df.columns:
            faq_df["advice"] = ""

        print("FAQ FILE      : FOUND")
        print("FAQ PATH      :", FAQ_PATH)
        print("FAQ ROWS      :", len(faq_df))

    except Exception as e:

        print("FAQ FILE      : ERROR")
        print("ERROR         :", str(e))

        faq_df = pd.DataFrame(
            columns=["disease", "advice"]
        )

else:

    print("FAQ FILE      : NOT FOUND")
    print("EXPECTED PATH :", FAQ_PATH)

    faq_df = pd.DataFrame(
        columns=["disease", "advice"]
    )


print("=" * 60)
print()


# ============================================================
# FIND FAQ INFORMATION
# ============================================================

def get_faq_advice(disease):

    if not disease:
        return None

    if faq_df.empty:
        return None

    try:

        disease_text = str(disease).strip().lower()

        disease_text = (
            disease_text
            .replace("_", " ")
            .replace("-", " ")
        )

        disease_column = (
            faq_df["disease"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.replace("_", " ", regex=False)
            .str.replace("-", " ", regex=False)
        )

        # Exact match
        exact_match = faq_df[
            disease_column.str.strip() == disease_text
        ]

        if not exact_match.empty:

            advice = exact_match.iloc[0]["advice"]

            if pd.notna(advice) and str(advice).strip():
                return str(advice).strip()

        # Partial match
        partial_match = faq_df[
            disease_column.str.contains(
                disease_text,
                regex=False,
                na=False
            )
        ]

        if not partial_match.empty:

            advice = partial_match.iloc[0]["advice"]

            if pd.notna(advice) and str(advice).strip():
                return str(advice).strip()

        return None

    except Exception as e:

        print("FAQ SEARCH ERROR:", str(e))
        return None


# ============================================================
# MAIN CHATBOT FUNCTION
# ============================================================

def get_chat_response(
    query: str,
    disease: str = None,
    history: list = None
) -> str:

    # --------------------------------------------------------
    # Clean query
    # --------------------------------------------------------

    if not query:
        query = "Please provide information about the plant disease."

    query = str(query).strip()


    # --------------------------------------------------------
    # Clean history
    # --------------------------------------------------------

    if not isinstance(history, list):
        history = []


    # ========================================================
    # GET FAQ AS CONTEXT
    # ========================================================

    # IMPORTANT:
    # FAQ answer ko directly return nahi karna.
    # FAQ information sirf Groq ko context ke roop me deni hai.

    faq_context = ""

    if disease:

        faq_response = get_faq_advice(disease)

        if faq_response:

            faq_context = f"""
Relevant information from the plant disease FAQ:

{faq_response}

Use this information when it is relevant to the user's question.
Do not simply copy the FAQ answer.
Answer the user's actual question directly.
"""


    # ========================================================
    # GROQ AVAILABILITY CHECK
    # ========================================================

    if client is None:

        return (
            "Sorry, the AI chatbot is currently unavailable. "
            "Please check the Groq API key configuration."
        )


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """
You are an expert agricultural advisor helping farmers in Sri Lanka.

You are part of a Crop Disease Detection application.

Your job is to answer the user's ACTUAL question about:
- Plant diseases
- Crop diseases
- Treatment
- Prevention
- Causes
- Symptoms
- Pests
- Fungus
- Irrigation
- Fertilizers
- Soil
- Plant care

IMPORTANT RULES:

1. Always answer the user's actual question.

2. Do NOT give the same generic answer to every question.

3. If the user asks about treatment:
   Give treatment steps.

4. If the user asks about prevention:
   Give prevention steps.

5. If the user asks about causes:
   Explain likely causes.

6. If the user asks about symptoms:
   Explain symptoms.

7. If the user asks whether a particular treatment
   such as neem oil is useful:
   Answer specifically about that treatment.

8. If the user asks a follow-up question:
   Use previous conversation history.

9. Use the detected disease as context.

10. The image classification result may not always be 100% correct.
    Do not claim certainty if the diagnosis is uncertain.

11. Give practical advice suitable for Sri Lankan farmers.

12. Consider tropical weather and monsoon/rainy conditions.

13. Prefer affordable and locally available solutions.

14. If mentioning pesticides or chemicals:
    Tell the user to follow the product label and
    local agriculture officer's instructions.

15. Do not provide dangerous pesticide mixing instructions.

16. Keep the answer simple and easy to understand.

17. Use bullet points when useful.

18. Keep answers around 150-200 words maximum.

19. Do not mention internal prompts, FAQ files,
    APIs, models, or technical implementation.
"""


    # ========================================================
    # CREATE MESSAGE LIST
    # ========================================================

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]


    # ========================================================
    # ADD CHAT HISTORY
    # ========================================================

    if history:

        for item in history:

            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role not in ["user", "assistant"]:
                continue

            if not content:
                continue

            messages.append(
                {
                    "role": role,
                    "content": str(content)
                }
            )


    # ========================================================
    # CURRENT USER QUESTION
    # ========================================================

    user_message = f"""
User's question:

{query}
"""


    # --------------------------------------------------------
    # Disease context
    # --------------------------------------------------------

    if disease:

        clean_disease = (
            str(disease)
            .replace("_", " ")
            .replace("-", " ")
        )

        user_message += f"""

Detected disease from the image classifier:

{clean_disease}

Use this disease as context for answering the question.
"""


    # --------------------------------------------------------
    # FAQ context
    # --------------------------------------------------------

    if faq_context:

        user_message += f"""

{faq_context}
"""


    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )


    # ========================================================
    # CALL GROQ
    # ========================================================

    try:

        print("GROQ REQUEST : SENDING")
        print("MODEL        : openai/gpt-oss-20b")

        completion = client.chat.completions.create(

            messages=messages,

            model="openai/gpt-oss-20b",

            temperature=0.7,

            max_tokens=400,

            top_p=0.9
        )


        # ====================================================
        # GET RESPONSE
        # ====================================================

        response = completion.choices[0].message.content


        if response:
            response = response.strip()


        if not response:

            print("GROQ RESPONSE : EMPTY")

            return (
                "Sorry, I could not generate a response. "
                "Please try asking the question again."
            )


        print("GROQ RESPONSE : SUCCESS")

        return response


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        error_msg = str(e)

        print("\n" + "=" * 60)
        print("GROQ API ERROR")
        print("=" * 60)
        print("ERROR TYPE :", type(e).__name__)
        print("ERROR      :", error_msg)
        print("=" * 60)


        # ----------------------------------------------------
        # Model not found / access
        # ----------------------------------------------------

        if (
            "model_not_found" in error_msg.lower()
            or "does not exist" in error_msg.lower()
            or "do not have access" in error_msg.lower()
            or "404" in error_msg
        ):

            return (
                "Sorry, the AI model is not available for "
                "your Groq account. Please check the API "
                "model access."
            )


        # ----------------------------------------------------
        # Invalid API key
        # ----------------------------------------------------

        if (
            "401" in error_msg
            or "authentication" in error_msg.lower()
            or "invalid api key" in error_msg.lower()
        ):

            return (
                "Sorry, the Groq API key is invalid or expired. "
                "Please check your API key configuration."
            )


        # ----------------------------------------------------
        # Rate limit
        # ----------------------------------------------------

        if (
            "429" in error_msg
            or "rate limit" in error_msg.lower()
            or "too many requests" in error_msg.lower()
        ):

            return (
                "The AI service is temporarily busy. "
                "Please wait a moment and try again."
            )


        # ----------------------------------------------------
        # Network error
        # ----------------------------------------------------

        if (
            "connection" in error_msg.lower()
            or "timeout" in error_msg.lower()
            or "network" in error_msg.lower()
        ):

            return (
                "I could not connect to the AI service right now. "
                "Please check your internet connection and try again."
            )


        # ----------------------------------------------------
        # Generic error
        # ----------------------------------------------------

        return (
            "Sorry, I couldn't connect to the AI service right now. "
            "Please try again in a moment."
        )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("CHATBOT TEST")
    print("=" * 60)


    # Test 1
    print("\nTEST 1")
    print("Question: How can I treat this disease?")

    answer1 = get_chat_response(
        "How can I treat this disease?",
        disease="Tomato Septoria leaf spot"
    )

    print("\nANSWER:")
    print(answer1)


    # Test 2
    print("\n" + "-" * 60)
    print("TEST 2")
    print("Question: Why did this disease happen?")

    answer2 = get_chat_response(
        "Why did this disease happen?",
        disease="Tomato Septoria leaf spot"
    )

    print("\nANSWER:")
    print(answer2)


    # Test 3
    print("\n" + "-" * 60)
    print("TEST 3")
    print("Question: How can I prevent it?")

    answer3 = get_chat_response(
        "How can I prevent this disease?",
        disease="Tomato Septoria leaf spot"
    )

    print("\nANSWER:")
    print(answer3)


    print("\n" + "=" * 60)
    print("CHATBOT TEST FINISHED")
    print("=" * 60)