"""
EasySwitch - Main client for unified mobile money API integration
"""
import asyncio
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional, Union

from easyswitch.adapters import AdaptersRegistry, BaseAdapter
from easyswitch.conf import RootConfig
from easyswitch.conf.manager import ConfigManager
from easyswitch.exceptions import (
    AuthenticationError, ConfigurationError,
    InvalidProviderError
)
from easyswitch.types import (
    Currency, CustomerInfo, PaymentResponse,
    Provider, TransactionStatus,TransactionDetail,
    WebhookEvent
)
from easyswitch.integrators import load_adapter


####
##      EASY SWITCH CLIENT
#####
class EasySwitch:
    """
    Main client for EasySwitch SDK with flexible configuration options.

    Examples:
        >>> # From environment variables
        >>> client = EasySwitch.from_env()
        
        >>> # From JSON file
        >>> client = EasySwitch.from_json("config.json")
        
        >>> # From multiple sources
        >>> client = EasySwitch.from_multi_sources(
        ...     env_file=".env",
        ...     json_file="fallback.json"
        ... )
    """
    
    def __init__(self, config: RootConfig):
        """
        Initialize the EasySwitch client with validated configuration.
        
        Args:
            config: Validated configuration object
        """
        self.config = config
        self._integrators: Dict[Provider, BaseAdapter] = {}
        self._initialize_integrators()

    @classmethod
    def from_config(cls, config: RootConfig) -> 'EasySwitch':
        """Create client from existing RootConfig"""
        return cls(config)

    @classmethod
    def from_env(
        cls,
        env_file: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> 'EasySwitch':
        """
        Create client from environment variables.
        
        Args:
            env_file: Path to .env file (optional)
            **kwargs: Additional arguments for ConfigManager
        """
        manager = ConfigManager.from_env(env_file, **kwargs)
        return cls(manager.load().get_config())
    
    @classmethod
    def from_dict(
        cls,
        config_dict: Dict[str, Any],
        **kwargs
    ) -> 'EasySwitch':
        """
        Create client from Python dictionary.
        
        Args:
            config_dict: Configuration dictionary
            **kwargs: Additional arguments for ConfigManager
        """
        manager = ConfigManager.from_dict(config_dict, **kwargs)
        return cls(manager.load().get_config())
    
    @classmethod
    def from_json(
        cls,
        json_file: Union[str, Path],
        **kwargs
    ) -> 'EasySwitch':
        """
        Create client from JSON file.
        
        Args:
            json_file: Path to JSON configuration file
            **kwargs: Additional arguments for ConfigManager
        """
        manager = ConfigManager.from_json(json_file, **kwargs)
        return cls(manager.load().get_config())
    
    @classmethod
    def from_yaml(
        cls,
        yaml_file: Union[str, Path],
        **kwargs
    ) -> 'EasySwitch':
        """
        Create client from YAML file.
        
        Args:
            yaml_file: Path to YAML configuration file
            **kwargs: Additional arguments for ConfigManager
        """
        manager = ConfigManager.from_yaml(yaml_file, **kwargs)
        return cls(manager.load().get_config())
    
    @classmethod
    def from_multi_sources(
        cls,
        env_file: Optional[Union[str, Path]] = None,
        json_file: Optional[Union[str, Path]] = None,
        yaml_file: Optional[Union[str, Path]] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> 'EasySwitch':
        """
        Create client from multiple configuration sources with fallback logic.
        Sources are loaded in this order with later sources overriding earlier ones:
        1. Environment variables (.env)
        2. JSON file
        3. YAML file
        4. Python dictionary
        
        Args:
            env_file: Path to .env file (optional)
            json_file: Path to JSON file (optional)
            yaml_file: Path to YAML file (optional)
            config_dict: Configuration dictionary (optional)
            **kwargs: Additional arguments for ConfigManager
        """
        manager = ConfigManager()

        # Add .env source if exists
        if env_file:
            manager.add_source('env', env_file)

        # Add json file source if exists
        if json_file:
            manager.add_source('json', json_file)
        
        # Add yaml file source if exists
        if yaml_file:
            manager.add_source('yaml', yaml_file)
        
        # And dict source too
        if config_dict:
            manager.add_source('dict', config_dict)

        return cls(manager.load(**kwargs).get_config())

    def _validate_providers(self):
        """Validate provider configuration."""

        if not self.config.providers:
            raise ConfigurationError(
                "No providers configured. At least one provider must be enabled."
            )

        if self.config.default_provider:
            if self.config.default_provider not in self.config.providers:
                raise ConfigurationError(
                    f"Default provider '{self.config.default_provider}' "
                    "must be in configured providers."
                )
        else:
            # Set first provider as default if none specified
            self.config.default_provider = next(iter(self.config.providers.keys()))
    
    def _initialize_integrators(self):
        """Initialize all configured provider integrators."""

        # Validate providers
        self._validate_providers()

        # Initialize the integrators based on the enabled providers
        for provider_name, provider_config in self.config.providers.items():
            # Load the adapter module only if needed
            if provider_name.upper() not in AdaptersRegistry.list():
                # Then load it
                load_adapter(provider_name)

            try:
                provider = Provider(provider_name)
                adapter_class = AdaptersRegistry.get(provider.value)
                self._integrators[provider] = adapter_class(
                    provider_config,
                    context = {
                        'debug_mode': self.config.debug,
                        'log_config': self.config.logging,
                        'default_currency': self.config.default_currency
                    }
                )
            except ValueError as e:
                raise InvalidProviderError(
                    f"Invalid provider '{provider_name}': {str(e)}"
                )
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to initialize provider '{provider_name}': {str(e)}"
                )
    
    def _get_integrator(
        self, 
        provider: Optional[Provider] = None
    ) -> BaseAdapter:
        """Get the integrator for specified provider or default."""

        provider = provider or self.config.default_provider

        if not provider:
            raise ConfigurationError(
                "No provider specified and no default provider set"
            )
        
        if provider not in self._integrators:
            raise InvalidProviderError(
                f"The Provider '{provider}' is not supported. "
                "perhaps you forgot to enable it in the configuration. "
                f"Available choices are: {self.config.providers}"
            )
        
        return self._integrators[provider]
    
    def send_payment(
        self,
        transaction: TransactionDetail,
        provider: Optional[Provider] = None,
    ) -> PaymentResponse:
        """
        Sends a payment request to a specific provider.
        
        Args:
            transaction: The transaction object containing payment details
            provider: The payment provider to use
            
        Returns:
            PaymentResponse: Response to the payment request
        """
        provider =  provider or transaction.provider or self.config.default_provider
        integrator = self._get_integrator(provider)
        return asyncio.run(
                integrator.send_payment(
                transaction = transaction
            )
        )
    
    def check_status(
        self, 
        transaction_id: str,
        provider: Optional[Provider] = None, 
    ) -> TransactionStatus:
        """
        Checks a transaction status.
        
        Args:
            provider: The payment provider to use
            transaction_id: The transaction ID to check
            
        Returns:
            TransactionStatus: The current status of the transaction
        """
        provider =  provider or self.config.default_provider
        integrator = self._get_integrator(provider)
        return asyncio.run(
            integrator.check_status(transaction_id)
        )
    
    def cancel_transaction(
        self, 
        transaction_id: str,
        provider: Optional[Provider] = None,
    ) -> bool:
        """
        Cancel a transaction if supported.
        
        Args:
            provider: The payment provider to use
            transaction_id: The transaction ID to cancel
            
        Returns:
            bool: True if cancellation succeeded, False otherwise
        """
        provider =  provider or self.config.default_provider
        integrator = self._get_integrator(provider)
        return asyncio.run(
            integrator.cancel_transaction(transaction_id)
        ) 
    
    def refund(
        self,
        transaction_id: str,
        provider: Optional[Provider] = None,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> PaymentResponse:
        """
        Performs a refund for a transaction.
        This method allows you to refund a transaction either fully or partially.
        
        Args:
            provider: The payment provider to use
            transaction_id: The transaction ID to check
            amount: The amount to refund (if None, refund full amount)
            reason: reason for the refund (optional)
            
        Returns:
            PaymentResponse: Response to the refund request
        """
        provider =  provider or self.config.default_provider
        integrator = self._get_integrator(provider)
        return asyncio.run(
            integrator.refund(
                transaction_id=transaction_id,
                amount=amount,
                reason=reason
            )
        )
    
    def validate_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, Any],
        provider: Optional[Provider] = None
    ) -> bool:
        """
        Validates a webhook event.
        
        Args:
            provider: The payment provider to use
            payload: The payload of the webhook event
            headers: The headers of the webhook request
            
        Returns:
            bool: True if the webhook is valid, False elsewhere
        """
        provider =  provider or self.config.default_provider
        integrator = self._get_integrator(provider)
        return asyncio.run(
            integrator.validate_webhook(
                payload = payload,
                headers = headers
            )
        )
    
    def parse_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, Any],
        provider: Optional[Provider] = None
    ) -> WebhookEvent:
        """
        Parse a webhook event and return a standardized WebhookEvent object.
        This method validates and processes the webhook payload and headers 
        to extract and return a WebhookEvent object.
        
        Args:
            provider: The payment provider to use
            payload: The payload of the webhook event
            headers: The headers of the webhook request
            
        Returns:
            WebhookEvent: Parsed webhook event object
        """
        provider =  provider or self.config.default_provider
        integrator = self._get_integrator(provider)
        return asyncio.run(
            integrator.parse_webhook(
                payload = payload,
                headers = headers
            )
        )
