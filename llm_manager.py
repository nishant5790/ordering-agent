from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from typing import Optional, Dict, Any
import config

class LLMManager:
    """Manages different LLM providers using LangChain"""
    
    def __init__(self, provider: str = None):
        self.provider = provider or config.DEFAULT_LLM_PROVIDER
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on provider"""
        try:
            if self.provider == "openai" and config.OPENAI_API_KEY:
                return ChatOpenAI(
                    model=config.DEFAULT_MODEL,
                    temperature=config.TEMPERATURE,
                    max_tokens=config.MAX_TOKENS,
                    api_key=config.OPENAI_API_KEY
                )
            elif self.provider == "google" and config.GOOGLE_AI_API_KEY:
                return ChatGoogleGenerativeAI(
                    model=config.GOOGLE_MODEL,
                    temperature=config.TEMPERATURE,
                    google_api_key=config.GOOGLE_AI_API_KEY
                )
            elif self.provider == "groq" and config.GROQ_API_KEY:
                return ChatGroq(
                    model=config.GROQ_MODEL,
                    temperature=config.TEMPERATURE,
                    groq_api_key=config.GROQ_API_KEY
                )
            else:
                print(f"Warning: No API key for {self.provider}, using fallback classification")
                return None
        except Exception as e:
            print(f"Error initializing {self.provider} LLM: {e}")
            return None
    
    def classify_request(self, description: str, type_of_request: str = None) -> str:
        """Classify a request using LLM or fallback to rule-based"""
        if not self.llm:
            return self._rule_based_classification(description, type_of_request)
        
        try:
            system_prompt = """You are an order classification expert. Analyze the order request and classify it as either "generic" or "bulk".

Classification rules:
- "generic": Single items, small quantities (1-50), personal use, specific products
- "bulk": Large quantities (100+), multiple items, reselling, wholesale, events

Respond with only "generic" or "bulk"."""

            user_prompt = f"""Description: {description}
Type of request: {type_of_request or "Not specified"}

Classify this order:"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            result = response.content.strip().lower()
            
            # Validate response
            if result in ["generic", "bulk"]:
                return result
            else:
                return self._rule_based_classification(description, type_of_request)
                
        except Exception as e:
            print(f"Error using LLM for classification: {e}")
            return self._rule_based_classification(description, type_of_request)
    
    def _rule_based_classification(self, description: str, type_of_request: str) -> str:
        """Fallback rule-based classification"""
        description_lower = description.lower()
        
        # Keywords that suggest bulk orders
        bulk_keywords = [
            "bulk", "wholesale", "reselling", "business", "company", "office", 
            "event", "conference", "marathon", "onboarding", "employee", "team",
            "hundred", "thousand", "500", "1000", "large quantity", "mass order"
        ]
        
        # Keywords that suggest generic orders
        generic_keywords = [
            "personal", "home", "individual", "single", "one", "few", "small",
            "desk", "lamp", "furniture", "electronics", "personal use"
        ]
        
        # Check for bulk indicators
        for keyword in bulk_keywords:
            if keyword in description_lower:
                return "bulk"
        
        # Check for generic indicators
        for keyword in generic_keywords:
            if keyword in description_lower:
                return "generic"
        
        # Check for quantity numbers
        import re
        quantity_match = re.search(r'(\d+)', description)
        if quantity_match:
            quantity = int(quantity_match.group(1))
            if quantity >= 100:
                return "bulk"
            elif quantity <= 50:
                return "generic"
        
        # Default to generic if uncertain
        return "generic"
    
    def generate_response(self, prompt: str, system_message: str = None) -> str:
        """Generate a response using the LLM"""
        if not self.llm:
            return "I'm sorry, I'm having trouble processing your request right now."
        
        try:
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I encountered an error while processing your request."
    
    def switch_provider(self, new_provider: str):
        """Switch to a different LLM provider"""
        self.provider = new_provider
        self.llm = self._initialize_llm()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current LLM provider"""
        return {
            "provider": self.provider,
            "model": self._get_model_name(),
            "available": self.llm is not None,
            "api_key_configured": self._is_api_key_configured()
        }
    
    def _get_model_name(self) -> str:
        """Get the current model name"""
        if self.provider == "openai":
            return config.DEFAULT_MODEL
        elif self.provider == "google":
            return config.GOOGLE_MODEL
        elif self.provider == "groq":
            return config.GROQ_MODEL
        return "Unknown"
    
    def _is_api_key_configured(self) -> bool:
        """Check if API key is configured for current provider"""
        if self.provider == "openai":
            return bool(config.OPENAI_API_KEY)
        elif self.provider == "google":
            return bool(config.GOOGLE_AI_API_KEY)
        elif self.provider == "groq":
            return bool(config.GROQ_API_KEY)
        return False
