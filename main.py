import streamlit as st
import uuid
from datetime import datetime
import json
from database import DatabaseManager
from agents import AgentManager
from llm_manager import LLMManager
import config

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Order Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
        margin-left: 20%;
    }
    .chat-message.bot {
        background-color: #262730;
        margin-right: 20%;
    }
    .chat-message .content {
        display: flex;
        align-items: center;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        font-size: 1.2rem;
        margin-right: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .agent-badge {
        background-color: #ff6b6b;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        margin-left: 0.5rem;
    }
    .order-summary {
        background-color: #1e1e1e;
        border: 1px solid #444;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .sidebar-section {
        margin-bottom: 2rem;
    }
    .llm-status {
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    .llm-status.success {
        background-color: #28a745;
        color: white;
    }
    .llm-status.warning {
        background-color: #ffc107;
        color: black;
    }
    .llm-status.error {
        background-color: #dc3545;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'agent_manager' not in st.session_state:
        db_manager = DatabaseManager()
        st.session_state.agent_manager = AgentManager(db_manager, st.session_state.session_id)
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'llm_provider' not in st.session_state:
        st.session_state.llm_provider = config.DEFAULT_LLM_PROVIDER

def display_chat_message(message, is_user=False, agent_name=None):
    """Display a chat message with proper styling"""
    if is_user:
        st.markdown(f"""
        <div class="chat-message user">
            <div class="content">
                <div class="avatar">👤</div>
                <div>
                    <strong>You</strong>
                    <div>{message}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        agent_emoji = "🤖"
        if agent_name == "Orchestrator":
            agent_emoji = "🎯"
        elif agent_name == "Generic":
            agent_emoji = "📦"
        elif agent_name == "Bulk":
            agent_emoji = "📊"
        
        st.markdown(f"""
        <div class="chat-message bot">
            <div class="content">
                <div class="avatar">{agent_emoji}</div>
                <div>
                    <strong>Bot</strong>
                    <span class="agent-badge">{agent_name or 'System'}</span>
                    <div>{message}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_order_summary(order_data):
    """Display order summary in a formatted way"""
    st.markdown("""
    <div class="order-summary">
        <h4>📋 Order Summary</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Title:** {order_data.get('title', 'N/A')}")
        st.write(f"**Description:** {order_data.get('description', 'N/A')}")
        st.write(f"**Product:** {order_data.get('product_name', 'N/A')}")
    
    with col2:
        st.write(f"**Quantity:** {order_data.get('quantity', 'N/A')}")
        st.write(f"**Brand/Supplier:** {order_data.get('brand_preference', 'None')}")
        st.write(f"**Type:** {order_data.get('order_type', 'N/A')}")

def display_llm_status(llm_info):
    """Display LLM provider status"""
    if llm_info['available']:
        status_class = "success"
        status_text = f"✅ {llm_info['provider'].title()} - {llm_info['model']}"
    elif llm_info['api_key_configured']:
        status_class = "warning"
        status_text = f"⚠️ {llm_info['provider'].title()} - API Key configured but LLM unavailable"
    else:
        status_class = "error"
        status_text = f"❌ {llm_info['provider'].title()} - No API Key configured"
    
    st.markdown(f"""
    <div class="llm-status {status_class}">
        {status_text}
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""
    st.title("🤖 Multi-Agent Order Chatbot System")
    st.markdown("---")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard")
        
        # Session info
        with st.expander("Session Information", expanded=True):
            st.write(f"**Session ID:** {st.session_state.session_id[:8]}...")
            st.write(f"**Current Agent:** {st.session_state.agent_manager.get_current_agent_name()}")
            st.write(f"**Status:** Active")
        
        # LLM Configuration
        with st.expander("🤖 LLM Configuration", expanded=True):
            # LLM Provider Selection
            llm_provider = st.selectbox(
                "Select LLM Provider:",
                ["openai", "google", "groq"],
                index=["openai", "google", "groq"].index(st.session_state.llm_provider)
            )
            
            if llm_provider != st.session_state.llm_provider:
                st.session_state.llm_provider = llm_provider
                st.session_state.agent_manager.switch_llm_provider(llm_provider)
                st.rerun()
            
            # Display LLM Status
            llm_info = st.session_state.agent_manager.get_llm_info()
            display_llm_status(llm_info)
            
            # API Key Status
            if llm_provider == "openai":
                if config.OPENAI_API_KEY:
                    st.success("✅ OpenAI API Key configured")
                else:
                    st.warning("⚠️ OpenAI API Key not configured")
            elif llm_provider == "google":
                if config.GOOGLE_AI_API_KEY:
                    st.success("✅ Google AI API Key configured")
                else:
                    st.warning("⚠️ Google AI API Key not configured")
            elif llm_provider == "groq":
                if config.GROQ_API_KEY:
                    st.success("✅ Groq API Key configured")
                else:
                    st.warning("⚠️ Groq API Key not configured")
        
        # Database stats
        with st.expander("Database Statistics", expanded=True):
            try:
                all_orders = st.session_state.db_manager.get_all_orders()
                st.write(f"**Total Orders:** {len(all_orders)}")
                
                session_orders = st.session_state.db_manager.get_orders_by_session(st.session_state.session_id)
                st.write(f"**Session Orders:** {len(session_orders)}")
                
                if st.button("View All Orders"):
                    st.session_state.show_all_orders = True
            except Exception as e:
                st.error(f"Database error: {e}")
        
        # Quick actions
        with st.expander("Quick Actions", expanded=True):
            if st.button("🔄 Start New Order"):
                st.session_state.agent_manager = AgentManager(
                    st.session_state.db_manager, 
                    str(uuid.uuid4()),
                    st.session_state.llm_provider
                )
                st.session_state.session_id = st.session_state.agent_manager.session_id
                st.session_state.chat_history = []
                st.rerun()
            
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        # LangChain Configuration
        with st.expander("🔗 LangChain Settings", expanded=False):
            st.write("**Tracing:**", "Enabled" if config.LANGCHAIN_TRACING_V2 else "Disabled")
            st.write("**Project:**", config.LANGCHAIN_PROJECT)
            if config.LANGCHAIN_ENDPOINT:
                st.write("**Endpoint:**", config.LANGCHAIN_ENDPOINT)

    # Main chat area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat Interface")
        
        # Display chat history
        for message in st.session_state.chat_history:
            display_chat_message(
                message['content'], 
                is_user=message['is_user'],
                agent_name=message.get('agent_name')
            )
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Add user message to chat history
            st.session_state.chat_history.append({
                'content': user_input,
                'is_user': True,
                'timestamp': datetime.now(),
                'agent_name': None
            })
            
            # Process message through agent manager
            try:
                response = st.session_state.agent_manager.process_message(user_input)
                current_agent = st.session_state.agent_manager.get_current_agent_name()
                
                # Add bot response to chat history
                st.session_state.chat_history.append({
                    'content': response,
                    'is_user': False,
                    'timestamp': datetime.now(),
                    'agent_name': current_agent
                })
                
                # Rerun to display new messages
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing message: {e}")
                st.session_state.chat_history.append({
                    'content': f"Sorry, I encountered an error: {e}",
                    'is_user': False,
                    'timestamp': datetime.now(),
                    'agent_name': 'System'
                })
                st.rerun()
    
    with col2:
        st.subheader("📋 Current Order")
        
        # Display current order context
        context = st.session_state.agent_manager.get_context()
        order_data = context.get('order_data', {})
        
        if order_data:
            display_order_summary(order_data)
            
            # Show current state
            st.write(f"**Current State:** {context.get('state', 'N/A')}")
            st.write(f"**Agent:** {context.get('current_agent', 'N/A')}")
        else:
            st.info("No active order. Start by providing an order title!")
        
        # Recent orders for this session
        st.subheader("📦 Session Orders")
        try:
            session_orders = st.session_state.db_manager.get_orders_by_session(st.session_state.session_id)
            if session_orders:
                for i, order in enumerate(session_orders[:5]):  # Show last 5 orders
                    with st.expander(f"Order {i+1}: {order['title']}", expanded=False):
                        st.write(f"**Product:** {order['product_name']}")
                        st.write(f"**Quantity:** {order['quantity']}")
                        st.write(f"**Created:** {order['created_at']}")
            else:
                st.info("No orders in this session yet.")
        except Exception as e:
            st.error(f"Error loading orders: {e}")
        
        # LangChain Agent Info
        st.subheader("🔗 LangChain Agents")
        try:
            llm_info = st.session_state.agent_manager.get_llm_info()
            st.write(f"**Provider:** {llm_info['provider'].title()}")
            st.write(f"**Model:** {llm_info['model']}")
            st.write(f"**Status:** {'🟢 Active' if llm_info['available'] else '🔴 Inactive'}")
        except Exception as e:
            st.error(f"Error getting LLM info: {e}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Multi-Agent Order Chatbot System | Built with Streamlit, LangChain & Python</p>
        <p>🤖 Orchestrator Agent | 📦 Generic Order Agent | 📊 Bulk Order Agent</p>
        <p>🔗 Powered by LangChain Framework</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
