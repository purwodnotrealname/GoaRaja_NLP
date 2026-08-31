import ollama
import re
import logging
from prompts import INTENT_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

MODEL_NAME = "llama3.2:3b"
VALID_INTENTS = set(range(1, 8))  


def classify_intent(user_question: str) -> int:
    prompt = INTENT_CLASSIFICATION_PROMPT.format(user_question=user_question)

    try:
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={
                "temperature": 0,      
                "num_predict": 5,     
                "top_p": 1,
                "top_k": 1,
            },
        )
        raw_output = response["response"].strip()
        intent = _parse_intent(raw_output)

        logger.info(f"Question: '{user_question}'Raw LLM output: '{raw_output}'Parsed intent: {intent}")
        return intent

    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return 0


def _parse_intent(raw_output: str) -> int:
    match = re.search(r"\d+", raw_output)
    if not match:
        return 0

    intent = int(match.group())
    if intent not in VALID_INTENTS:
        return 0

    return intent
