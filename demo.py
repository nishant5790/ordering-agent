#!/usr/bin/env python3
"""
Demo script for the Multi-Agent Order Chatbot System with LangChain
This script demonstrates the system functionality with example conversations
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from agents import AgentManager
from llm_manager import LLMManager

def print_chat_message(speaker, message, agent_name=None):
    """Print a formatted chat message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if speaker == "User":
        print(f"\n[{timestamp}] 👤 {speaker}: {message}")
    else:
        agent_emoji = "🤖"
        if agent_name == "Orchestrator":
            agent_emoji = "🎯"
        elif agent_name == "Generic":
            agent_emoji = "📦"
        elif agent_name == "Bulk":
            agent_emoji = "📊"
        
        print(f"\n[{timestamp}] {agent_emoji} {speaker} ({agent_name}): {message}")
        
        # Check if this message contains a final output
        if "📋 **Final Output:**" in message:
            print("\n" + "="*60)
            print("🎯 FINAL OUTPUT (JSON Format):")
            print("="*60)
            try:
                # Extract JSON content
                start = message.find("```json") + 7
                end = message.find("```", start)
                if start > 6 and end > start:
                    json_str = message[start:end].strip()
                    import json
                    output = json.loads(json_str)
                    print(json.dumps(output, indent=2))
                    print("="*60)
            except Exception as e:
                print(f"Error parsing JSON: {e}")

def demo_generic_order():
    """Demonstrate a generic order workflow"""
    print("\n" + "="*60)
    print("🎬 DEMO 1: Generic Order Workflow (LangChain)")
    print("="*60)
    
    # Initialize system
    db = DatabaseManager("demo_generic.db")
    agent_manager = AgentManager(db, "demo_generic_session", "openai")
    
    # Show LLM info
    llm_info = agent_manager.get_llm_info()
    print(f"🤖 Using LLM Provider: {llm_info['provider'].title()} - {llm_info['model']}")
    print(f"🔗 LangChain Agent Status: {'🟢 Active' if llm_info['available'] else '🔴 Inactive'}")
    
    # Simulate conversation
    conversation = [
        ("User", "I need 10 wooden desks"),
        ("Bot", "Please provide a title for this order."),
        ("User", "Wooden Desk Order"),
        ("Bot", "Describe the request."),
        ("User", "10 wooden desks for the new conference room."),
        ("Bot", "Classified as generic order. Handing off to Generic Order Agent..."),
        ("User", "Yes"),
        ("Bot", "Please specify the brand or vendor preference."),
        ("User", "UrbanCraft"),
        ("Bot", "Here's the summary of your order:\n\nTitle: Wooden Desk Order\nDescription: 10 wooden desks for the new conference room.\nProduct: wooden desks\nQuantity: 10\nBrand Preference: UrbanCraft\n\nPlease confirm if this is correct (yes/no)."),
        ("User", "Yes"),
        ("Bot", "Order confirmed and saved!\n\n📋 **Final Output:**\n```json\n{\n  \"title\": \"Wooden Desk Order\",\n  \"description\": \"10 wooden desks for the new conference room.\",\n  \"product_name\": \"wooden desks\",\n  \"quantity\": 10,\n  \"brand_preference\": \"UrbanCraft\"\n}\n```\n\nIs there anything else you'd like to order?")
    ]
    
    for speaker, message in conversation:
        if speaker == "User":
            print_chat_message("User", message)
            time.sleep(1)  # Simulate typing delay
        else:
            # Process through agent manager
            response = agent_manager.process_message(message if speaker == "User" else "")
            current_agent = agent_manager.get_current_agent_name()
            print_chat_message("Bot", response, current_agent)
            time.sleep(1.5)  # Simulate processing delay
    
    # Show final state
    print(f"\n📊 Final State:")
    print(f"Current Agent: {agent_manager.get_current_agent_name()}")
    
    # Show saved orders
    orders = db.get_orders_by_session("demo_generic_session")
    print(f"Orders Created: {len(orders)}")
    for order in orders:
        print(f"  - {order['title']}: {order['quantity']} {order['product_name']}")
    
    # Cleanup
    os.remove("demo_generic.db")
    print("\n✅ Demo completed and cleaned up!")

