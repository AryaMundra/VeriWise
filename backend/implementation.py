

import gradio as gr
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
    """Gradio application for fact-checking with Gemini (multi-key support)."""

    def __init__(self, enable_multi_key: bool = True):
        """
        Initialize the fact-checking application.
        
        Args:
            enable_multi_key: Enable multi-API-key mode for 5x throughput
        """
        
        # Load API keys from environment or config file
        self.api_config = self._load_api_keys()
        
        # Extract multiple Gemini keys if available
        self.gemini_keys = self._extract_gemini_keys()
        
        # Determine mode
        self.multi_key_mode = enable_multi_key and len(self.gemini_keys) > 1
        
        if self.multi_key_mode:
            print(f"🚀 MULTI-KEY MODE ENABLED: {len(self.gemini_keys)} API keys detected!")
            print(f"   Expected throughput: ~{len(self.gemini_keys) * 8} RPM")
            print(f"   Keys: {[key[:20] + '...' for key in self.gemini_keys]}")
        else:
            print(f"📌 Single-key mode (8 RPM)")
            print(f"   Key: {self.gemini_keys[0][:20]}...")
        
        # Initialize FactCheck
        self.factcheck = FactCheck(
            default_model="gemini-2.5-flash",
            prompt="gemini_prompt",
            retriever="serper",
            api_config=self.api_config,
            api_keys=self.gemini_keys,
            num_seed_retries=1,
        )
        
        # Enable multi-key mode in ClaimVerify if available
        if self.multi_key_mode and hasattr(self.factcheck.claimverify, 'enable_multi_key'):
            self.factcheck.claimverify.enable_multi_key(
                api_keys=self.gemini_keys,
                llm_client_factory=self._create_gemini_client
            )
            print("✅ Multi-key mode activated in ClaimVerify")
        
        print("✅ FactCheck pipeline initialized")

    def _load_api_keys(self) -> dict:
        """Load API keys from environment or config file."""
        # Try environment variables first
        api_config = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "GEMINI_API_KEY_2": os.getenv("GEMINI_API_KEY_2"),
            "GEMINI_API_KEY_3": os.getenv("GEMINI_API_KEY_3"),
            "GEMINI_API_KEY_4": os.getenv("GEMINI_API_KEY_4"),
            "GEMINI_API_KEY_5": os.getenv("GEMINI_API_KEY_5"),
            "GEMINI_API_KEY_MEDIA": os.getenv("GEMINI_API_KEY_MEDIA"),
            "SERPER_API_KEY": os.getenv("SERPER_API_KEY"),
        }
        
        # If not in environment, try loading from file
        if not api_config.get("GEMINI_API_KEY"):
            try:
                api_config = load_api_config("factcheck/config/api_config.yaml")
            except:
                pass
        
        # Validate at least one Gemini key exists
        if not api_config.get("GEMINI_API_KEY"):
            raise ValueError(
                "GEMINI_API_KEY not found! Set it as:\n"
                "  Environment variable: $env:GEMINI_API_KEY='your_key'\n"
                "  Or in: factcheck/config/api_config.yaml"
            )
        
        return api_config

    def _extract_gemini_keys(self) -> List[str]:
        """Extract all available Gemini API keys."""
        keys = []
        
        # Primary key
        if self.api_config.get("GEMINI_API_KEY"):
            keys.append(self.api_config["GEMINI_API_KEY"])
        
        # Additional keys
        for i in range(2, 10):  # Support up to 9 keys
            key_name = f"GEMINI_API_KEY_{i}"
            if self.api_config.get(key_name):
                keys.append(self.api_config[key_name])
        
        return keys

    def _create_gemini_client(self, api_key: str):
        """Factory function to create Gemini client with specific API key."""
        from factcheck.utils.llmclient.gemini import GeminiClient
        
        return GeminiClient(
            model="gemini-2.5-flash",
            api_config={"GEMINI_API_KEY": api_key},
            max_requests_per_minute=10,  # Per-key limit
        )

    def get_factuality_color(self, score: float) -> str:
        """Get color based on factuality score."""
        if score >= 0.8:
            return "#4CAF50"  # Green
        elif score >= 0.6:
            return "#8BC34A"  # Light green
        elif score >= 0.4:
            return "#FFC107"  # Amber
        elif score >= 0.2:
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red

    def get_relationship_badge(self, relationship: str) -> str:
        """Get colored badge HTML for relationship."""
        colors = {
            "SUPPORTS": "#4CAF50",
            "REFUTES": "#F44336",
            "IRRELEVANT": "#9E9E9E",
        }
        color = colors.get(relationship, "#9E9E9E")
        return (
            f'<span style="'
            f'background: {color}; color: white; '
            f'padding: 4px 12px; border-radius: 12px; '
            f'font-size: 12px; font-weight: 600; '
            f'text-transform: uppercase;">'
            f'{relationship}</span>'
        )
    def format_results_html(self, results: Dict) -> Tuple[str, str, str]:
        """Format fact-check results into beautiful HTML."""
        summary = results.get("summary", {})
        claims = results.get("claim_detail", [])

        # Overall factuality score
        factuality = summary.get("factuality", 0)
        color = self.get_factuality_color(factuality)

        # Summary HTML with enhanced statistics
        summary_html = f"""
        <div style="padding: 30px; background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                    border-radius: 16px; border-left: 6px solid {color}; margin-bottom: 20px;">
            <h2 style="margin: 0 0 20px 0; color: {color}; font-size: 32px;">
                📊 Factuality Score: {factuality:.1%}
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                        gap: 15px; margin-top: 20px;">
                <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #666;">
                        {summary.get("num_claims", 0)}
                    </div>
                    <div style="font-size: 12px; color: #999; text-transform: uppercase;">
                        Total Claims
                    </div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #4CAF50;">
                        {summary.get("num_supported_claims", 0)}
                    </div>
                    <div style="font-size: 12px; color: #999; text-transform: uppercase;">
                        Supported
                    </div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #F44336;">
                        {summary.get("num_refuted_claims", 0)}
                    </div>
                    <div style="font-size: 12px; color: #999; text-transform: uppercase;">
                        Refuted
                    </div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #FFC107;">
                        {summary.get("num_controversial_claims", 0)}
                    </div>
                    <div style="font-size: 12px; color: #999; text-transform: uppercase;">
                        Mixed Evidence
                    </div>
                </div>
            </div>
        </div>
        """

        # Claims HTML with detailed breakdowns
        claims_html = ""
        for i, claim in enumerate(claims, 1):
            # Skip non-checkworthy claims for cleaner display
            if not claim.get("checkworthy", True):
                continue

            claim_text = claim.get("claim", "")
            factuality_score = claim.get("factuality", 0)
            
            # Handle string factuality (like "Nothing to check.")
            if isinstance(factuality_score, str):
                score_color = "#9E9E9E"
                score_text = factuality_score
            else:
                score_color = self.get_factuality_color(factuality_score)
                score_text = f"{factuality_score:.1%}"

            claims_html += f"""
            <div style="background: white; padding: 20px; border-radius: 12px; 
                        margin-bottom: 20px; border-left: 4px solid {score_color}; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                    <div style="flex: 1;">
                        <div style="font-size: 14px; color: #999; margin-bottom: 5px;">
                            Claim #{i}
                        </div>
                        <div style="font-size: 18px; font-weight: 600; color: #333; line-height: 1.5;">
                            {claim_text}
                        </div>
                    </div>
                    <div style="text-align: right; margin-left: 20px;">
                        <div style="font-size: 24px; font-weight: bold; color: {score_color};">
                            {score_text}
                        </div>
                        <div style="font-size: 12px; color: #999;">
                            Factuality
                        </div>
                    </div>
                </div>
            """

            # Origin text
            origin_text = claim.get("origin_text", "")
            if origin_text:
                claims_html += f"""
                <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; 
                            margin-bottom: 15px; font-style: italic; color: #666;">
                    <strong>Origin:</strong> "{origin_text}"
                </div>
                """

            # Evidence section
            evidences = claim.get("evidences", [])
            if evidences:
                claims_html += '<div style="margin-top: 15px;">'
                claims_html += '<div style="font-weight: 600; margin-bottom: 10px; color: #666;">📚 Evidence:</div>'
                
                for j, evidence in enumerate(evidences, 1):
                    relationship = evidence.get("relationship", "IRRELEVANT")
                    reasoning = evidence.get("reasoning", "No reasoning provided")
                    url = evidence.get("url", "#")
                    source = evidence.get("source", "Unknown source")
                    
                    badge = self.get_relationship_badge(relationship)
                    
                    claims_html += f"""
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                                margin-bottom: 10px; border-left: 3px solid {self.get_factuality_color(1 if relationship == "SUPPORTS" else 0)};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: 600; font-size: 14px;">Evidence #{j}</span>
                            {badge}
                        </div>
                        <div style="font-size: 14px; color: #555; margin-bottom: 8px; line-height: 1.6;">
                            {reasoning}
                        </div>
                        <div style="font-size: 12px; color: #999;">
                            🔗 <a href="{url}" target="_blank" style="color: #2196F3; text-decoration: none;">
                                {source}
                            </a>
                        </div>
                    </div>
                    """
                
                claims_html += '</div>'

            claims_html += "</div>"

        if not claims_html:
            claims_html = """
            <div style="padding: 40px; text-align: center; color: #999;">
                <h3>No checkworthy claims found</h3>
                <p>The provided text doesn't contain any factual claims that can be verified.</p>
            </div>
            """

        # Raw data JSON
        details_html = f"""
        <div style="background: #1e1e1e; padding: 20px; border-radius: 8px; overflow: auto;">
            <pre style="color: #d4d4d4; margin: 0; font-family: 'Courier New', monospace; font-size: 13px;">
{json.dumps(results, indent=2)}
            </pre>
        </div>
        """

        return summary_html, claims_html, details_html

    def process_input(
        self,
        input_text: str,
        text_file,
        audio_file,
        image_file,
        video_file,
        model: str,
        progress=gr.Progress(),
    ) -> Tuple[str, str, str]:
        """Process input and return fact-check results."""
        try:
            progress(0, desc="Initializing...")

            # Determine input type and get content
            content = None
            modal = "text"
            input_path = None

            if text_file is not None:
                input_path = text_file.name
                with open(input_path, "r", encoding="utf-8") as f:
                    content = f.read()
                modal = "text"
            elif audio_file is not None:
                input_path = audio_file.name
                modal = "speech"
            elif image_file is not None:
                input_path = image_file.name
                modal = "image"
            elif video_file is not None:
                input_path = video_file.name
                modal = "video"
            else:
                return (
                    '<div style="padding: 20px; background: #ffebee; border-radius: 8px; color: #c62828;">'
                    "❌ Please provide input (text, file, audio, image, or video)"
                    "</div>",
                    "",
                    "",
                )
            if input_text is not None:
                content=input_text

            # Normalize multimodal input to text
            if modal in ["speech", "image", "video"]:
                progress(0.2, desc=f"Converting {modal} to text...")
                
                api_key = self.api_config.get("GEMINI_API_KEY_MEDIA")
                if not api_key:
                    return (
                        '<div style="padding: 20px; background: #ffebee; border-radius: 8px;">'
                        "❌ GEMINI_API_KEY not found in config"
                        "</div>",
                        "",
                        "",
                    )

                content_media = modal_normalization(
                    modal=modal, input_data=input_path, gemini_key=api_key
                )
            else:
                content_media=" "

            progress(0.3, desc="Initializing fact-checker...")

            # Run fact-checking (with rate-limited parallelism)
            progress(0.4, desc="Analyzing claims (this may take 1-2 minutes)...")
            
            start_time = time.time()
            results = self.factcheck.check_text(content+content_media)
            
            elapsed = time.time() - start_time
            
            print(f"✅ Fact-checking completed in {elapsed:.2f}s")

            progress(0.9, desc="Formatting results...")

            # Format results
            summary_html, claims_html, details_html = self.format_results_html(results)

            progress(1.0, desc="Complete!")

            return summary_html, claims_html, details_html

        except Exception as e:
            import traceback
            
            error_html = f"""
            <div style="padding: 20px; background: #ffebee; border-radius: 8px; 
                        border-left: 4px solid #f44336;">
                <h3 style="color: #c62828; margin-top: 0;">❌ Error</h3>
                <p style="color: #d32f2f; font-weight: 600;">{str(e)}</p>
                <details style="margin-top: 15px;">
                    <summary style="cursor: pointer; color: #d32f2f; font-weight: 600;">
                        View Full Traceback
                    </summary>
                    <pre style="background: #fff; padding: 15px; border-radius: 4px; 
                               overflow: auto; font-size: 12px; margin-top: 10px;">
{traceback.format_exc()}
                    </pre>
                </details>
            </div>
            """
            return error_html, "", ""


