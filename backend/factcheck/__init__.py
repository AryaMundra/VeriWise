import concurrent.futures
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict

from factcheck.utils.llmclient import CLIENTS, model2client
from factcheck.utils.prompt import prompt_mapper
from factcheck.utils.logger import CustomLogger
from factcheck.utils.api_config import load_api_config
from factcheck.utils.data_class import PipelineUsage, FactCheckOutput, ClaimDetail, FCSummary
from factcheck.core import (
    Decompose,
    Checkworthy,
    QueryGenerator,
    retriever_mapper,
    ClaimVerify,
)

logger = CustomLogger(__name__).getlog()


class FactCheck:
    """
    Main fact-checking pipeline that orchestrates the entire workflow.
    
    Supports multiple LLM backends (OpenAI, Gemini, etc.) and retrieval methods.
    NEW: Multi-API-Key support for 5x faster verification!
    """
    
    def __init__(
        self,
        default_model: str = "gemini-2.5-flash",
        client: str = None,
        prompt: str = "gemini_prompt",
        retriever: str = "serper",
        
        # NEW: Multi-API-Key support
        api_keys: Optional[List[str]] = None,  # List of Gemini API keys from different projects
        
        decompose_model: Optional[str] = None,
        checkworthy_model: Optional[str] = None,
        query_generator_model: Optional[str] = None,
        evidence_retrieval_model: Optional[str] = None,
        claim_verify_model: Optional[str] = None,
        api_config: Optional[dict] = None,
        num_seed_retries: int = 1,
        
        # NEW: Performance tuning
        max_parallel_verifications: int = None,  # Auto-adjust based on num keys
    ):
        """
        Initialize the FactCheck pipeline.
        
        Args:
            default_model: Default LLM model for all steps (default: "gemini-2.5-flash")
            client: Specific client to use (auto-detected if None)
            prompt: Prompt template set to use (default: "gemini_prompt")
            retriever: Evidence retrieval method (default: "serper")
            
            api_keys: List of Gemini API keys from DIFFERENT Google Cloud projects.
                     Using multiple keys multiplies throughput:
                     - 1 key: 10 RPM
                     - 5 keys: 50 RPM (5x faster!)
                     
            decompose_model: Model for claim decomposition
            checkworthy_model: Model for checkworthiness filtering
            query_generator_model: Model for query generation
            evidence_retrieval_model: Model for evidence retrieval
            claim_verify_model: Model for claim verification
            api_config: API configuration dictionary
            num_seed_retries: Number of retries with different seeds
            
            max_parallel_verifications: Number of parallel verification threads.
                                       Auto-set based on number of API keys if None.
        """
        # Load prompt templates
        self.prompt = prompt_mapper(prompt_name=prompt)
        
        # Load API configurations
        self.load_config(api_config=api_config)
        
        # Store API keys for multi-key verification
        self.api_keys = api_keys
        
        # Log multi-key mode
        if api_keys and len(api_keys) > 1:
            logger.info(f"🔑 Multi-API-Key Mode: {len(api_keys)} keys detected")
            logger.info(f"📊 Expected throughput: ~{len(api_keys) * 10} RPM")
        elif api_keys and len(api_keys) == 1:
            logger.info("🔑 Single-API-Key Mode (consider adding more for 5x speed!)")
        else:
            logger.info("🔑 Using default API configuration")
        
        # Auto-adjust worker count based on number of keys
        if max_parallel_verifications is None:
            if api_keys and len(api_keys) > 1:
                max_parallel_verifications =len(api_keys)
            else:
                max_parallel_verifications = 4
        
        logger.info(f"⚙️ Max parallel verifications: {max_parallel_verifications}")
        
        # Initialize models for each pipeline step
        step_models = {
            "decompose_model": decompose_model,
            "checkworthy_model": checkworthy_model,
            "query_generator_model": query_generator_model,
            "evidence_retrieval_model": evidence_retrieval_model,
            "claim_verify_model": claim_verify_model,
        }
        
        for key, model_name in step_models.items():
            # Use default model if step-specific model not provided
            model_name = default_model if model_name is None else model_name
            logger.info(f"Initializing {key} with model: {model_name}")
            
            # Determine client based on model name or explicit specification
            if client is not None:
                logger.info(f"Using specified client: {client}")
                LLMClient = CLIENTS[client]
            else:
                logger.info("Auto-detecting LLM client based on model name")
                LLMClient = model2client(model_name)
            
            # Initialize the client for this step
            setattr(
                self, 
                key, 
                LLMClient(model=model_name, api_config=self.api_config)
            )
        
        # Initialize sub-modules with their respective clients
        self.decomposer = Decompose(
            llm_client=self.decompose_model, 
            prompt=self.prompt
        )
        self.checkworthy = Checkworthy(
            llm_client=self.checkworthy_model, 
            prompt=self.prompt
        )
        self.query_generator = QueryGenerator(
            llm_client=self.query_generator_model, 
            prompt=self.prompt
        )
        self.evidence_crawler = retriever_mapper(retriever_name=retriever)(
            llm_client=self.evidence_retrieval_model, 
            api_config=self.api_config
        )
        
        # Initialize ClaimVerify with multi-key support
        if api_keys and len(api_keys) > 1:
            logger.info("🚀 Initializing ClaimVerify with multi-key support...")
            
            # Create client factory for multi-key mode
            def client_factory(api_key: str):
                """Create a new LLM client with specific API key."""
                temp_config = self.api_config.copy()
                temp_config['GEMINI_API_KEY'] = api_key
                
                model_name = claim_verify_model or default_model
                if client is not None:
                    LLMClient = CLIENTS[client]
                else:
                    LLMClient = model2client(model_name)
                
                return LLMClient(model=model_name, api_config=temp_config)
            
            self.claimverify = ClaimVerify(
                llm_client=client_factory,
                prompt=self.prompt,
                api_keys=api_keys,
                max_parallel_verifications=max_parallel_verifications,
                max_requests_per_minute=10,  # Gemini 2.5 Flash free tier
                max_requests_per_day=250,    # Daily limit per key
            )
        else:
            logger.info("Initializing ClaimVerify with single-key mode...")
            self.claimverify = ClaimVerify(
                llm_client=self.claim_verify_model,
                prompt=self.prompt,
                max_parallel_verifications=max_parallel_verifications,
            )
        
        # Track sub-modules for usage reporting
        self.attr_list = [
            "decomposer", 
            "checkworthy", 
            "query_generator", 
            "evidence_crawler", 
            "claimverify"
        ]
        self.num_seed_retries = num_seed_retries
        
        logger.info("=== FactCheck Pipeline Initialized Successfully ===")

    def load_config(self, api_config: Optional[dict]) -> None:
        """
        Load API configuration from dict or config file.
        
        Args:
            api_config: API configuration dictionary
        """
        self.api_config = load_api_config(api_config)

    def check_text(self, raw_text: str) -> dict:
        """
        Main fact-checking method - processes text through entire pipeline.
        
        Pipeline steps:
        1. Decompose text into atomic claims
        2. Filter checkworthy claims
        3. Generate search queries for claims
        4. Retrieve evidence from web
        5. Verify claims against evidence (MULTI-KEY ACCELERATED!)
        
        Args:
            raw_text: Input text to fact-check
            
        Returns:
            FactCheckOutput dictionary with claims, evidence, and factuality scores
        """
        # Reset token usage counters
        self._reset_usage()
        
        start_time = time.time()
        logger.info("=== Starting Fact-Check Pipeline ===")
        
        # Step 1: Decompose text into claims
        logger.info("Step 1: Decomposing text into claims...")
        claims = self.decomposer.getclaims(
            doc=raw_text, 
            num_retries=self.num_seed_retries
        )
                
        # Steps 2-3: Run with rate-limited parallelism (single-key is sufficient here)
        logger.info("Steps 2-3: Running with rate-limited parallelism...")

     
        from factcheck.utils.rate_limiter import RateLimitedExecutor

        executor = RateLimitedExecutor(
            max_requests_per_minute=8,
            max_workers=3
        )
        logger.info("📌 Using RateLimitedExecutor for Steps 2-3 (8 RPM)")

        # Define tasks
        def task_restore():
            return self.decomposer.restore_claims(
                doc=raw_text,
                claims=claims,
                num_retries=self.num_seed_retries
            )

        def task_checkworthy():
            return self.checkworthy.identify_checkworthiness(
                claims,
                num_retries=self.num_seed_retries
            )

        def task_queries():
            return self.query_generator.generate_query(claims=claims)

        # Execute in parallel with rate limiting
        results = executor.map(
            lambda f: f(),
            [task_restore, task_checkworthy, task_queries]
        )

        claim2doc = results[0]
        checkworthy_claims, claim2checkworthy = results[1]
        claim_queries_dict = results[2]

        logger.info(f"✅ Steps 2-3 complete: {len(claims)} claims, {len(checkworthy_claims)} checkworthy")



        
        # Filter queries to only checkworthy claims
        checkworthy_claims_set = set(checkworthy_claims)
        claim_queries_dict = {
            claim: queries 
            for claim, queries in claim_queries_dict.items() 
            if claim in checkworthy_claims_set
        }
        
        # Log decomposition results
        for i, (claim, origin) in enumerate(claim2doc.items()):
            logger.info(f"Claim {i}: {claim} | Origin: {origin}")
        
        for i, claim in enumerate(checkworthy_claims):
            logger.info(f"Checkworthy Claim {i}: {claim}")
        
        # Handle case with no checkworthy claims
        if not checkworthy_claims:
            logger.info("No checkworthy claims found. Finalizing...")
            return self._finalize_factcheck(
                raw_text=raw_text, 
                claim_detail=[], 
                return_dict=True
            )
        
        # Log generated queries
        for claim, queries in claim_queries_dict.items():
            logger.info(f"Claim: {claim}")
            logger.info(f"Queries: {queries}")
        
        step123_time = time.time()
        
        # Step 4: Retrieve evidence from web
        logger.info("Step 4: Retrieving evidence from web...")
        claim_evidences_dict = self.evidence_crawler.retrieve_evidence(
            claim_queries_dict=claim_queries_dict
        )
        
        for claim, evidences in claim_evidences_dict.items():
            logger.info(f"Claim: {claim}")
            logger.info(f"Evidence count: {len(evidences)}")
        
        step4_time = time.time()
        
        # Step 5: Verify claims against evidence
        logger.info("Step 5: Verifying claims against evidence...")
        if self.api_keys and len(self.api_keys) > 1:
            logger.info(f"🚀 Using {len(self.api_keys)} API keys for parallel verification!")

        # Convert to (text, url) tuples - handle both dicts and Evidence objects
        claim_evidence_tuples = {}
        for claim, evidences in claim_evidences_dict.items():
            tuples_list = []
            for ev in evidences:
                if isinstance(ev, dict):
                    # Retriever returns dicts
                    tuples_list.append((ev.get('text', ''), ev.get('url', '')))
                else:
                    # Evidence objects (shouldn't happen with Serper but handle anyway)
                    tuples_list.append((ev.text, ev.url))
            claim_evidence_tuples[claim] = tuples_list

        claim_verifications_dict = self.claimverify.verify_claims(
            claim_evidences_dict=claim_evidence_tuples
        )


        
        for claim, verifications in claim_verifications_dict.items():
            logger.info(f"Claim: {claim} | Verifications: {len(verifications)}")
        
        step5_time = time.time()
        
        # Log timing breakdown
        verification_time = step5_time - step4_time
        verification_rate = len(claim_verifications_dict) / verification_time if verification_time > 0 else 0
        
        logger.info(
            f"=== Pipeline Complete ===\n"
            f"Total time: {step5_time - start_time:.2f}s\n"
            f"  - Claim processing: {step123_time - start_time:.2f}s\n"
            f"  - Evidence retrieval: {step4_time - step123_time:.2f}s\n"
            f"  - Verification: {verification_time:.2f}s ({verification_rate:.1f} req/s)\n"
        )
        
        # Merge all results into claim details
        claim_detail = self._merge_claim_details(
            claim2doc=claim2doc,
            claim2checkworthy=claim2checkworthy,
            claim2queries=claim_queries_dict,
            claim2evidences=claim_evidences_dict,
            claim2verifications=claim_verifications_dict,
        )
        
        return self._finalize_factcheck(
            raw_text=raw_text, 
            claim_detail=claim_detail, 
            return_dict=True
        )

    def _get_usage(self) -> PipelineUsage:
        """
        Collect token usage statistics from all sub-modules.
        
        Returns:
            PipelineUsage object with usage stats for each module
        """
        usage_dict = {}
        
        for attr in self.attr_list:
            module = getattr(self, attr)
            
            # ✅ FIX: Handle multi-key mode where llm_client is a factory function
            if hasattr(module, 'llm_client') and hasattr(module.llm_client, 'usage'):
                usage_dict[attr] = module.llm_client.usage
            else:
                # Multi-key mode or special case - create empty usage
                from factcheck.utils.data_class import TokenUsage
                usage_dict[attr] = TokenUsage()
        
        return PipelineUsage(**usage_dict)


    def _reset_usage(self) -> None:
        """Reset token usage counters for all sub-modules."""
        for attr in self.attr_list:
            module = getattr(self, attr)
            
            # ✅ FIX: Only reset if llm_client has reset_usage method
            if hasattr(module, 'llm_client') and hasattr(module.llm_client, 'reset_usage'):
                module.llm_client.reset_usage()
            # In multi-key mode, usage tracking is handled by the executor


    def _merge_claim_details(
        self,
        claim2doc: Dict[str, dict],
        claim2checkworthy: Dict[str, str],
        claim2queries: Dict[str, List[str]],
        claim2evidences: Dict[str, List],
        claim2verifications: Dict[str, List],
    ) -> List[ClaimDetail]:
        """
        Merge all claim-related information into ClaimDetail objects.
        
        Args:
            claim2doc: Maps claims to their source text locations
            claim2checkworthy: Maps claims to checkworthiness assessments
            claim2queries: Maps claims to search queries
            claim2evidences: Maps claims to retrieved evidence
            claim2verifications: Maps claims to verification results
            
        Returns:
            List of ClaimDetail objects with complete information
        """
        claim_details = []
        
        for i, (claim, origin) in enumerate(claim2doc.items()):
            if claim in claim2verifications:
                # Claim was verified - calculate factuality score
                assert claim in claim2queries, f"Claim not found in queries: {claim}"
                assert claim in claim2evidences, f"Claim not found in evidences: {claim}"
                
                evidences = claim2verifications.get(claim, {})
                labels = [e.relationship for e in evidences]
                
                # Calculate factuality: SUPPORTS / (SUPPORTS + REFUTES)
                num_supports = labels.count("SUPPORTS")
                num_refutes = labels.count("REFUTES")
                
                if num_supports + num_refutes == 0:
                    factuality = "No evidence found."
                else:
                    factuality = num_supports / (num_supports + num_refutes)
                
                claim_obj = ClaimDetail(
                    id=i,
                    claim=claim,
                    checkworthy=True,
                    checkworthy_reason=claim2checkworthy.get(
                        claim, 
                        "No reason provided"
                    ),
                    origin_text=origin["text"],
                    start=origin["start"],
                    end=origin["end"],
                    queries=claim2queries[claim],
                    evidences=evidences,
                    factuality=factuality,
                )
            else:
                # Claim was not checkworthy - skip verification
                claim_obj = ClaimDetail(
                    id=i,
                    claim=claim,
                    checkworthy=False,
                    checkworthy_reason=claim2checkworthy.get(
                        claim, 
                        "No reason provided"
                    ),
                    origin_text=origin["text"],
                    start=origin["start"],
                    end=origin["end"],
                    queries=[],
                    evidences=[],
                    factuality="Nothing to check.",
                )
            
            claim_details.append(claim_obj)
        
        return claim_details

    def _finalize_factcheck(
        self, 
        raw_text: str, 
        claim_detail: List[ClaimDetail] = None, 
        return_dict: bool = True
    ) -> Union[dict, FactCheckOutput]:
        """
        Finalize fact-check results with summary statistics.
        
        Args:
            raw_text: Original input text
            claim_detail: List of ClaimDetail objects
            return_dict: Return as dict if True, FactCheckOutput object if False
            
        Returns:
            FactCheckOutput (as dict or object)
        """
        if claim_detail is None:
            claim_detail = []
        
        # Calculate summary statistics
        verified_claims = [
            c for c in claim_detail 
            if not isinstance(c.factuality, str)
        ]
        
        num_claims = len(claim_detail)
        num_checkworthy_claims = len([
            c for c in claim_detail 
            if c.factuality != "Nothing to check."
        ])
        num_verified_claims = len(verified_claims)
        num_supported_claims = len([
            c for c in verified_claims 
            if c.factuality == 1
        ])
        num_refuted_claims = len([
            c for c in verified_claims 
            if c.factuality == 0
        ])
        num_controversial_claims = (
            num_verified_claims - num_supported_claims - num_refuted_claims
        )
        
        # Overall factuality score
        if num_verified_claims > 0:
            factuality = sum(c.factuality for c in verified_claims) / num_verified_claims
        else:
            factuality = 0.0
        
        summary = FCSummary(
            num_claims=num_claims,
            num_checkworthy_claims=num_checkworthy_claims,
            num_verified_claims=num_verified_claims,
            num_supported_claims=num_supported_claims,
            num_refuted_claims=num_refuted_claims,
            num_controversial_claims=num_controversial_claims,
            factuality=factuality,
        )
        
        num_tokens = len(raw_text) // 4
        
        output = FactCheckOutput(
            raw_text=raw_text,
            token_count=num_tokens,
            usage=self._get_usage(),
            claim_detail=claim_detail,
            summary=summary,
        )
        
        # Validate output
        if not output.attribute_check():
            raise ValueError("Output attribute validation failed")
        
        logger.info(f"=== Overall Factuality Score: {output.summary.factuality:.2f} ===")
        
        if return_dict:
            return asdict(output)
        else:
            return output