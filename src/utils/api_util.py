
def request_and_log_api_openrouter(messages, model, max_tokens, temperature=0.0, max_retries=1, retry_delay=5):
    """
    New OpenRouter-based implementation for requesting and logging API.

    Args:
    messages (list): The list of messages.
    model (str): The model name.
    max_tokens (int): The maximum number of output tokens limit.
    temperature (float): Sampling temperature (0.0 to 1.0). Default is 0.0 (deterministic).
    max_retries (int): Maximum number of retries in case of failure.
    retry_delay (int): Delay in seconds between retries.

    Returns:
    str: The response content.
    """
    # Create a client for OpenRouter
    api_key = "your_api_key"

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,  # Replace with your OpenRouter API key
    )

    retries = 0
    while retries < max_retries:
        try:
            # Create a completion with the client
            completion = client.chat.completions.create(
                extra_body={},
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,  # Use the provided temperature
                top_p=1.0,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False
            )

            # Get the content of the first choice
            response = completion.choices[0].message.content

            # Return the response
            return response

        except Exception as e:
            retries += 1
            print(f"Attempt {retries} failed: {e}")
            if retries < max_retries:
                time.sleep(retry_delay)  # Wait before retrying
            else:
                print("Max retries reached. Unable to complete the request.")
                raise  # Re-raise the exception if max retries are reached

    return None  # Return None if all retries fail

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

def request_and_log_api_openrouter_parallel(messages, model, max_tokens, temperature=0.0, max_retries=1, retry_delay=5, concurrency=1):
    """
    Parallel version of OpenRouter-based implementation for requesting and logging API.

    Args:
    messages (list): The list of messages.
    model (str): The model name.
    max_tokens (int): The maximum number of output tokens limit.
    temperature (float): Sampling temperature (0.0 to 1.0). Default is 0.0 (deterministic).
    max_retries (int): Maximum number of retries in case of failure.
    retry_delay (int): Delay in seconds between retries.
    concurrency (int): Number of concurrent requests. Default is 1 (no concurrency).

    Returns:
    list: A list of response contents. If concurrency=1, returns a single response as a string.
    """
    # Create a client for OpenRouter
    api_key = "xxxx"

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,  # Replace with your OpenRouter API key
    )

    def _make_request():
        """Helper function to make a single API request with retries."""
        retries = 0
        while retries < max_retries:
            try:
                # Create a completion with the client
                completion = client.chat.completions.create(
                    extra_body={},
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,  # Use the provided temperature
                    top_p=1.0,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                    stream=False
                )

                # Get the content of the first choice
                response = completion.choices[0].message.content
                return response

            except Exception as e:
                retries += 1
                print(f"Attempt {retries} failed: {e}")
                if retries < max_retries:
                    time.sleep(retry_delay)  # Wait before retrying
                else:
                    print("Max retries reached. Unable to complete the request.")
                    return None  # Return None if max retries are reached

    if concurrency == 1:
        # Single request (no concurrency)
        return _make_request()
    else:
        # Concurrent requests
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(_make_request) for _ in range(concurrency)]
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"Concurrent request failed: {e}")
            return results