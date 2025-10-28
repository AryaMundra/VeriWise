import json
import time
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv

# Import fact-checking components
from factcheck import FactCheck
from factcheck.utils.multimodal import modal_normalization
from factcheck.utils.api_config import load_api_config

# Load environment variables
load_dotenv()


class FactCheckApp:
    """Fact-checking application (headless version, no Gradio)."""

    def __init__(self, enable_multi_key: bool = True):
        # Load API keys
        self.api_config = self._load_api_keys()
        self.gemini_keys = self._extract_gemini_keys()
        self.multi_key_mode = enable_multi_key and len(self.gemini_keys) > 1

        # Initialize FactCheck
        self.factcheck = FactCheck(
            default_model="gemini-2.5-flash",
            prompt="gemini_prompt",
            retriever="serper",
            api_config=self.api_config,
            api_keys=self.gemini_keys,
            num_seed_retries=1,
        )

        if self.multi_key_mode and hasattr(self.factcheck.claimverify, 'enable_multi_key'):
            self.factcheck.claimverify.enable_multi_key(
                api_keys=self.gemini_keys,
                llm_client_factory=self._create_gemini_client
            )

    def _load_api_keys(self) -> dict:
        """Load API keys from env or config file."""
        api_config = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "GEMINI_API_KEY_2": os.getenv("GEMINI_API_KEY_2"),
            "GEMINI_API_KEY_3": os.getenv("GEMINI_API_KEY_3"),
            "GEMINI_API_KEY_4": os.getenv("GEMINI_API_KEY_4"),
            "GEMINI_API_KEY_5": os.getenv("GEMINI_API_KEY_5"),
            "GEMINI_API_KEY_MEDIA": os.getenv("GEMINI_API_KEY_MEDIA"),
            "SERPER_API_KEY": os.getenv("SERPER_API_KEY"),
        }

        if not api_config.get("GEMINI_API_KEY"):
            try:
                api_config = load_api_config("factcheck/config/api_config.yaml")
            except:
                pass

        if not api_config.get("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY not found! Set in .env or api_config.yaml")
        return api_config

    def _extract_gemini_keys(self) -> List[str]:
        keys = []
        if self.api_config.get("GEMINI_API_KEY"):
            keys.append(self.api_config["GEMINI_API_KEY"])
        for i in range(2, 10):
            key_name = f"GEMINI_API_KEY_{i}"
            if self.api_config.get(key_name):
                keys.append(self.api_config[key_name])
        return keys

    def _create_gemini_client(self, api_key: str):
        from factcheck.utils.llmclient.gemini import GeminiClient
        return GeminiClient(
            model="gemini-2.5-flash",
            api_config={"GEMINI_API_KEY": api_key},
            max_requests_per_minute=10,
        )

    def process_input(
        self,
        input_text: Optional[str] = None,
        text_file: Optional[str] = None,
        audio_file: Optional[str] = None,
        image_file: Optional[str] = None,
        video_file: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ) -> Dict:
        """Process input and return fact-check results."""
        try:

            # Determine input type
            content = ""
            modal = "text"
            input_path = None

            if text_file:
                with open(text_file, "r", encoding="utf-8") as f:
                    content = f.read()
                modal = "text"
            elif audio_file:
                input_path = audio_file
                modal = "speech"
            elif image_file:
                input_path = image_file
                modal = "image"
            elif video_file:
                input_path = video_file
                modal = "video"
            if input_text:
                content = input_text
            else:
                raise ValueError("No input provided.")

            if modal in ["speech", "image", "video"]:
                print(f"🎥 Converting {modal} to text...")
                api_key = self.api_config.get("GEMINI_API_KEY_MEDIA")
                if not api_key:
                    raise ValueError("Missing GEMINI_API_KEY_MEDIA for media processing.")
                content_media = modal_normalization(
                    modal=modal, input_data=input_path, gemini_key=api_key
                )
                if"No Text" in content_media:
                    content_media=""
            else:
                content_media = ""


            start_time = time.time()
            if((content+content_media)==""or (content+content_media)==" "):
                return {}
            results = self.factcheck.check_text(content + content_media)
            elapsed = time.time() - start_time

            return results

        except Exception as e:
            import traceback
            print("Error during processing:", e)
            print(traceback.format_exc())
            return {"error": str(e)}

