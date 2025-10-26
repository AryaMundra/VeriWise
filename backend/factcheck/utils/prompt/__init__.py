from .gemini_prompt import GeminiPrompt

prompt_map = {
    "gemini_prompt": GeminiPrompt,
}


def prompt_mapper(prompt_name: str):
    if prompt_name in prompt_map:
        return prompt_map[prompt_name]()
    else:
        raise NotImplementedError(f"Prompt {prompt_name} not implemented.")