def create_interface():
    """Create and configure the Gradio interface."""
    
    # Initialize app
    try:
        app = FactCheckApp()
    except ValueError as e:
        print(f"❌ Initialization failed: {e}")
        raise

    # Custom CSS
    custom_css = """
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        max-width: 1400px !important;
    }
    .gr-button-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        font-weight: 600 !important;
        transition: transform 0.2s !important;
    }
    .gr-button-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3) !important;
    }
    """

    # Create interface
    with gr.Blocks(css=custom_css, theme=gr.themes.Soft(), title="OpenFactVerification") as demo:
        gr.Markdown(
            """
            # 🔍 OpenFactVerification with Gemini
            
            **Advanced AI-powered fact-checking** using Google Gemini 2.5 Flash with rate-limited parallelism.
            Supports text, audio, images, and video input.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Input")
                
                # Input options
                input_text = gr.Textbox(
                    label="Text Input",
                    placeholder="Enter text to fact-check...",
                    lines=6,
                )
                
                with gr.Accordion("📁 Or Upload Files", open=False):
                    text_file = gr.File(label="Text File (.txt, .md)", file_types=[".txt", ".md"])
                    audio_file = gr.File(label="Audio File", file_types=[".mp3", ".wav", ".m4a"])
                    image_file = gr.File(label="Image File", file_types=[".jpg", ".jpeg", ".png"])
                    video_file = gr.File(label="Video File", file_types=[".mp4", ".avi", ".mov"])
                
                # Model selection
                model = gr.Dropdown(
                    choices=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
                    value="gemini-2.5-flash",
                    label="Model Selection",
                )
                
                # Submit button
                check_btn = gr.Button("🚀 Fact-Check", variant="primary", size="lg")
                
                gr.Markdown(
                    """
                    **⚡ Performance:**
                    - ~1-2 minutes for short text (2-3 claims)
                    - Rate-limited parallelism: 8 RPM with safety margin
                    - Automatic retry on failures
                    """
                )

            with gr.Column(scale=2):
                gr.Markdown("### 📊 Results")
                
                with gr.Tabs():
                    with gr.Tab("Summary"):
                        summary_output = gr.HTML(
                            value='<div style="padding: 40px; text-align: center; color: #999;">Results will appear here after fact-checking...</div>'
                        )
                    
                    with gr.Tab("Claims Analysis"):
                        claims_output = gr.HTML()
                    
                    with gr.Tab("Raw Data"):
                        details_output = gr.HTML()

        # Event handler
        check_btn.click(
            fn=app.process_input,
            inputs=[input_text, text_file, audio_file, image_file, video_file, model],
            outputs=[summary_output, claims_output, details_output],
        )

        gr.Markdown(
            """
            ---
            ### 📚 About
            
            **OpenFactVerification** uses advanced AI to verify claims by:
            1. **Decomposing** text into atomic claims
            2. **Filtering** checkworthy claims
            3. **Generating** search queries
            4. **Retrieving** evidence from the web (Serper)
            5. **Verifying** claims with Gemini 2.5 Flash
            
            **Rate Limiting:** Automatic 8 RPM with 3-worker parallelism for optimal speed/quota balance.
            
            Powered by **Google Gemini 2.5 Flash** | Built with **Gradio**
            
            [GitHub](https://github.com/Libr-AI/OpenFactVerification) | [Documentation](https://openfactverification.com)
            """
        )

    return demo


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting OpenFactVerification with Gemini 2.5 Flash")
    print("=" * 60 + "\n")
    
    demo = create_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        inbrowser=True,  # Auto-open browser
    )
