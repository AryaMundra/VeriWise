from factcheck.utils.logger import CustomLogger
import nltk
import json  
import re    

logger = CustomLogger(__name__).getlog()

class Decompose:
    def __init__(self, llm_client, prompt):
        """Initialize the Decompose class
        
        Args:
            llm_client (BaseClient): The LLM client used for decomposing documents into claims.
            prompt (BasePrompt): The prompt used for fact checking.
        """
        self.llm_client = llm_client
        self.prompt = prompt
        self.doc2sent = self._nltk_doc2sent
    
    def _nltk_doc2sent(self, text: str):
        """Split the document into sentences using nltk
        
        Args:
            text (str): the document to be split into sentences
        
        Returns:
            list: a list of sentences
        """
        sentences = nltk.sent_tokenize(text)
        sentence_list = [s.strip() for s in sentences if len(s.strip()) >= 3]
        return sentence_list
    
    def _clean_json_response(self, response: str) -> str:
        """
        Clean Gemini response to extract JSON.
        Handles markdown code blocks and extra text.
        """


        response = re.sub(r'```\s*', '', response)
        
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return match.group(0)
        
        return response.strip()
    
    def getclaims(self, doc: str, num_retries: int = 3, prompt: str = None) -> list[str]:
        """Use LLM to decompose a document into claims
        
        Args:
            doc (str): the document to be decomposed into claims
            num_retries (int, optional): maximum attempts for LLM to decompose the document into claims. Defaults to 3.
        
        Returns:
            list: a list of claims
        """
        if prompt is None:
            user_input = self.prompt.decompose_prompt.format(doc=doc).strip()
        else:
            user_input = prompt.format(doc=doc).strip()
        
        claims = None
        messages = self.llm_client.construct_message_list([user_input])
        
        for i in range(num_retries):
            try:
                response = self.llm_client.call(
                    messages=messages,
                    num_retries=1,
                    seed=42 + i,
                )
                
                # Clean the response
                cleaned_response = self._clean_json_response(response)
                
                # Parse JSON
                try:
                    parsed = json.loads(cleaned_response)
                except json.JSONDecodeError:
                
                    logger.warning(f"JSON decode failed, trying eval. Response: {response[:200]}")
                    parsed = eval(cleaned_response)
                
                claims = parsed.get("claims", [])
                
                if isinstance(claims, list) and len(claims) > 0:
                    logger.info(f"Successfully extracted {len(claims)} claims")
                    break
                    
            except Exception as e:
                logger.error(f"Parse LLM response error {e}, response is: {response[:500]}")
                logger.error(f"Prompt was: {messages}")
        
        if isinstance(claims, list) and len(claims) > 0:
            return claims
        else:
            logger.warning("LLM did not output claims correctly, falling back to sentence splitting")
            claims = self.doc2sent(doc)
            return claims
    
    def restore_claims(self, doc: str, claims: list, num_retries: int = 3, prompt: str = None) -> dict[str, dict]:
        """Use LLM to map claims back to the document
        
        Args:
            doc (str): the document to be decomposed into claims
            claims (list[str]): a list of claims to be mapped back to the document
            num_retries (int, optional): maximum attempts for LLM to decompose the document into claims. Defaults to 3.
        
        Returns:
            dict: a dictionary of claims and their corresponding text spans and start/end indices.
        """
        def restore(claim2doc):
            claim2doc_detail = {}
            flag = True
            
            for claim, sent in claim2doc.items():
                st = doc.find(sent)
                if st != -1:
                    claim2doc_detail[claim] = {"text": sent, "start": st, "end": st + len(sent)}
                else:
                    flag = False
            
            cur_pos = -1
            texts = []
            for k, v in claim2doc_detail.items():
                if v["start"] < cur_pos + 1 and v["end"] > cur_pos:
                    v["start"] = cur_pos + 1
                    flag = False
                elif v["start"] < cur_pos + 1 and v["end"] <= cur_pos:
                    v["start"] = v["end"]  
                    flag = False
                elif v["start"] > cur_pos + 1:
                    v["start"] = cur_pos + 1
                    flag = False
                
                v["text"] = doc[v["start"] : v["end"]]
                texts.append(v["text"])
                claim2doc_detail[k] = v
                cur_pos = v["end"]
            
            return claim2doc_detail, flag
        
        if prompt is None:
            user_input = self.prompt.restore_prompt.format(doc=doc, claims=claims).strip()
        else:
            user_input = prompt.format(doc=doc, claims=claims).strip()
        
        messages = self.llm_client.construct_message_list([user_input])
        tmp_restore = {}
        
        for i in range(num_retries):
            try:
                response = self.llm_client._call(
                    messages=messages,
                    num_retries=1,
                    seed=42 + i,
                )
                
                # Clean and parse JSON
                cleaned_response = self._clean_json_response(response)
                
                try:
                    claim2doc = json.loads(cleaned_response)
                except json.JSONDecodeError:
                    logger.warning(f"JSON decode failed for restore_claims, trying eval")
                    claim2doc = eval(cleaned_response)
                
                assert len(claim2doc) == len(claims)
                claim2doc_detail, flag = restore(claim2doc)
                
                if flag:
                    return claim2doc_detail
                else:
                    tmp_restore = claim2doc_detail
                    raise Exception("Restore claims not satisfied.")
                    
            except Exception as e:
                logger.error(f"Parse LLM response error {e}, response is: {response[:500]}")
                logger.error(f"Prompt was: {messages}")
        
        return tmp_restore
