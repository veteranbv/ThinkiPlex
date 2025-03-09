"""
Service for generating AI summaries using Claude.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from anthropic import Anthropic, APIConnectionError, APIError, AuthenticationError

from ...utils.config import Config
from ...utils.exceptions import AIProcessingError, ConfigError
from ...utils.logging import get_logger

logger = get_logger()


def chunk_text(text: str, max_tokens: int) -> List[str]:
    """
    Split text into chunks that don't exceed the specified token limit.

    Args:
        text: The text to be chunked
        max_tokens: Maximum number of tokens per chunk

    Returns:
        List of text chunks
    """
    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        tokens = encoding.encode(text)
        chunks = []
        current_chunk = []
        current_chunk_tokens = 0

        for token in tokens:
            if current_chunk_tokens + 1 <= max_tokens:
                current_chunk.append(token)
                current_chunk_tokens += 1
            else:
                chunks.append(encoding.decode(current_chunk))
                current_chunk = [token]
                current_chunk_tokens = 1

        if current_chunk:
            chunks.append(encoding.decode(current_chunk))

        return chunks
    except ImportError:
        # If tiktoken is not available, use a simpler approach
        logger.warning("tiktoken not available, using a simpler chunking method")
        # Split by paragraphs (approximately 100 tokens per paragraph)
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0

        # Rough estimate: 4 characters per token
        tokens_per_char = 0.25
        max_chars = max_tokens / tokens_per_char

        for para in paragraphs:
            para_tokens = int(len(para) * tokens_per_char)
            if current_length + para_tokens <= max_tokens:
                current_chunk.append(para)
                current_length += para_tokens
            else:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_length = para_tokens

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks


def merge_summaries(summaries: List[str]) -> str:
    """
    Merge multiple summaries into a single text.

    Args:
        summaries: List of summary texts

    Returns:
        Merged summary text
    """
    return "\n\n".join(summaries)


class ClaudeService:
    """Service for interacting with the Anthropic Claude API."""

    def __init__(self) -> None:
        """
        Initialize the Claude service.

        Raises:
            AIProcessingError: If the Anthropic API key is not set.
            ConfigError: If there are issues with the Claude model configuration.
        """
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise AIProcessingError(
                "Anthropic API key is not set in environment variables. Please set ANTHROPIC_API_KEY."
            )

        self.config = Config()
        self.client = Anthropic(api_key=self.api_key)

        # Get models configuration
        self.models_config = self.config.get("claude.models", {})
        if not self.models_config:
            logger.warning("No Claude models found in configuration. Using default values.")
            self.models_config = {
                "claude-3-7-sonnet-latest": {
                    "name": "Claude 3.7 Sonnet",
                    "context_window": 200000,
                    "max_output_tokens": 8192,
                    "is_default": True,
                }
            }

        # Validate model configuration and find default model
        self.default_model = self._get_default_model()
        self.model = self.default_model
        self.token_limit = self.get_model_token_limit(self.model)
        self.max_output_tokens = self.get_model_output_limit(self.model)

        # Load prompt configurations
        self.prompts_config = self.config.get("claude.prompts", {})
        self.prompt_source = self.prompts_config.get("use_source", "default")
        self.default_prompt_type = self.prompts_config.get("default_type", "transcribe")

        logger.info(f"Claude service initialized with model: {self.model}")

    def _get_default_model(self) -> str:
        """
        Get the default model from configuration.

        Returns:
            The default model name

        Raises:
            ConfigError: If multiple models are set as default or no default model is found
        """
        default_models = []

        for model_id, model_config in self.models_config.items():
            if model_config.get("is_default", False):
                default_models.append(model_id)

        if len(default_models) > 1:
            error_msg = f"Multiple default Claude models found in configuration: {default_models}. Only one model should be set as default."
            logger.error(error_msg)
            raise ConfigError(error_msg)

        if not default_models:
            # If no default model is specified, use the first one
            if self.models_config:
                default_model = next(iter(self.models_config.keys()))
                logger.warning(
                    f"No default Claude model specified in configuration. Using {default_model} as default."
                )
                return str(default_model)
            else:
                error_msg = "No Claude models found in configuration."
                logger.error(error_msg)
                raise ConfigError(error_msg)

        return str(default_models[0])

    def set_model(self, model: str) -> None:
        """
        Set the Claude model to use.

        Args:
            model: The name of the Claude model

        Raises:
            ConfigError: If the specified model is not found in configuration
        """
        if model not in self.models_config:
            error_msg = f"Model '{model}' not found in configuration. Available models: {list(self.models_config.keys())}"
            logger.error(error_msg)
            raise ConfigError(error_msg)

        self.model = model
        self.token_limit = self.get_model_token_limit(model)
        self.max_output_tokens = self.get_model_output_limit(model)
        logger.info(f"Claude model set to: {model}")

    def get_model_token_limit(self, model: str) -> int:
        """
        Get the token limit for a given model from the configuration.

        Args:
            model: The name of the model

        Returns:
            The token limit for the model
        """
        # Try to get from config
        model_config = self.models_config.get(model, {})
        if "context_window" in model_config:
            return int(model_config["context_window"])

        # Fallback to hardcoded values if not in config
        token_limits = {
            "claude-3-7-sonnet-latest": 200000,
            "claude-3-5-sonnet-latest": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
        }
        return token_limits.get(model, 100000)  # Default to 100k

    def get_model_output_limit(self, model: str) -> int:
        """
        Get the output token limit for a given model from the configuration.

        Args:
            model: The name of the model

        Returns:
            The output token limit for the model
        """
        # Try to get from config
        model_config = self.models_config.get(model, {})
        if "max_output_tokens" in model_config:
            return int(model_config["max_output_tokens"])

        # Fallback to hardcoded values if not in config
        output_limits = {
            "claude-3-7-sonnet-latest": 8192,
            "claude-3-5-sonnet-latest": 8192,
            "claude-3-opus-20240229": 4096,
            "claude-3-haiku-20240307": 4096,
        }
        return output_limits.get(model, 4096)  # Default to 4096

    def get_available_models(self) -> List[str]:
        """
        Get a list of available Claude models from the configuration.

        Returns:
            List of available model names
        """
        return list(self.models_config.keys())

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.

        Args:
            model: The name of the model

        Returns:
            Dictionary with model information
        """
        model_info = self.models_config.get(model, {})
        if not model_info:
            return {}
        return dict(model_info)

    def get_prompt(self, prompt_type: Optional[str] = None) -> str:
        """
        Get a prompt based on the specified type and source.

        Args:
            prompt_type: The type of prompt to get (e.g., 'summarize', 'transcribe', 'analyze')
                         If None, uses the default prompt type from config

        Returns:
            The prompt text

        Raises:
            ConfigError: If the prompt cannot be found or loaded
        """
        if prompt_type is None:
            prompt_type = self.default_prompt_type

        # Determine source (default or file)
        source = self.prompt_source

        if source == "default":
            return self._get_default_prompt(str(prompt_type))
        elif source == "file":
            return self._get_file_prompt(str(prompt_type))
        else:
            error_msg = f"Invalid prompt source '{source}'. Must be 'default' or 'file'."
            logger.error(error_msg)
            raise ConfigError(error_msg)

    def _get_default_prompt(self, prompt_type: str) -> str:
        """
        Get a prompt from the default prompts in the config.

        Args:
            prompt_type: The type of prompt to get

        Returns:
            The prompt text

        Raises:
            ConfigError: If the prompt type is not found in the defaults
        """
        defaults = self.prompts_config.get("defaults", {})
        if prompt_type not in defaults:
            error_msg = f"Prompt type '{prompt_type}' not found in default prompts. Available types: {list(defaults.keys())}"
            logger.error(error_msg)
            raise ConfigError(error_msg)

        prompt = defaults[prompt_type]
        return str(prompt) if prompt is not None else ""

    def _get_file_prompt(self, prompt_type: str) -> str:
        """
        Get a prompt from a file.

        Args:
            prompt_type: The type of prompt to get

        Returns:
            The prompt text

        Raises:
            ConfigError: If the prompt file cannot be found or read
        """
        file_paths = self.prompts_config.get("files", {})
        if prompt_type not in file_paths:
            error_msg = f"Prompt type '{prompt_type}' not found in prompt files. Available types: {list(file_paths.keys())}"
            logger.error(error_msg)
            raise ConfigError(error_msg)

        file_path = file_paths[prompt_type]
        config_dir = Path(self.config.config_file).parent
        full_path = config_dir / file_path

        try:
            if not full_path.exists():
                error_msg = f"Prompt file not found: {full_path}"
                logger.error(error_msg)
                raise ConfigError(error_msg)

            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            error_msg = f"Error reading prompt file '{full_path}': {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg)

    def chunk_and_summarize(self, text: str, prompt_type: Optional[str] = None) -> str:
        """
        Split text into chunks if needed, summarize each chunk, and combine the results.

        Args:
            text: The input text to summarize
            prompt_type: The type of prompt to use (e.g., 'summarize', 'transcribe', 'analyze')
                         If None, uses the default prompt type from config

        Returns:
            The summary text

        Raises:
            AIProcessingError: If there's an error during processing
        """
        try:
            # Get the appropriate prompt
            prompt = self.get_prompt(prompt_type)

            # Calculate safe token limit
            # Reserve space for the prompt and the response
            safe_token_limit = self.token_limit - len(prompt) - self.max_output_tokens - 500

            # Split into chunks if needed
            chunks = chunk_text(text, safe_token_limit)

            if len(chunks) == 1:
                # Simple case: text fits in one chunk
                return self.process_text(
                    f"{prompt}\n\nHere is the content to analyze:\n\n{chunks[0]}"
                )

            # Process each chunk separately
            summaries = []
            for i, chunk in enumerate(chunks):
                chunk_prompt = f"{prompt}\n\nThis is part {i + 1} of {len(chunks)} of the content to analyze. Please provide a partial analysis for this section:\n\n{chunk}"
                summary = self.process_text(chunk_prompt)
                summaries.append(summary)

            # Merge the summaries
            merged_summary = merge_summaries(summaries)

            # Process the combined summary
            final_prompt = f"{prompt}\n\nThe original content was split into {len(chunks)} parts due to length. Below are the summaries of each part. Please provide a cohesive final summary that brings everything together:\n\n{merged_summary}"
            return self.process_text(final_prompt)

        except Exception as e:
            logger.error(f"Error in chunk_and_summarize: {str(e)}")
            raise AIProcessingError(f"Error processing text with Claude: {str(e)}")

    def process_text(self, prompt: str) -> str:
        """
        Process text using the Claude API.

        Args:
            prompt: The prompt for Claude

        Returns:
            Claude's response as a string

        Raises:
            AIProcessingError: If there's an error during processing
        """
        try:
            logger.info(f"Processing text with Claude model: {self.model}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_output_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            logger.info(f"Text processed successfully with Claude using model {self.model}")
            return str(response.content[0].text)

        except AuthenticationError as e:
            logger.error(f"Authentication error with Claude API: {str(e)}")
            raise AIProcessingError(f"Authentication error with Claude API: {str(e)}")
        except APIConnectionError as e:
            logger.error(f"Connection error with Claude API: {str(e)}")
            raise AIProcessingError(f"Connection error with Claude API: {str(e)}")
        except APIError as e:
            logger.error(f"API error with Claude API: {str(e)}")
            raise AIProcessingError(f"API error with Claude API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error with Claude API: {str(e)}")
            raise AIProcessingError(f"Unexpected error with Claude API: {str(e)}")
