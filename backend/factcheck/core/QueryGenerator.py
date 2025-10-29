from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class QueryGenerator:
    def __init__(self, llm_client, prompt, max_query_per_claim: int = 5):
        """Initialize the QueryGenerator class

        Args:
            llm_client (BaseClient): The LLM client used for generating questions.
            prompt (BasePrompt): The prompt used for generating questions.
        """
        self.llm_client = llm_client
        self.prompt = prompt
        self.max_query_per_claim = max_query_per_claim

    def generate_query(self, claims: list[str], generating_time: int = 3, prompt: str = None) -> dict[str, list[str]]:
        """Generate questions for the given claims

        Args:
            claims ([str]): a list of claims to generate questions for.
            generating_time (int, optional): maximum attempts for GPT to generate questions. Defaults to 3.

        Returns:
            dict: a dictionary of claims and their corresponding generated questions.
        """
        generated_questions = {}
        attempts = 0

        while (attempts < generating_time) and (len(generated_questions) < len(claims)):
            try:
                # Create a single prompt with all claims
                if prompt is None:
                    user_input = self._create_batch_prompt(claims)
                else:
                    user_input = prompt.format(claims=claims)
                
                # Use single call instead of multi_call
                messages = self.llm_client.construct_message_list([user_input])[0]
                response = self.llm_client.call([messages])
                
                # Parse the response
                parsed_response = eval(response)
                
                # Extract questions for each claim
                for claim in claims:
                    if claim in parsed_response and claim not in generated_questions:
                        generated_questions[claim] = parsed_response[claim]
                
            except Exception as e:
                logger.info(f"Warning: LLM response parse fail, retry {attempts}. Error: {e}")
            
            attempts += 1

        # Ensure that each claim has at least one question which is the claim itself
        claim_query_dict = {
            claim: [claim] + generated_questions.get(claim, [])[:(self.max_query_per_claim - 1)]
            for claim in claims
        }
        return claim_query_dict

    def _create_batch_prompt(self, claims: list[str]) -> str:
        """Create a prompt for generating questions for multiple claims at once"""
        claims_formatted = "\n".join([f"{i+1}. {claim}" for i, claim in enumerate(claims)])
        
        batch_prompt = f"""Task: Create the minimum number of questions needed to verify the correctness of each given claim.

    Instructions:
    1. Generate only essential questions to verify each claim
    2. Questions should be specific and directly related to the claim
    3. Output in JSON format where each key is the claim text and the value is a list of questions

    Claims:
    {claims_formatted}

    Output format:
    {{
    "claim text 1": ["question"],
    "claim text 2": ["question"],
    ...
    }}

    Output:
    """
        return batch_prompt