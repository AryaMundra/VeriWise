from __future__ import annotations
import json
import time
from typing import List, Optional, Dict, Tuple
from factcheck.utils.logger import CustomLogger
from factcheck.utils.data_class import Evidence
from factcheck.utils.rate_limiter import MultiKeyRateLimitedExecutor

logger = CustomLogger(__name__).getlog()

class ClaimVerify:
    """Optimized claim verification: 1 claim = 1 API call with all evidences batched."""
    
    def __init__(
        self,
        llm_client,
        prompt,
        api_keys: Optional[List[str]] = None,
        max_parallel_verifications: int = 5,
        max_requests_per_minute: int = 10,
        max_requests_per_day: int = 250,
        batch_size: int = 5,  
    ):
        """
        Initialize ClaimVerify with optimized batching.
        
        Args:
            batch_size: Max evidences per claim (default 5)
        """
        self.llm_client = llm_client
        self.prompt = prompt
        self.batch_size = batch_size
        
        # Multi-key setup
        self.use_multi_key = api_keys is not None and len(api_keys) > 1
        
        if self.use_multi_key:

            if callable(llm_client):
                self.client_pool = {key: llm_client(key) for key in api_keys}
            else:
                self.client_pool = {key: llm_client for key in api_keys}

            self.executor = MultiKeyRateLimitedExecutor(
                api_keys=api_keys,
                max_requests_per_minute=max_requests_per_minute,
                max_requests_per_day=max_requests_per_day,
                max_workers=max_parallel_verifications,
                request_window=60,
            )
        else:

            self.client_pool = None
            self.executor = None
    
    
    def verify_claims(
        self,
        claim_evidences_dict: Dict[str, List[Tuple[str, str]]],
    ) -> Dict[str, List[Evidence]]:
        """
        Verify all claims in parallel (multi-key) or sequentially (single-key).
        """
        start_time = time.time()
    
        logger.info(f"Verifying {len(claim_evidences_dict)} claims...")
        
        start_time = time.time()
        
        # Create tasks: one task per claim
        claim_tasks = []
        for claim, evidence_tuples in claim_evidences_dict.items():
            claim_tasks.append((claim, evidence_tuples))
        
        # Process in parallel (multi-key) or sequential (single-key)
        if self.use_multi_key:
            logger.info(f" Processing {len(claim_tasks)} claims IN PARALLEL...")
            results = self.executor.map(self._verify_single_claim, claim_tasks)
            results_dict = {claim: evidences for claim, evidences in results}
        else:
            logger.info(f" Processing {len(claim_tasks)} claims sequentially...")
            results_dict = {}
            for task in claim_tasks:
                claim, evidences = self._verify_single_claim(task, api_key=None)
                results_dict[claim] = evidences
        
        duration = time.time() - start_time
        logger.info(
            f"Verification complete:\n"
            f"   - Claims: {len(claim_evidences_dict)}\n"
            f"   - Duration: {duration:.2f}s\n"
            f"   - Avg per claim: {duration/len(claim_evidences_dict):.2f}s"
        )
        
        return results_dict
    
    def _verify_single_claim(
        self,
        claim_task: Tuple[str, List[Tuple[str, str]]],
        api_key: str = None
    ) -> Tuple[str, List[Evidence]]:
        """
        Verify a single claim with all its evidences in one API call.
        
        Args:
            claim_task: (claim, [(evidence_text, url), ...])
            api_key: API key (provided by executor in multi-key mode)
            
        Returns:
            (claim, [Evidence objects])
        """
        claim, evidence_tuples = claim_task
        
        # Get appropriate client
        if self.use_multi_key and api_key:
            client = self.client_pool[api_key]
            key_id = f"key_{list(self.client_pool.keys()).index(api_key)}"
        else:
            client = self.llm_client
            key_id = "single_key"
        
        logger.info(f"  {key_id} → Claim: {claim[:60]}... ({len(evidence_tuples)} evidences)")
        

        if len(evidence_tuples) > self.batch_size:
            logger.warning(
                f"   Claim has {len(evidence_tuples)} evidences, "
                f"truncating to {self.batch_size}"
            )
            evidence_tuples = evidence_tuples[:self.batch_size]
        
        # Format evidences for prompt
        evidences_text = ""
        for i, (evidence_text, _) in enumerate(evidence_tuples, 1):

            evidence_truncated = evidence_text[:500] if len(evidence_text) > 500 else evidence_text
            evidences_text += f"[Evidence {i}]: {evidence_truncated}\n"
        try:
  
            if hasattr(self.prompt, 'verify_prompt'):
                prompt_template = self.prompt.verify_prompt
            else:
      
                prompt_template = self.prompt
            
            prompt_text = prompt_template.format(
                claim=claim,
                evidence=evidences_text.strip()
            )
        except Exception as e:
    
            # Return fallback evidences
            return (claim, self._create_fallback_evidences(claim, evidence_tuples, str(e)))
        
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt_text}
            ]
            response = client._call(messages)
            # Parse response
            verdicts = self._parse_batch_response(response)
            

            if not isinstance(verdicts, dict):
                logger.error(f"Converting {type(verdicts)} to empty dict")
                verdicts = {}

            
            # Parse response
            verdicts = self._parse_batch_response(response)
            
            # Create Evidence objects
            evidence_objects = []
            for i, (evidence_text, evidence_url) in enumerate(evidence_tuples, start=1):
                evidence_key = f"evidence_{i}"
                verdict = verdicts.get(evidence_key, {})
                
                evidence_obj = Evidence(
                    claim=claim,
                    text=evidence_text,
                    url=evidence_url,
                    reasoning=verdict.get("reasoning", "No reasoning provided"),
                    relationship=verdict.get("relationship", "IRRELEVANT")
                )
                evidence_objects.append(evidence_obj)
            
            logger.info(f" Verified {len(evidence_objects)} evidences")
            return (claim, evidence_objects)
            
        except Exception as e:
            logger.error(f"Verification failed for claim: {str(e)}")
            return (claim, self._create_fallback_evidences(claim, evidence_tuples, str(e)))

    def _create_fallback_evidences(
        self,
        claim: str,
        evidence_tuples: List[Tuple[str, str]],
        error_msg: str
    ) -> List[Evidence]:
        """Create fallback Evidence objects when verification fails."""
        fallback_evidences = []
        for evidence_text, evidence_url in evidence_tuples:
            evidence_obj = Evidence(
                claim=claim,
                text=evidence_text,
                url=evidence_url,
                reasoning=f"Verification failed: {error_msg}",
                relationship="IRRELEVANT"
            )
            fallback_evidences.append(evidence_obj)
        return fallback_evidences

    
    def _parse_batch_response(self, response: str) -> Dict:
        """Parse JSON response from LLM - always returns dict."""
        try:
            response = response.strip()
            
            # Remove markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                if len(lines) > 2:
                    response = "\n".join(lines[1:-1])
            
            # Parse JSON
            parsed = json.loads(response)
            
            # Ensure it's a dict
            if isinstance(parsed, dict):
                return parsed
            else:
                logger.error(f"Parsed JSON is not a dict: {type(parsed)}")
                return {}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            logger.error(f"Response: {response[:300]}...")
            return {}  # Always return dict!
        except Exception as e:
            logger.error(f"Parse error: {str(e)}")
            return {}  # Always return dict!

