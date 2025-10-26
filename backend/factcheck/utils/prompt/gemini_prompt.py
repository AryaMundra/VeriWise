"""
Optimized prompts for Gemini models.
"""

decompose_prompt = """
Task: Decompose the given text into atomic, self-contained claims.

Instructions:
1. Each claim should be concise (less than 15 words) and self-contained
2. Avoid vague references like 'he', 'she', 'it', 'this' - use complete names
3. Generate at least one claim for each sentence in the text
4. Output must be valid JSON with a single key "claims" containing a list of strings

Example 1:
Text: Mary is a five-year old girl, she likes playing piano and she doesn't like cookies.
Output:
{{
  "claims": [
    "Mary is a five-year old girl.",
    "Mary likes playing piano.",
    "Mary doesn't like cookies."
  ]
}}

Example 2:
Text: Apple Inc. was founded by Steve Jobs in 1976. The company is headquartered in Cupertino.
Output:
{{
  "claims": [
    "Apple Inc. was founded by Steve Jobs.",
    "Apple Inc. was founded in 1976.",
    "Apple Inc. is headquartered in Cupertino."
  ]
}}

Now decompose this text:
Text: {doc}
Output:
"""

restore_prompt = """
Task: Map each claim back to its corresponding text span in the original document.

Instructions:
1. For each claim, find the minimal continuous span in the original text that contains the information
2. Return a JSON dict where keys are claims and values are the corresponding text spans
3. Ensure the spans can be concatenated to form the full original document
4. Copy spans exactly from the original text

Example:
Text: Mary is a five-year old girl, she likes playing piano and she doesn't like cookies.
Claims: ["Mary is a five-year old girl.", "Mary likes playing piano.", "Mary doesn't like cookies."]

Output:
{{
  "Mary is a five-year old girl.": "Mary is a five-year old girl,",
  "Mary likes playing piano.": " she likes playing piano",
  "Mary doesn't like cookies.": " and she doesn't like cookies."
}}

Now map these claims:
Text: {doc}
Claims: {claims}
Output:
"""

checkworthy_prompt = """
Task: Evaluate each statement to determine if it presents objectively verifiable factual information.

Evaluation Criteria:
1. Opinions vs Facts: Distinguish subjective opinions from factual claims
2. Clarity: The statement must have clear, specific references (not "he", "she", "it")
3. Verifiability: Must contain factual elements that can be checked against evidence
4. Note: Even incorrect statements can be checkworthy if they make factual claims

Output Format: JSON with each statement as a key and "Yes" or "No" with rationale as the value.

Example:
Statements:
1. Gary Smith is a distinguished professor of economics.
2. He is a professor at MBZUAI.
3. Obama is the president of the UK.
4. Pizza tastes better than burgers.

Output:
{{
  "Gary Smith is a distinguished professor of economics.": "Yes (Contains verifiable factual information about Gary Smith's professional title and field.)",
  "He is a professor at MBZUAI.": "No (Cannot be verified due to unclear reference - who is 'he'?)",
  "Obama is the president of the UK.": "Yes (Contains verifiable information about political leadership, even though it's incorrect.)",
  "Pizza tastes better than burgers.": "No (This is a subjective opinion, not a factual claim.)"
}}

Now evaluate these statements:
{texts}

Output:
"""

qgen_prompt = """
Task: Create the minimum number of questions needed to verify the correctness of the given claim.

Instructions:
1. Generate only essential questions to verify the claim
2. Questions should be specific and directly related to the claim
3. Output in JSON format with a single key "Questions" and a list of question strings

Example 1:
Claim: Your nose switches back and forth between nostrils. When you sleep, you switch about every 45 minutes. This is to prevent a buildup of mucus. It's called the nasal cycle.
Output:
{{
  "Questions": [
    "Does your nose switch between nostrils?",
    "How often do nostrils switch during sleep?",
    "Why does nostril switching occur?",
    "What is the nasal cycle?"
  ]
}}

Example 2:
Claim: The Stanford Prison Experiment was conducted in the basement of Encina Hall, Stanford's psychology building.
Output:
{{
  "Questions": [
    "Where was the Stanford Prison Experiment conducted?"
  ]
}}

Example 3:
Claim: The Havel-Hakimi algorithm is an algorithm for converting the adjacency matrix of a graph into its adjacency list. It is named after Vaclav Havel and Samih Hakimi.
Output:
{{
  "Questions": [
    "What does the Havel-Hakimi algorithm do?",
    "Who is the Havel-Hakimi algorithm named after?"
  ]
}}

Example 4:
Claim: Social work is a profession that is based in the philosophical tradition of humanism. It is an intellectual discipline that has its roots in the 1800s.
Output:
{{
  "Questions": [
    "What philosophical tradition is social work based on?",
    "When did social work originate?"
  ]
}}

Now generate questions for this claim:
Claim: {claim}
Output:
"""

