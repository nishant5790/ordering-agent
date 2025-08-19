import openai
from typing import Optional
import config

class CategoryFinderTool:
    def __init__(self):
        self.client = None
        if config.OPENAI_API_KEY:
            try:
                openai.api_key = config.OPENAI_API_KEY
                self.client = openai
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
    
    def classify_request(self, description: str = None, type_of_request: str = None) -> str:
        """
        Classify a request as "generic" or "bulk" using LLM analysis
        
        Args:
            description: Description of what user wants to buy
            type_of_request: Whether it's for personal use or reselling
            
        Returns:
            "generic" or "bulk"
        """
        if not description:
            return "generic"
        
        # Simple rule-based classification as fallback
        if not self.client:
            return self._rule_based_classification(description, type_of_request)
        
        try:
            # Use LLM for intelligent classification
            prompt = f"""
            Analyze this order request and classify it as either "generic" or "bulk":
            
            Description: {description}
            Type of request: {type_of_request or "Not specified"}
            
            Classification rules:
            - "generic": Single items, small quantities (1-50), personal use, specific products
            - "bulk": Large quantities (100+), multiple items, reselling, wholesale, events
            
            Respond with only "generic" or "bulk".
            """
            
            response = self.client.chat.completions.create(
                model=config.DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().lower()
            
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