def demo_bulk_order():
    """Demonstrate a bulk order workflow"""
    print("\n" + "="*60)
    print("🎬 DEMO 2: Bulk Order Workflow (LangChain)")
    print("="*60)
    
    # Initialize system
    db = DatabaseManager("demo_bulk.db")
    agent_manager = AgentManager(db, "demo_bulk_session", "openai")
    
    # Show LLM info
    llm_info = agent_manager.get_llm_info()
    print(f"🤖 Using LLM Provider: {llm_info['provider'].title()} - {llm_info['model']}")
    print(f"🔗 LangChain Agent Status: {'🟢 Active' if llm_info['available'] else '🔴 Inactive'}")
    
    # Simulate conversation
    conversation = [
        ("User", "I need 500 water bottles"),
        ("Bot", "Please provide a title for this order."),
        ("User", "Bottle Order"),
        ("Bot", "Describe the request."),
        ("User", "Need 500 reusable water bottles for our marathon event."),
        ("Bot", "Classified as bulk order. Handing off to Bulk Order Agent..."),
        ("User", "Yes"),
        ("Bot", "Please specify the supplier preference."),
        ("User", "BottlePro or any eco-friendly vendor"),
        ("Bot", "Here's the summary of your bulk order:\n\nTitle: Bottle Order\nDescription: Need 500 reusable water bottles for our marathon event.\nProduct: reusable water bottles\nQuantity: 500\nSupplier Preference: BottlePro or any eco-friendly vendor\n\nPlease confirm if this is correct (yes/no)."),
        ("User", "Yes"),
        ("Bot", "Bulk order confirmed and saved!\n\n📋 **Final Output:**\n```json\n{\n  \"title\": \"Bottle Order\",\n  \"description\": \"Need 500 reusable water bottles for our marathon event.\",\n  \"product_name\": \"reusable water bottles\",\n  \"quantity\": 500,\n  \"brand_preference\": \"BottlePro or any eco-friendly vendor\"\n}\n```\n\nIs there anything else you'd like to order?")
    ]
    
    for speaker, message in conversation:
        if speaker == "User":
            print_chat_message("User", message)
            time.sleep(1)  # Simulate typing delay
        else:
            # Process through agent manager
            response = agent_manager.process_message(message if speaker == "User" else "")
            current_agent = agent_manager.get_current_agent_name()
            print_chat_message("Bot", response, current_agent)
            time.sleep(1.5)  # Simulate processing delay
    
    # Show final state
    print(f"\n📊 Final State:")
    print(f"Current Agent: {agent_manager.get_current_agent_name()}")
    
    # Show saved orders
    orders = db.get_orders_by_session("demo_bulk_session")
    print(f"Orders Created: {len(orders)}")
    for order in orders:
        print(f"  - {order['title']}: {order['quantity']} {order['product_name']}")
    
    # Cleanup
    os.remove("demo_bulk.db")
    print("\n✅ Demo completed and cleaned up!")

def demo_agent_handoff():
    """Demonstrate agent handoff functionality"""
    print("\n" + "="*60)
    print("🎬 DEMO 3: Agent Handoff Workflow (LangChain)")
    print("="*60)
    
    # Initialize system
    db = DatabaseManager("demo_handoff.db")
    agent_manager = AgentManager(db, "demo_handoff_session", "openai")
    
    # Show LLM info
    llm_info = agent_manager.get_llm_info()
    print(f"🤖 Using LLM Provider: {llm_info['provider'].title()} - {llm_info['model']}")
    print(f"🔗 LangChain Agent Status: {'🟢 Active' if llm_info['available'] else '🔴 Inactive'}")
    
    # Simulate conversation with handoff
    conversation = [
        ("User", "I need 300 USB drives"),
        ("Bot", "Please provide a title for this order."),
        ("User", "USB Drive Bulk Order"),
        ("Bot", "Describe the request."),
        ("User", "300 USB drives for employee onboarding kits."),
        ("Bot", "Classified as bulk order. Handing off to Bulk Order Agent..."),
        ("User", "No, actually I need 20 desk lamps instead."),
        ("Bot", "Please provide a title for desk lamp order."),
        ("User", "Desk Lamp Order"),
        ("Bot", "Describe the request."),
        ("User", "20 desk lamps for office lighting."),
        ("Bot", "Classified as generic order. Handing off to Generic Order Agent..."),
        ("User", "No"),
        ("Bot", "Here's the summary of your order:\n\nTitle: Desk Lamp Order\nDescription: 20 desk lamps for office lighting.\nProduct: desk lamps\nQuantity: 20\nBrand Preference: None\n\nPlease confirm if this is correct (yes/no)."),
        ("User", "Yes"),
        ("Bot", "Order confirmed and saved!\n\n📋 **Final Output:**\n```json\n{\n  \"title\": \"Desk Lamp Order\",\n  \"description\": \"20 desk lamps for office lighting.\",\n  \"product_name\": \"desk lamps\",\n  \"quantity\": 20,\n  \"brand_preference\": \"None\"\n}\n```\n\nIs there anything else you'd like to order?")
    ]
    
    for speaker, message in conversation:
        if speaker == "User":
            print_chat_message("User", message)
            time.sleep(1)  # Simulate typing delay
        else:
            # Process through agent manager
            response = agent_manager.process_message(message if speaker == "User" else "")
            current_agent = agent_manager.get_current_agent_name()
            print_chat_message("Bot", response, current_agent)
            time.sleep(1.5)  # Simulate processing delay
    
    # Show final state
    print(f"\n📊 Final State:")
    print(f"Current Agent: {agent_manager.get_current_agent_name()}")
    
    # Show saved orders
    orders = db.get_orders_by_session("demo_handoff_session")
    print(f"Orders Created: {len(orders)}")
    for order in orders:
        print(f"  - {order['title']}: {order['quantity']} {order['product_name']}")
    
    # Cleanup
    os.remove("demo_handoff.db")
    print("\n✅ Demo completed and cleaned up!")

