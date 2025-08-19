from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from database import DatabaseManager
from llm_manager import LLMManager
import json

class BaseAgent(ABC):
    """Base class for all agents using LangChain"""
    
    def __init__(self, db_manager: DatabaseManager, session_id: str, llm_manager: LLMManager):
        self.db_manager = db_manager
        self.session_id = session_id
        self.llm_manager = llm_manager
        self.name = self.__class__.__name__
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.tools = self._create_tools()
        self.prompt = self._create_prompt()
        self.agent_executor = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the LangChain agent"""
        try:
            if self.llm_manager.llm:
                self.agent_executor = AgentExecutor.from_agent_and_tools(
                    agent=self._create_agent(),
                    tools=self.tools,
                    memory=self.memory,
                    verbose=True,
                    handle_parsing_errors=True
                )
        except Exception as e:
            print(f"Error initializing agent: {e}")
    
    @abstractmethod
    def _create_tools(self) -> List[BaseTool]:
        """Create tools for the agent"""
        pass
    
    @abstractmethod
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for the agent"""
        pass
    
    @abstractmethod
    def _create_agent(self):
        """Create the LangChain agent"""
        pass
    
    @abstractmethod
    def process_message(self, user_input: str, context: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Process user message and return response and updated context"""
        pass
    
    def log_interaction(self, user_input: str, response: str):
        """Log the interaction to database"""
        self.db_manager.log_conversation(
            self.session_id, user_input, response, self.name
        )
    
    def generate_final_output(self) -> str:
        """Generate the final output in the specified JSON format"""
        if not hasattr(self, 'order_data') or not self.order_data:
            return "No order data available"
        
        output = {
            "title": self.order_data.get("title", ""),
            "description": self.order_data.get("description", ""),
            "product_name": self.order_data.get("product_name", ""),
            "quantity": self.order_data.get("quantity", 0),
            "brand_preference": self.order_data.get("brand_preference", "")
        }
        
        return json.dumps(output, indent=2)

class MainAgent(BaseAgent):
    """Main orchestrator agent that routes requests to appropriate agents"""
    
    def __init__(self, db_manager: DatabaseManager, session_id: str, llm_manager: LLMManager):
        super().__init__(db_manager, session_id, llm_manager)
        self.name = "Orchestrator"
        self.state = "waiting_for_title"
        self.order_data = {}
    
    def _create_tools(self) -> List[BaseTool]:
        """Create tools for the main agent"""
        from langchain.tools import tool
        
        @tool
        def classify_order(description: str, type_of_request: str = None) -> str:
            """Classify an order request as generic or bulk"""
            return self.llm_manager.classify_request(description, type_of_request)
        
        @tool
        def get_order_summary() -> str:
            """Get a summary of the current order"""
            if not self.order_data:
                return "No order data available"
            
            return f"""
Order Summary:
- Title: {self.order_data.get('title', 'N/A')}
- Description: {self.order_data.get('description', 'N/A')}
- Type: {self.order_data.get('order_type', 'N/A')}
            """.strip()
        
        return [classify_order, get_order_summary]
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for the main agent"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are the Main Orchestrator Agent for an order management system. Your role is to:

1. Collect order title and description from users
2. Classify orders as either "generic" or "bulk" using the classify_order tool
3. Route users to appropriate specialized agents
4. Maintain a professional and helpful tone

Current state: {state}
Order data: {order_data}

Always ask for the next required information based on the current state."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def _create_agent(self):
        """Create the LangChain agent"""
        if not self.llm_manager.llm:
            return None
        
        return create_openai_functions_agent(
            llm=self.llm_manager.llm,
            tools=self.tools,
            prompt=self.prompt
        )
    
    def process_message(self, user_input: str, context: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Process user message and route to appropriate agent"""
        
        if self.state == "waiting_for_title":
            self.order_data["title"] = user_input
            self.state = "waiting_for_description"
            response = "Describe the request."
            context["current_agent"] = self.name
            context["state"] = self.state
            context["order_data"] = self.order_data
            
        elif self.state == "waiting_for_description":
            self.order_data["description"] = user_input
            self.state = "classifying"
            
            # Use LLM manager to classify the request
            order_type = self.llm_manager.classify_request(
                description=user_input,
                type_of_request=context.get("type_of_request")
            )
            
            self.order_data["order_type"] = order_type
            context["order_data"] = self.order_data
            
            if order_type == "generic":
                response = f"Classified as generic order. Handing off to Generic Order Agent..."
                context["next_agent"] = "GenericOrderAgent"
            else:
                response = f"Classified as bulk order. Handing off to Bulk Order Agent..."
                context["next_agent"] = "BulkOrderAgent"
            
            context["current_agent"] = self.name
            context["state"] = "handing_off"
            
        else:
            response = "Please provide a title for this order."
            self.state = "waiting_for_title"
            self.order_data = {}
            context["state"] = self.state
            context["order_data"] = self.order_data
        
        self.log_interaction(user_input, response)
        return response, context

class GenericOrderAgent(BaseAgent):
    """Agent for handling generic/single orders using LangChain"""
    
    def __init__(self, db_manager: DatabaseManager, session_id: str, llm_manager: LLMManager):
        super().__init__(db_manager, session_id, llm_manager)
        self.name = "Generic"
        self.state = "collecting_details"
        self.order_data = {}
    
    def _create_tools(self) -> List[BaseTool]:
        """Create tools for the generic order agent"""
        from langchain.tools import tool
        
        @tool
        def extract_order_details(description: str) -> Dict[str, Any]:
            """Extract product name and quantity from order description"""
            import re
            
            # Extract quantity
            quantity_match = re.search(r'(\d+)', description)
            quantity = int(quantity_match.group(1)) if quantity_match else 1
            
            # Extract product name (simplified)
            words = description.split()
            if len(words) >= 3:
                product_name = " ".join(words[1:3])
            else:
                product_name = description
            
            return {
                "product_name": product_name,
                "quantity": quantity
            }
        
        @tool
        def save_order(order_data: Dict[str, Any]) -> str:
            """Save the order to the database"""
            try:
                order_id = self.db_manager.save_order(self.session_id, order_data)
                return f"Order saved successfully with ID: {order_id}"
            except Exception as e:
                return f"Error saving order: {e}"
        
        return [extract_order_details, save_order]
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for the generic order agent"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are the Generic Order Agent, specialized in handling single and small orders. Your role is to:

1. Collect and confirm order details
2. Ask for brand preferences
3. Generate order summaries
4. Save orders to the database

Current state: {state}
Order data: {order_data}

Use the available tools to help process orders efficiently."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def _create_agent(self):
        """Create the LangChain agent"""
        if not self.llm_manager.llm:
            return None
        
        return create_openai_functions_agent(
            llm=self.llm_manager.llm,
            tools=self.tools,
            prompt=self.prompt
        )
    
    def process_message(self, user_input: str, context: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Process generic order details"""
        
        # Get order data from context
        if "order_data" in context:
            self.order_data = context["order_data"]
        
        if self.state == "collecting_details":
            # Extract product name and quantity from description
            description = self.order_data.get("description", "")
            
            # Use tool to extract details
            if self.agent_executor and self.agent_executor.tools:
                try:
                    result = self.agent_executor.invoke({
                        "input": f"Extract order details from: {description}"
                    })
                    extracted_data = result.get("output", {})
                    if isinstance(extracted_data, dict):
                        self.order_data.update(extracted_data)
                except Exception as e:
                    print(f"Error using agent executor: {e}")
                    # Fallback to simple extraction
                    self._fallback_extraction(description)
            else:
                self._fallback_extraction(description)
            
            self.state = "asking_brand_preference"
            response = f"Confirming order for {self.order_data.get('quantity', '')} {self.order_data.get('product_name', 'items')}. Any brand or vendor preference?"
            
        elif self.state == "asking_brand_preference":
            if user_input.lower() in ["yes", "yeah", "yep", "sure"]:
                self.state = "collecting_brand"
                response = "Please specify the brand or vendor preference."
            else:
                self.order_data["brand_preference"] = "None"
                self.state = "confirming"
                response = self._generate_order_summary()
                
        elif self.state == "collecting_brand":
            self.order_data["brand_preference"] = user_input
            self.state = "confirming"
            response = self._generate_order_summary()
            
        elif self.state == "confirming":
            if user_input.lower() in ["yes", "yeah", "yep", "sure", "confirm", "ok"]:
                # Save order to database
                self.db_manager.save_order(self.session_id, self.order_data)
                
                # Generate final output in specified format
                final_output = self.generate_final_output()
                response = f"Order confirmed and saved!\n\n📋 **Final Output:**\n```json\n{final_output}\n```\n\nIs there anything else you'd like to order?"
                
                self.state = "collecting_details"
                self.order_data = {}
                context["next_agent"] = "MainAgent"
            else:
                response = "Let me know if you want to make any changes to the order."
                
        else:
            response = "I'm here to help with your order. What would you like to order?"
            self.state = "collecting_details"
        
        context["current_agent"] = self.name
        context["state"] = self.state
        context["order_data"] = self.order_data
        
        self.log_interaction(user_input, response)
        return response, context
    
    def _fallback_extraction(self, description: str):
        """Fallback method for extracting order details"""
        import re
        quantity_match = re.search(r'(\d+)', description)
        if quantity_match:
            self.order_data["quantity"] = int(quantity_match.group(1))
        
        words = description.split()
        if len(words) >= 3:
            self.order_data["product_name"] = " ".join(words[1:3])
        else:
            self.order_data["product_name"] = description
    
    def _generate_order_summary(self) -> str:
        """Generate order summary for confirmation"""
        summary = f"""
Here's the summary of your order:

Title: {self.order_data.get('title', 'N/A')}
Description: {self.order_data.get('description', 'N/A')}
Product: {self.order_data.get('product_name', 'N/A')}
Quantity: {self.order_data.get('quantity', 'N/A')}
Brand Preference: {self.order_data.get('brand_preference', 'None')}

Please confirm if this is correct (yes/no).
        """.strip()
        return summary

class BulkOrderAgent(BaseAgent):
    """Agent for handling bulk/mass orders using LangChain"""
    
    def __init__(self, db_manager: DatabaseManager, session_id: str, llm_manager: LLMManager):
        super().__init__(db_manager, session_id, llm_manager)
        self.name = "Bulk"
        self.state = "collecting_details"
        self.order_data = {}
    
    def _create_tools(self) -> List[BaseTool]:
        """Create tools for the bulk order agent"""
        from langchain.tools import tool
        
        @tool
        def extract_bulk_order_details(description: str) -> Dict[str, Any]:
            """Extract product name and quantity from bulk order description"""
            import re
            
            # Extract quantity
            quantity_match = re.search(r'(\d+)', description)
            quantity = int(quantity_match.group(1)) if quantity_match else 100
            
            # Extract product name (simplified)
            words = description.split()
            if len(words) >= 3:
                product_name = " ".join(words[1:3])
            else:
                product_name = description
            
            return {
                "product_name": product_name,
                "quantity": quantity
            }
        
        @tool
        def save_bulk_order(order_data: Dict[str, Any]) -> str:
            """Save the bulk order to the database"""
            try:
                order_id = self.db_manager.save_order(self.session_id, order_data)
                return f"Bulk order saved successfully with ID: {order_id}"
            except Exception as e:
                return f"Error saving bulk order: {e}"
        
        return [extract_bulk_order_details, save_bulk_order]
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for the bulk order agent"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are the Bulk Order Agent, specialized in handling large quantity and wholesale orders. Your role is to:

1. Collect and confirm bulk order details
2. Ask for supplier preferences
3. Generate order summaries
4. Save orders to the database

Current state: {state}
Order data: {order_data}

Use the available tools to help process bulk orders efficiently."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def _create_agent(self):
        """Create the LangChain agent"""
        if not self.llm_manager.llm:
            return None
        
        return create_openai_functions_agent(
            llm=self.llm_manager.llm,
            tools=self.tools,
            prompt=self.prompt
        )
    
    def process_message(self, user_input: str, context: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Process bulk order details"""
        
        # Get order data from context
        if "order_data" in context:
            self.order_data = context["order_data"]
        
        if self.state == "collecting_details":
            # Extract product name and quantity from description
            description = self.order_data.get("description", "")
            
            # Use tool to extract details
            if self.agent_executor and self.agent_executor.tools:
                try:
                    result = self.agent_executor.invoke({
                        "input": f"Extract bulk order details from: {description}"
                    })
                    extracted_data = result.get("output", {})
                    if isinstance(extracted_data, dict):
                        self.order_data.update(extracted_data)
                except Exception as e:
                    print(f"Error using agent executor: {e}")
                    # Fallback to simple extraction
                    self._fallback_extraction(description)
            else:
                self._fallback_extraction(description)
            
            self.state = "asking_supplier_preference"
            response = f"Confirming bulk order of {self.order_data.get('quantity', '')} {self.order_data.get('product_name', 'items')}. Any supplier preference?"
            
        elif self.state == "asking_supplier_preference":
            if user_input.lower() in ["yes", "yeah", "yep", "sure"]:
                self.state = "collecting_supplier"
                response = "Please specify the supplier preference."
            else:
                self.order_data["brand_preference"] = "None"
                self.state = "confirming"
                response = self._generate_order_summary()
                
        elif self.state == "collecting_supplier":
            self.order_data["brand_preference"] = user_input
            self.state = "confirming"
            response = self._generate_order_summary()
            
        elif self.state == "confirming":
            if user_input.lower() in ["yes", "yeah", "yep", "sure", "confirm", "ok"]:
                # Save order to database
                self.db_manager.save_order(self.session_id, self.order_data)
                
                # Generate final output in specified format
                final_output = self.generate_final_output()
                response = f"Bulk order confirmed and saved!\n\n📋 **Final Output:**\n```json\n{final_output}\n```\n\nIs there anything else you'd like to order?"
                
                self.state = "collecting_details"
                self.order_data = {}
                context["next_agent"] = "MainAgent"
            else:
                response = "Let me know if you want to make any changes to the order."
                
        else:
            response = "I'm here to help with your bulk order. What would you like to order?"
            self.state = "collecting_details"
        
        context["current_agent"] = self.name
        context["state"] = self.state
        context["order_data"] = self.order_data
        
        self.log_interaction(user_input, response)
        return response, context
    
    def _fallback_extraction(self, description: str):
        """Fallback method for extracting order details"""
        import re
        quantity_match = re.search(r'(\d+)', description)
        if quantity_match:
            self.order_data["quantity"] = int(quantity_match.group(1))
        
        words = description.split()
        if len(words) >= 3:
            self.order_data["product_name"] = " ".join(words[1:3])
        else:
            self.order_data["product_name"] = description
    
    def _generate_order_summary(self) -> str:
        """Generate order summary for confirmation"""
        summary = f"""
Here's the summary of your bulk order:

Title: {self.order_data.get('title', 'N/A')}
Description: {self.order_data.get('description', 'N/A')}
Product: {self.order_data.get('product_name', 'N/A')}
Quantity: {self.order_data.get('quantity', 'N/A')}
Supplier Preference: {self.order_data.get('brand_preference', 'None')}

Please confirm if this is correct (yes/no).
        """.strip()
        return summary

class AgentManager:
    """Manages agent transitions and state using LangChain agents"""
    
    def __init__(self, db_manager: DatabaseManager, session_id: str, llm_provider: str = None):
        self.db_manager = db_manager
        self.session_id = session_id
        self.llm_manager = LLMManager(provider=llm_provider)
        
        # Initialize agents with LLM manager
        self.agents = {
            "MainAgent": MainAgent(db_manager, session_id, self.llm_manager),
            "GenericOrderAgent": GenericOrderAgent(db_manager, session_id, self.llm_manager),
            "BulkOrderAgent": BulkOrderAgent(db_manager, session_id, self.llm_manager)
        }
        
        self.current_agent = "MainAgent"
        self.context = {
            "current_agent": "MainAgent",
            "state": "waiting_for_title",
            "order_data": {},
            "type_of_request": None
        }
    
    def process_message(self, user_input: str) -> str:
        """Process user message through current agent"""
        
        # Check if user wants to start over
        if user_input.lower() in ["start over", "reset", "new order", "restart"]:
            self.current_agent = "MainAgent"
            self.context = {
                "current_agent": "MainAgent",
                "state": "waiting_for_title",
                "order_data": {},
                "type_of_request": None
            }
            return "Starting fresh! Please provide a title for your order."
        
        # Get current agent
        agent = self.agents[self.current_agent]
        
        # Process message
        response, updated_context = agent.process_message(user_input, self.context)
        self.context = updated_context
        
        # Check if agent wants to hand off
        if "next_agent" in updated_context:
            next_agent = updated_context["next_agent"]
            if next_agent in self.agents:
                self.current_agent = next_agent
                self.context["current_agent"] = next_agent
                # Reset the next agent flag
                if "next_agent" in self.context:
                    del self.context["next_agent"]
        
        return response
    
    def get_current_agent_name(self) -> str:
        """Get the name of the current agent"""
        return self.agents[self.current_agent].name
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        return self.context.copy()
    
    def switch_llm_provider(self, new_provider: str):
        """Switch to a different LLM provider"""
        self.llm_manager.switch_provider(new_provider)
        
        # Reinitialize agents with new LLM
        for agent_name, agent in self.agents.items():
            agent.llm_manager = self.llm_manager
            agent._initialize_agent()
    
    def get_llm_info(self) -> Dict[str, Any]:
        """Get information about the current LLM provider"""
        return self.llm_manager.get_provider_info()
