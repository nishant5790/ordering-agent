#!/usr/bin/env python3
"""
Test script for the exact example conversation flow
This script tests the system using the specific example provided by the user
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from agents import AgentManager

def print_conversation_step(step, user_input, bot_response, agent_name):
    """Print a conversation step with clear formatting"""
    print(f"\n{'='*80}")
    print(f"STEP {step}: {agent_name}")
    print(f"{'='*80}")
    print(f"👤 User: {user_input}")
    print(f"🤖 Bot ({agent_name}): {bot_response}")
    
    # Check if this is a handoff
    if "Handing off to" in bot_response:
        print(f"🔄 AGENT HANDOFF DETECTED!")
    elif "📋 **Final Output:**" in bot_response:
        print(f"🎯 FINAL OUTPUT GENERATED!")
        # Extract and display JSON
        try:
            start = bot_response.find("```json") + 7
            end = bot_response.find("```", start)
            if start > 6 and end > start:
                json_str = bot_response[start:end].strip()
                import json
                output = json.loads(json_str)
                print(f"\n📋 Final Output (JSON):")
                print(json.dumps(output, indent=2))
        except Exception as e:
            print(f"Error parsing JSON: {e}")

def test_exact_example_flow():
    """Test the exact example conversation flow provided by the user"""
    print("🚀 Testing Exact Example Conversation Flow")
    print("=" * 80)
    print("This test follows the exact conversation flow you specified:")
    print("1. User: I need 10 wooden desks.")
    print("2. Bot: Please provide a title for this order.")
    print("3. User: Wooden Desk Order")
    print("4. Bot: Describe the request.")
    print("5. User: 10 wooden desks for the new conference room.")
    print("6. [Orchestrator Agent calls category_finder_tool]")
    print("7. [category_finder_tool tool's output -> generic_order_agent]")
    print("8. [Orchestrator Agent hands off to Generic Order Agent]")
    print("9. Bot: Confirming order for 10 wooden desks. Any brand or vendor preference?")
    print("10. User: Yes, from UrbanCraft.")
    print("11. Bot: Here's the summary...")
    print("12. [Summary shown, details saved to database]")
    print("=" * 80)
    
    # Initialize system
    db = DatabaseManager("test_exact_example.db")
    agent_manager = AgentManager(db, "test_exact_example_session", "openai")
    
    # Show initial state
    print(f"\n🎯 Initial State:")
    print(f"Current Agent: {agent_manager.get_current_agent_name()}")
    print(f"Session ID: {agent_manager.session_id}")
    
    # Step 1: User says "I need 10 wooden desks."
    print("\n" + "="*80)
    print("🎬 STARTING CONVERSATION")
    print("="*80)
    
    user_input_1 = "I need 10 wooden desks."
    print(f"👤 User: {user_input_1}")
    
    # Process through agent manager
    response_1 = agent_manager.process_message(user_input_1)
    current_agent_1 = agent_manager.get_current_agent_name()
    print_conversation_step(1, user_input_1, response_1, current_agent_1)
    
    # Step 2: User provides title "Wooden Desk Order"
    user_input_2 = "Wooden Desk Order"
    print(f"\n👤 User: {user_input_2}")
    
    response_2 = agent_manager.process_message(user_input_2)
    current_agent_2 = agent_manager.get_current_agent_name()
    print_conversation_step(2, user_input_2, response_2, current_agent_2)
    
    # Step 3: User describes the request
    user_input_3 = "10 wooden desks for the new conference room."
    print(f"\n👤 User: {user_input_3}")
    
    response_3 = agent_manager.process_message(user_input_3)
    current_agent_3 = agent_manager.get_current_agent_name()
    print_conversation_step(3, user_input_3, response_3, current_agent_3)
    
    # Step 4: Continue with Generic Order Agent (brand preference)
    user_input_4 = "Yes, from UrbanCraft."
    print(f"\n👤 User: {user_input_4}")
    
    response_4 = agent_manager.process_message(user_input_4)
    current_agent_4 = agent_manager.get_current_agent_name()
    print_conversation_step(4, user_input_4, response_4, current_agent_4)
    
    # Step 5: Confirm the order
    user_input_5 = "Yes"
    print(f"\n👤 User: {user_input_5}")
    
    response_5 = agent_manager.process_message(user_input_5)
    current_agent_5 = agent_manager.get_current_agent_name()
    print_conversation_step(5, user_input_5, response_5, current_agent_5)
    
    # Final Analysis
    print("\n" + "="*80)
    print("📊 FINAL ANALYSIS")
    print("="*80)
    
    # Check final agent
    final_agent = agent_manager.get_current_agent_name()
    print(f"🎯 Final Agent: {final_agent}")
    
    # Check if order was saved
    try:
        orders = db.get_orders_by_session(agent_manager.session_id)
        print(f"📦 Orders Created: {len(orders)}")
        
        if orders:
            print("\n📋 Order Details:")
            for i, order in enumerate(orders, 1):
                print(f"Order {i}:")
                print(f"  - Title: {order['title']}")
                print(f"  - Description: {order['description']}")
                print(f"  - Product: {order['product_name']}")
                print(f"  - Quantity: {order['quantity']}")
                print(f"  - Brand Preference: {order['brand_preference']}")
                print(f"  - Created: {order['created_at']}")
        else:
            print("❌ No orders were created!")
            
    except Exception as e:
        print(f"❌ Error retrieving orders: {e}")
    
    # Check conversation history
    try:
        conversations = db.get_conversation_history(agent_manager.session_id)
        print(f"\n💬 Conversation Logs: {len(conversations)}")
        
        if conversations:
            print("\n📝 Recent Conversations:")
            for i, conv in enumerate(conversations[:5], 1):
                print(f"  {i}. [{conv['agent']}] User: {conv['user_input'][:50]}...")
                print(f"     Bot: {conv['chatbot_response'][:50]}...")
                
    except Exception as e:
        print(f"❌ Error retrieving conversations: {e}")
    
    # Verify the flow worked as expected
    print("\n" + "="*80)
    print("✅ VERIFICATION CHECKLIST")
    print("="*80)
    
    checks = [
        ("Orchestrator Agent started", agent_manager.get_context().get('current_agent') == "Orchestrator" or "Orchestrator" in str(conversations)),
        ("Title collected", any("Wooden Desk Order" in conv['user_input'] for conv in conversations)),
        ("Description collected", any("10 wooden desks for the new conference room" in conv['user_input'] for conv in conversations)),
        ("Classification happened", any("generic" in conv['chatbot_response'].lower() for conv in conversations)),
        ("Handoff to Generic Agent", any("Generic" in conv['agent'] for conv in conversations)),
        ("Brand preference collected", any("UrbanCraft" in conv['user_input'] for conv in conversations)),
        ("Order confirmed", any("confirmed and saved" in conv['chatbot_response'].lower() for conv in conversations)),
        ("Final output generated", any("📋 **Final Output:**" in conv['chatbot_response'] for conv in conversations)),
        ("Order saved to database", len(orders) > 0),
        ("Returned to Orchestrator", final_agent == "Orchestrator")
    ]
    
    passed_checks = 0
    for check_name, check_result in checks:
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if check_result:
            passed_checks += 1
    
    print(f"\n📊 Overall Result: {passed_checks}/{len(checks)} checks passed")
    
    if passed_checks == len(checks):
        print("🎉 SUCCESS: All checks passed! The system works exactly as specified.")
    else:
        print("⚠️  Some checks failed. Please review the conversation flow.")
    
    # Cleanup
    try:
        os.remove("test_exact_example.db")
        print("\n🧹 Test database cleaned up")
    except Exception as e:
        print(f"\n⚠️  Could not clean up test database: {e}")
    
    return passed_checks == len(checks)

def main():
    """Main function to run the test"""
    print("🧪 Multi-Agent Chatbot System - Exact Example Flow Test")
    print("=" * 80)
    
    try:
        success = test_exact_example_flow()
        
        if success:
            print("\n🎯 TEST SUMMARY:")
            print("✅ The system successfully followed your exact conversation flow")
            print("✅ Orchestrator Agent collected title and description")
            print("✅ Category classification worked correctly")
            print("✅ Agent handoff to Generic Order Agent was smooth")
            print("✅ Brand preference was collected")
            print("✅ Order was confirmed and saved")
            print("✅ Final output in JSON format was generated")
            print("✅ System returned to Orchestrator for new orders")
        else:
            print("\n❌ TEST SUMMARY:")
            print("Some aspects of the conversation flow did not work as expected")
            print("Please review the verification checklist above")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