verify_prompt = """
Task: Evaluate multiple pieces of evidence against a single claim and determine the relationship for each evidence.

Instructions:
1. Carefully review the claim and ALL numbered evidences provided
2. For each evidence, determine if it SUPPORTS, REFUTES, or is IRRELEVANT to the claim
3. Note that different evidences may have different relationships to the claim
4. Consider the relevance and reliability of each piece of evidence
5. Provide clear reasoning for each verdict

Output Format: JSON with keys "evidence_1", "evidence_2", etc., each containing:
- "reasoning": Explain your thought process for this specific evidence
- "relationship": One of "SUPPORTS", "REFUTES", or "IRRELEVANT"

Example 1:

Claim: MBZUAI is located in Abu Dhabi, United Arab Emirates.

Evidences:
[1] Where is MBZUAI located? Answer: Masdar City - Abu Dhabi - United Arab Emirates
[2] MBZUAI is a graduate-level, research-based academic institution located in Masdar City, Abu Dhabi.
[3] The University of Cambridge is a public collegiate research university in Cambridge, United Kingdom.

Output:
{{
  "evidence_1": {{
    "reasoning": "The evidence confirms that MBZUAI is located in Masdar City, Abu Dhabi, United Arab Emirates, which matches the claim.",
    "relationship": "SUPPORTS"
  }},
  "evidence_2": {{
    "reasoning": "The evidence states MBZUAI is in Masdar City, Abu Dhabi, which supports the claim about it being in Abu Dhabi, UAE.",
    "relationship": "SUPPORTS"
  }},
  "evidence_3": {{
    "reasoning": "The evidence is about the University of Cambridge in the UK, which has no relevance to MBZUAI's location.",
    "relationship": "IRRELEVANT"
  }}
}}

Example 2:

Claim: Copper reacts with ferrous sulfate (FeSO4).

Evidences:
[1] Copper is a less reactive metal with a positive standard reduction potential. Metals with high standard reduction potential cannot displace metals with low standard reduction potential. Therefore, copper cannot displace iron from ferrous sulphate solution, and no reaction occurs.
[2] When copper metal is dipped in ferrous sulphate solution, no reaction is observed as copper is less reactive than iron.

Output:
{{
  "evidence_1": {{
    "reasoning": "The evidence explicitly states that copper cannot displace iron from ferrous sulphate solution and no reaction occurs, which directly contradicts the claim.",
    "relationship": "REFUTES"
  }},
  "evidence_2": {{
    "reasoning": "The evidence confirms that no reaction occurs between copper and ferrous sulphate because copper is less reactive than iron, which refutes the claim.",
    "relationship": "REFUTES"
  }}
}}

Example 3:

Claim: The Moon landing occurred in 1969.

Evidences:
[1] The Apollo 11 mission successfully landed on the Moon on July 20, 1969. Neil Armstrong became the first human to walk on the lunar surface.
[2] Apple Inc. is an American multinational technology company headquartered in Cupertino, California.
[3] NASA's Apollo program consisted of multiple missions between 1961 and 1972, with Apollo 11 achieving the first crewed Moon landing in July 1969.

Output:
{{
  "evidence_1": {{
    "reasoning": "The evidence confirms the Moon landing occurred in 1969 during the Apollo 11 mission, directly supporting the claim.",
    "relationship": "SUPPORTS"
  }},
  "evidence_2": {{
    "reasoning": "The evidence is about Apple Inc., which has no connection to the Moon landing or the year 1969 in this context.",
    "relationship": "IRRELEVANT"
  }},
  "evidence_3": {{
    "reasoning": "The evidence confirms that Apollo 11 achieved the first Moon landing in July 1969, which directly supports the claim.",
    "relationship": "SUPPORTS"
  }}
}}

Now analyze this claim against all provided evidences:

Claim: {claim}

Evidences:
{evidence}

Output:
"""


class GeminiPrompt:
    """Gemini-optimized prompts for fact-checking."""
    decompose_prompt = decompose_prompt
    restore_prompt = restore_prompt
    checkworthy_prompt = checkworthy_prompt
    qgen_prompt = qgen_prompt
    verify_prompt = verify_prompt
