
import json
import argparse
from typing import Optional

from factcheck.utils.llmclient import CLIENTS
from factcheck.utils.multimodal import modal_normalization
from factcheck.utils.utils import load_yaml
from factcheck.utils.logger import CustomLogger
from factcheck import FactCheck

logger = CustomLogger(__name__).getlog()


def check(args):
    """
    Run fact-checking pipeline on input.

    Args:
        args: Command-line arguments containing:
            - model: LLM model name (e.g., "gemini-2.5-flash", "gpt-4o")
            - client: Specific client to use (optional, auto-detected)
            - modal: Input type ("string", "text", "speech", "image", "video")
            - input: Input content or path to file
            - prompt: Prompt template set to use
            - retriever: Evidence retrieval method
            - api_config: Path to API config YAML file
    """
    # Load API configuration from YAML file
    logger.info(f"Loading API config from: {args.api_config}")
    try:
        api_config = load_yaml(args.api_config)
    except FileNotFoundError:
        logger.warning(f"API config file not found: {args.api_config}")
        logger.info("Using empty config - make sure API keys are in environment variables")
        api_config = {}
    except Exception as e:
        logger.error(f"Error loading API config: {e}")
        api_config = {}

    # Initialize FactCheck pipeline
    logger.info(f"Initializing FactCheck with model: {args.model}")
    factcheck = FactCheck(
        default_model=args.model,
        client=args.client,
        api_config=api_config,
        prompt=args.prompt,
        retriever=args.retriever,
    )

    # Process input based on modality
    logger.info(f"Processing input with modal type: {args.modal}")
    
    # Get API key based on model type
    api_key = None
    if "gemini" in args.model.lower():
        api_key = api_config.get("GEMINI_API_KEY")
    elif "gpt" in args.model.lower() or "openai" in args.model.lower():
        api_key = api_config.get("OPENAI_API_KEY")
    
    # Normalize input to text
    content = modal_normalization(
        modal=args.modal,
        input_data=args.input,
        gemini_key=api_key,  # Updated parameter name
    )
    
    logger.info(f"Input normalized. Content length: {len(content)} characters")

    # Run fact-checking
    logger.info("Starting fact-check pipeline...")
    res = factcheck.check_text(content)
    
    # Print results as formatted JSON
    print("\n" + "="*80)
    print("FACT-CHECK RESULTS:")
    print("="*80)
    print(json.dumps(res, indent=4))
    print("="*80)

    # Optional: Save results to Lark (for internal testing)
    try:
        from backend.factcheck import lark
        lark.save_json_to_lark_by_level(res)
        logger.info("Results saved to Lark")
    except ImportError:
        pass  # Lark integration not available
    except Exception as e:
        logger.warning(f"Failed to save to Lark: {e}")


def main():
    """Parse arguments and run fact-checking."""
    parser = argparse.ArgumentParser(
        description="OpenFactVerification - Fact-check claims using LLMs and web evidence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check a string with Gemini (default):
  python -m factcheck --modal string --input "The Earth is flat."
  
  # Check a text file with Gemini Pro:
  python -m factcheck --model gemini-2.5-pro --modal text --input file.txt
  
  # Check audio transcription:
  python -m factcheck --modal speech --input audio.mp3
  
  # Check with OpenAI:
  python -m factcheck --model gpt-4o --prompt chatgpt_prompt --input "claim"
        """
    )
    
    # Model and client configuration
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",  # Changed default
        help="LLM model name (default: gemini-2.5-flash). Options: gemini-2.5-flash, gemini-2.5-pro, gpt-4o, gpt-4-turbo"
    )
    parser.add_argument(
        "--client",
        type=str,
        default=None,
        choices=list(CLIENTS.keys()),
        help="Specific LLM client to use (auto-detected if not specified)"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="gemini_prompt",  # Changed default
        help="Prompt template set (default: gemini_prompt). Options: gemini_prompt, chatgpt_prompt, claude_prompt"
    )
    
    # Evidence retrieval
    parser.add_argument(
        "--retriever",
        type=str,
        default="serper",
        help="Evidence retrieval method (default: serper). Options: serper, google"
    )
    
    # Input configuration
    parser.add_argument(
        "--modal",
        type=str,
        default="string",  # Changed from "text" to be more intuitive
        choices=["string", "text", "speech", "image", "video"],
        help="Input modality type (default: string)"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,  # Made required for clarity
        help="Input content (for 'string' modal) or path to file (for other modals)"
    )
    
    # Configuration
    parser.add_argument(
        "--api_config",
        type=str,
        default="factcheck/config/api_config.yaml",
        help="Path to API configuration YAML file (default: factcheck/config/api_config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Run fact-checking
    check(args)


if __name__ == "__main__":
    main()
