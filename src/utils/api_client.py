import requests
import time
import logging
import random
import re
import json
import os
from requests.exceptions import RequestException, Timeout
from ratelimit import limits, sleep_and_retry
from openai import OpenAI
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import deque
import hashlib

logger = logging.getLogger(__name__)

CALLS_PER_MINUTE = 60


class QuestionCache:
    def __init__(self, max_size=1000):
        self.cache = deque(maxlen=max_size)

    def add(self, question):
        question_hash = hashlib.md5(question.lower().encode()).hexdigest()
        self.cache.append(question_hash)

    def is_recent(self, question):
        question_hash = hashlib.md5(question.lower().encode()).hexdigest()
        return question_hash in self.cache


question_cache = QuestionCache()


def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session


session = create_session()


def load_settings():
    if os.path.exists("settings.json"):
        with open("settings.json", "r") as f:
            return json.load(f)
    return {}


@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=60)
def make_api_request(prompt, api_choice):
    settings = load_settings()
    max_retries = settings.get("max_retries", 3)
    timeout = settings.get("timeout", 30)

    system_message = """You are a helpful assistant that generates questions and answers. 
    Always include a specific category or subtopic for each question-answer pair you generate. 
    The category should be more specific than the general topic provided.
    Format your response exactly as follows:
    Question: [Your question here]
    Answer: [Your detailed answer here]
    Category: [A specific category or subtopic]"""

    full_prompt = f"{system_message}\n\n{prompt}"

    logger.debug(
        f"Making API request with {api_choice}. Full prompt:\n{full_prompt}")

    if api_choice == 'openai':
        client = OpenAI()  # This will use the OPENAI_API_KEY environment variable
        model = settings.get("openai_model", "gpt-3.5-turbo")
        temperature = settings.get("openai_temperature", 0.7)
        max_tokens = settings.get("openai_max_tokens", 500)

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                logger.debug(f"OpenAI API Response: {response}")
                return response
            except Exception as e:
                logger.error(
                    f"OpenAI API request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                logger.info(
                    f"Waiting for {wait_time} seconds before retrying...")
                time.sleep(wait_time)

        return None
    elif api_choice == 'ollama':
        temperature = settings.get("temperature", 0.7)
        top_p = settings.get("top_p", 0.9)
        model = settings.get("model", "llama3:latest")
        api_url = settings.get(
            "api_url", "http://47.18.235.71:11434/api/generate")

        for attempt in range(max_retries):
            try:
                response = session.post(
                    api_url,
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": False,
                        "temperature": temperature,
                        "top_p": top_p,
                        "seed": int(time.time() * 1000)
                    },
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json()
            except Timeout:
                logger.warning(
                    f"API request timed out (attempt {attempt + 1}/{max_retries})")
            except RequestException as e:
                logger.error(
                    f"API request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                logger.info(
                    f"Waiting for {wait_time} seconds before retrying...")
                time.sleep(wait_time)

        return None
    else:
        logger.error(f"Invalid API choice: {api_choice}")
        return None


def generate_qa_pair(topic, stop_event, api_choice):
    prompts = [
        f"Generate a unique and specific question about {topic} that is unlikely to have been asked before. Provide a detailed answer.",
        f"Create a challenging question related to an advanced aspect of {topic}. Include a comprehensive explanation in your answer.",
        f"Devise a question about a lesser-known fact or concept within {topic}. Ensure your answer is informative and precise.",
        f"Formulate a question that explores the relationship between {topic} and another field. Provide an in-depth answer."
    ]

    prompt = random.choice(prompts) + """
    Format your response exactly as follows:
    Question: [Your unique question here]
    Answer: [Your detailed answer here]
    Category: [A specific category or subtopic within the given topic]
    """

    if stop_event.is_set():
        logger.info("Stopping QA pair generation due to stop event.")
        return None, None, None

    result = make_api_request(prompt, api_choice)
    if result is None:
        logger.error("Failed to generate QA pair for topic '{}' after {} attempts".format(
            topic, load_settings().get('max_retries', 3)))
        return None, None, None

    if api_choice == 'openai':
        response_text = result.choices[0].message.content.strip()
    else:  # ollama
        response_text = result.get('response', '').strip()

    logger.debug(f"Full API response for topic '{topic}':\n{response_text}")

    components = ['Question', 'Answer', 'Category']
    extracted = {}

    for component in components:
        pattern = rf'{component}:\s*(.*?)(?:\n(?:Question|Answer|Category):|$)'
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            extracted[component.lower()] = match.group(1).strip()
            logger.debug(
                f"Extracted {component}: {extracted[component.lower()]}")
        else:
            logger.warning(
                f"Failed to extract {component} for topic '{topic}'")

    logger.debug(f"Extracted components for topic '{topic}': {extracted}")

    if 'category' not in extracted or not extracted['category']:
        logger.info(
            f"Category missing or empty for topic '{topic}'. Inferring from question or using topic.")
        extracted['category'] = infer_category(
            extracted.get('question', ''), topic)

    if all(key in extracted for key in ['question', 'answer', 'category']) and \
       all(extracted[key] for key in ['question', 'answer', 'category']):
        question = extracted['question']
        answer = extracted['answer']
        category = extracted['category']

        if len(question) > 10 and len(answer) > 20 and not question_cache.is_recent(question):
            logger.info(f"Successfully generated QA pair for topic '{topic}'")
            question_cache.add(question)
            return question, answer, category
        else:
            logger.warning(
                f"Generated QA pair too short or recently generated for topic '{topic}'")
    else:
        logger.warning(
            f"Failed to extract all components from API response for topic '{topic}'")

    return None, None, None


def infer_category(question, topic):
    if "python" in question.lower():
        return "Python Programming"
    elif any(word in question.lower() for word in ["math", "geometry", "algebra", "calculus"]):
        return "Mathematics"
    elif any(word in question.lower() for word in ["physics", "chemistry", "biology"]):
        return "Science"
    else:
        return topic.capitalize()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    class MockEvent:
        def is_set(self):
            return False

    stop_event = MockEvent()

    print("Testing Ollama API:")
    question, answer, category = generate_qa_pair(
        "Python programming", stop_event, api_choice='ollama')
    if question and answer and category:
        print("Generated QA pair (Ollama):")
        print("Question:", question)
        print("Answer:", answer)
        print("Category:", category)
    else:
        print("Failed to generate QA pair with Ollama")

    print("\nTesting OpenAI API:")
    question, answer, category = generate_qa_pair(
        "Machine learning", stop_event, api_choice='openai')
    if question and answer and category:
        print("Generated QA pair (OpenAI):")
        print("Question:", question)
        print("Answer:", answer)
        print("Category:", category)
    else:
        print("Failed to generate QA pair with OpenAI")
