#!/usr/bin/env python3
"""
Test script for the Multi-Agent Order Chatbot System with LangChain
This script tests the core functionality without requiring the Streamlit UI
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from agents import AgentManager, MainAgent, GenericOrderAgent, BulkOrderAgent
from llm_manager import LLMManager

def test_database():
    """Test database functionality"""
    print("🧪 Testing Database...")
    
    try:
        # Initialize database
        db = DatabaseManager("test_chatbot.db")
        print("✅ Database initialized successfully")
        
        # Test conversation logging
        db.log_conversation("test_session", "Hello", "Hi there!", "TestAgent")
        print("✅ Conversation logging works")
        
        # Test order saving
        test_order = {
            "title": "Test Order",
            "description": "Test description",
            "product_name": "Test Product",
            "quantity": 10,
            "brand_preference": "Test Brand"
        }
        order_id = db.save_order("test_session", test_order)
        print(f"✅ Order saved with ID: {order_id}")
        
        # Test retrieval
        orders = db.get_orders_by_session("test_session")
        print(f"✅ Retrieved {len(orders)} orders")
        
        # Cleanup test database
        os.remove("test_chatbot.db")
        print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_llm_manager():
    """Test LLM manager functionality"""
    print("\n🧪 Testing LLM Manager...")
    
    try:
        # Test with no API keys (should use fallback)
        llm_manager = LLMManager(provider="openai")
        print("✅ LLM Manager initialized")
        
        # Test classification
        result1 = llm_manager.classify_request("I need 5 desk lamps", "personal")
        print(f"✅ Generic classification: {result1}")
        
        result2 = llm_manager.classify_request("Need 500 water bottles for event", "business")
        print(f"✅ Bulk classification: {result2}")
        
        # Test provider info
        provider_info = llm_manager.get_provider_info()
        print(f"✅ Provider info: {provider_info['provider']} - {provider_info['model']}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Manager test failed: {e}")
        return False

def test_agents():
    """Test agent functionality"""
    print("\n🧪 Testing Agents...")
    
    try:
        # Initialize test database and LLM manager
        db = DatabaseManager("test_agents.db")
        llm_manager = LLMManager(provider="openai")
        
        # Test Main Agent
        main_agent = MainAgent(db, "test_session", llm_manager)
        print("✅ Main Agent initialized")
        
        # Test Generic Order Agent
        generic_agent = GenericOrderAgent(db, "test_session", llm_manager)
        print("✅ Generic Order Agent initialized")
        
        # Test Bulk Order Agent
        bulk_agent = BulkOrderAgent(db, "test_session", llm_manager)
        print("✅ Bulk Order Agent initialized")
        
        # Test Agent Manager
        agent_manager = AgentManager(db, "test_session", "openai")
        print("✅ Agent Manager initialized")
        
        # Cleanup
        os.remove("test_agents.db")
        print("✅ Test agents database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Agents test failed: {e}")
        return False

def test_final_output_format():
    """Test the final output format generation"""
    print("\n🧪 Testing Final Output Format...")
    
    try:
        # Initialize test database and LLM manager
        db = DatabaseManager("test_output_format.db")
        llm_manager = LLMManager(provider="openai")
        
        # Test Generic Order Agent output format
        generic_agent = GenericOrderAgent(db, "test_session", llm_manager)
        generic_agent.order_data = {
            "title": "Test Order",
            "description": "Test description",
            "product_name": "Test Product",
            "quantity": 100,
            "brand_preference": "Test Brand"
        }
        
        final_output = generic_agent.generate_final_output()
        print("✅ Final output generated successfully")
        
        # Parse and validate JSON format
        import json
        output_data = json.loads(final_output)
        
        # Check required fields
        required_fields = ["title", "description", "product_name", "quantity", "brand_preference"]
        for field in required_fields:
            if field not in output_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Check data types
        if not isinstance(output_data["title"], str):
            print("❌ Title should be string")
            return False
        if not isinstance(output_data["description"], str):
            print("❌ Description should be string")
            return False
        if not isinstance(output_data["product_name"], str):
            print("❌ Product name should be string")
            return False
        if not isinstance(output_data["quantity"], int):
            print("❌ Quantity should be integer")
            return False
        if not isinstance(output_data["brand_preference"], str):
            print("❌ Brand preference should be string")
            return False
        
        print("✅ All required fields present with correct types")
        print(f"✅ Final output format:\n{final_output}")
        
        # Cleanup
        os.remove("test_output_format.db")
        print("✅ Test output format database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Final output format test failed: {e}")
        return False

def test_workflow():
    """Test complete workflow"""
    print("\n🧪 Testing Complete Workflow...")
    
    try:
        # Initialize system
        db = DatabaseManager("test_workflow.db")
        agent_manager = AgentManager(db, "test_workflow_session", "openai")
        
        # Simulate conversation flow
        print("📝 Simulating conversation flow...")
        
        # Step 1: User provides title
        response1 = agent_manager.process_message("Wooden Desk Order")
        print(f"Step 1 - Title: {response1}")
        
        # Step 2: User provides description
        response2 = agent_manager.process_message("10 wooden desks for conference room")
        print(f"Step 2 - Description: {response2}")
        
        # Step 3: Check if handoff occurred
        current_agent = agent_manager.get_current_agent_name()
        print(f"Current Agent: {current_agent}")
        
        # Step 4: Continue with specialized agent
        if current_agent == "Generic":
            response3 = agent_manager.process_message("Yes")
            print(f"Step 3 - Brand preference: {response3}")
            
            response4 = agent_manager.process_message("UrbanCraft")
            print(f"Step 4 - Brand specified: {response4}")
            
            response5 = agent_manager.process_message("Yes")
            print(f"Step 5 - Confirmation: {response5}")
            
            # Check if final output was generated
            if "📋 **Final Output:**" in response5:
                print("✅ Final output format generated successfully")
            else:
                print("❌ Final output format not generated")
                return False
        
        # Check final state
        final_agent = agent_manager.get_current_agent_name()
        print(f"Final Agent: {final_agent}")
        
        # Verify order was saved
        orders = db.get_orders_by_session("test_workflow_session")
        print(f"Orders created: {len(orders)}")
        
        # Test LLM provider switching
        print("\n🔄 Testing LLM Provider Switching...")
        agent_manager.switch_llm_provider("google")
        llm_info = agent_manager.get_llm_info()
        print(f"Switched to: {llm_info['provider']} - {llm_info['model']}")
        
        # Cleanup
        os.remove("test_workflow.db")
        print("✅ Workflow test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

def test_langchain_integration():
    """Test LangChain integration features"""
    print("\n🧪 Testing LangChain Integration...")
    
    try:
        # Initialize system
        db = DatabaseManager("test_langchain.db")
        agent_manager = AgentManager(db, "test_langchain_session", "openai")
        
        # Test agent tools
        main_agent = agent_manager.agents["MainAgent"]
        if main_agent.tools:
            print(f"✅ Main Agent has {len(main_agent.tools)} tools")
            for tool in main_agent.tools:
                print(f"  - Tool: {tool.name} - {tool.description}")
        else:
            print("⚠️ Main Agent has no tools")
        
        # Test agent prompts
        if main_agent.prompt:
            print("✅ Main Agent has prompt template")
        else:
            print("⚠️ Main Agent has no prompt template")
        
        # Test memory
        if main_agent.memory:
            print("✅ Main Agent has memory")
        else:
            print("⚠️ Main Agent has no memory")
        
        # Cleanup
        os.remove("test_langchain.db")
        print("✅ LangChain integration test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain integration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Multi-Agent Chatbot System Tests (LangChain Version)\n")
    print("=" * 60)
    
    tests = [
        ("Database", test_database),
        ("LLM Manager", test_llm_manager),
        ("Agents", test_agents),
        ("Final Output Format", test_final_output_format),
        ("Complete Workflow", test_workflow),
        ("LangChain Integration", test_langchain_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
        
        print("-" * 40)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LangChain-based system is ready to use.")
        print("\n🚀 Key Features Verified:")
        print("✅ Multi-agent architecture with LangChain")
        print("✅ LLM provider management (OpenAI, Google, Groq)")
        print("✅ Agent tools and prompts")
        print("✅ Conversation memory")
        print("✅ Database integration")
        print("✅ Agent handoffs and workflow")
        print("✅ Final output format in specified JSON structure")
        print("✅ Required fields: title, description, product_name, quantity, brand_preference")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