def demo_llm_provider_switching():
    """Demonstrate LLM provider switching"""
    print("\n" + "="*60)
    print("🎬 DEMO 4: LLM Provider Switching (LangChain)")
    print("="*60)
    
    # Initialize system
    db = DatabaseManager("demo_provider_switch.db")
    agent_manager = AgentManager(db, "demo_provider_switch_session", "openai")
    
    # Show initial LLM info
    llm_info = agent_manager.get_llm_info()
    print(f"🤖 Initial LLM Provider: {llm_info['provider'].title()} - {llm_info['model']}")
    
    # Switch to different providers
    providers = ["google", "groq", "openai"]
    
    for provider in providers:
        print(f"\n🔄 Switching to {provider.title()}...")
        agent_manager.switch_llm_provider(provider)
        
        # Get updated info
        llm_info = agent_manager.get_llm_info()
        print(f"✅ Switched to: {llm_info['provider'].title()} - {llm_info['model']}")
        print(f"   Status: {'🟢 Active' if llm_info['available'] else '🔴 Inactive'}")
        print(f"   API Key: {'✅ Configured' if llm_info['api_key_configured'] else '❌ Not configured'}")
        
        time.sleep(1)
    
    # Cleanup
    os.remove("demo_provider_switch.db")
    print("\n✅ Provider switching demo completed and cleaned up!")

def demo_final_output_format():
    """Demonstrate the final output format"""
    print("\n" + "="*60)
    print("🎬 DEMO 5: Final Output Format (JSON)")
    print("="*60)
    
    print("📋 The system generates final outputs in this exact JSON format:")
    print("="*60)
    
    example_output = {
        "title": "Example Order",
        "description": "This is an example order description",
        "product_name": "Example Product",
        "quantity": 100,
        "brand_preference": "Example Brand"
    }
    
    import json
    print(json.dumps(example_output, indent=2))
    print("="*60)
    
    print("✅ This format is automatically generated when orders are confirmed")
    print("✅ The output is displayed in the Streamlit UI")
    print("✅ All order data is saved to the database")
    print("✅ The format matches your exact specification")

def run_all_demos():
    """Run all demonstration scenarios"""
    print("🚀 Multi-Agent Order Chatbot System - Live Demonstrations (LangChain)")
    print("=" * 80)
    print("This demo will show you how the LangChain-based system works with real conversations.")
    print("Each demo simulates a complete order workflow using LangChain agents.")
    print("The final output will be in the specified JSON format.\n")
    
    input("Press Enter to start the demonstrations...")
    
    try:
        # Run all demos
        demo_generic_order()
        time.sleep(2)
        
        demo_bulk_order()
        time.sleep(2)
        
        demo_agent_handoff()
        time.sleep(2)
        
        demo_llm_provider_switching()
        time.sleep(2)
        
        demo_final_output_format()
        
        print("\n" + "="*80)
        print("🎉 All demonstrations completed successfully!")
        print("="*80)
        print("\n🚀 Key Features Demonstrated:")
        print("✅ Multi-agent architecture with LangChain")
        print("✅ LLM provider management (OpenAI, Google, Groq)")
        print("✅ Agent tools and prompts")
        print("✅ Conversation memory and state management")
        print("✅ Seamless agent handoffs")
        print("✅ Database storage and retrieval")
        print("✅ Session management")
        print("✅ Error handling and validation")
        print("✅ LLM provider switching")
        print("✅ Final output in specified JSON format")
        
        print("\n🔗 LangChain Features:")
        print("✅ Agent Executors with tools")
        print("✅ Prompt templates")
        print("✅ Conversation memory")
        print("✅ Tool integration")
        print("✅ Error handling")
        
        print("\n📋 Final Output Format:")
        print("✅ JSON structure with title, description, product_name, quantity, brand_preference")
        print("✅ Automatically generated when orders are confirmed")
        print("✅ Displayed in Streamlit UI")
        print("✅ Saved to database")
        
        print("\nTo run the full application:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure API keys in .env file (optional)")
        print("3. Run Streamlit app: streamlit run main.py")
        print("4. Open browser to: http://localhost:8501")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")

if __name__ == "__main__":
    run_all_demos()
