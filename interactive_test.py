#!/usr/bin/env python3
"""
Interactive test script for the Multi-Agent Order Chatbot System
This script allows you to test the conversation flow step by step
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from agents import AgentManager

def print_agent_status(agent_manager):
    """Print current agent status"""
    context = agent_manager.get_context()
    print(f"\n🎯 Current Agent: {agent_manager.get_current_agent_name()}")
    print(f"📊 Current State: {context.get('state', 'N/A')}")
    print(f"📋 Order Data: {context.get('order_data', {})}")

def print_conversation_summary(agent_manager, db):
    """Print a summary of the conversation so far"""
    try:
        conversations = db.get_conversation_history(agent_manager.session_id)
        orders = db.get_orders_by_session(agent_manager.session_id)
        
        print(f"\n📊 Conversation Summary:")
        print(f"  💬 Messages exchanged: {len(conversations)}")
        print(f"  📦 Orders created: {len(orders)}")
        
        if orders:
            print(f"\n📋 Orders:")
            for i, order in enumerate(orders, 1):
                print(f"  {i}. {order['title']} - {order['quantity']} {order['product_name']}")
        
    except Exception as e:
        print(f"Error getting summary: {e}")

def interactive_test():
    """Run interactive test of the conversation flow"""
    print("🚀 Multi-Agent Order Chatbot System - Interactive Test")
    print("=" * 80)
    print("This test allows you to interact with the system step by step.")
    print("Follow the example conversation flow or create your own!")
    print("\nExample flow:")
    print("1. 'I need 10 wooden desks.'")
    print("2. 'Wooden Desk Order'")
    print("3. '10 wooden desks for the new conference room.'")
    print("4. 'Yes, from UrbanCraft.'")
    print("5. 'Yes' (to confirm)")
    print("=" * 80)
    
    # Initialize system
    db = DatabaseManager("interactive_test.db")
    agent_manager = AgentManager(db, "interactive_test_session", "openai")
    
    print(f"\n🎯 Session started with ID: {agent_manager.session_id[:8]}...")
    print_agent_status(agent_manager)
    
    step = 1
    while True:
        try:
            print(f"\n{'='*60}")
            print(f"STEP {step}")
            print(f"{'='*60}")
            
            # Get user input
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() in ['status', 's']:
                print_agent_status(agent_manager)
                print_conversation_summary(agent_manager, db)
                continue
            elif user_input.lower() in ['help', 'h']:
                print("\n📚 Help:")
                print("  - Type your message to continue the conversation")
                print("  - 'status' or 's' - Show current agent status")
                print("  - 'summary' or 'sum' - Show conversation summary")
                print("  - 'quit' or 'q' - Exit the test")
                print("  - 'help' or 'h' - Show this help")
                continue
            elif user_input.lower() in ['summary', 'sum']:
                print_conversation_summary(agent_manager, db)
                continue
            elif not user_input:
                print("⚠️  Please enter a message or type 'help' for options")
                continue
            
            # Process message
            print(f"🔄 Processing message...")
            response = agent_manager.process_message(user_input)
            current_agent = agent_manager.get_current_agent_name()
            
            # Display response
            print(f"\n🤖 Bot ({current_agent}): {response}")
            
            # Check for special events
            if "Handing off to" in response:
                print(f"🔄 AGENT HANDOFF DETECTED!")
            elif "📋 **Final Output:**" in response:
                print(f"🎯 FINAL OUTPUT GENERATED!")
                # Extract and display JSON
                try:
                    start = response.find("```json") + 7
                    end = response.find("```", start)
                    if start > 6 and end > start:
                        json_str = response[start:end].strip()
                        import json
                        output = json.loads(json_str)
                        print(f"\n📋 Final Output (JSON):")
                        print(json.dumps(output, indent=2))
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
            
            # Update status
            print_agent_status(agent_manager)
            step += 1
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    
    try:
        conversations = db.get_conversation_history(agent_manager.session_id)
        orders = db.get_orders_by_session(agent_manager.session_id)
        
        print(f"💬 Total messages: {len(conversations)}")
        print(f"📦 Total orders: {len(orders)}")
        print(f"🎯 Final agent: {agent_manager.get_current_agent_name()}")
        
        if orders:
            print(f"\n📋 Orders created:")
            for i, order in enumerate(orders, 1):
                print(f"  {i}. {order['title']}")
                print(f"     - Product: {order['product_name']}")
                print(f"     - Quantity: {order['quantity']}")
                print(f"     - Brand: {order['brand_preference']}")
        
    except Exception as e:
        print(f"Error getting final summary: {e}")
    
    # Cleanup
    try:
        os.remove("interactive_test.db")
        print("\n🧹 Test database cleaned up")
    except Exception as e:
        print(f"\n⚠️  Could not clean up test database: {e}")

def main():
    """Main function"""
    try:
        interactive_test()
    except Exception as e:
        print(f"💥 Interactive test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
