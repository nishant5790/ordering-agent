import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import config

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_input TEXT NOT NULL,
                    chatbot_response TEXT NOT NULL,
                    agent TEXT NOT NULL
                )
            ''')
            
            # Create orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    brand_preference TEXT,
                    additional_details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def log_conversation(self, session_id: str, user_input: str, chatbot_response: str, agent: str):
        """Log a conversation interaction"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (session_id, user_input, chatbot_response, agent)
                VALUES (?, ?, ?, ?)
            ''', (session_id, user_input, chatbot_response, agent))
            conn.commit()
    
    def save_order(self, session_id: str, order_data: Dict[str, Any]):
        """Save an order to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert additional_details to JSON string if it's a dict
            additional_details = json.dumps(order_data.get('additional_details', {}))
            
            cursor.execute('''
                INSERT INTO orders (session_id, title, description, product_name, quantity, 
                                 brand_preference, additional_details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                order_data['title'],
                order_data['description'],
                order_data['product_name'],
                order_data['quantity'],
                order_data.get('brand_preference', ''),
                additional_details
            ))
            conn.commit()
            
            return cursor.lastrowid
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_input, chatbot_response, agent, timestamp
                FROM conversations 
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (session_id, limit))
            
            rows = cursor.fetchall()
            return [
                {
                    'user_input': row[0],
                    'chatbot_response': row[1],
                    'agent': row[2],
                    'timestamp': row[3]
                }
                for row in rows
            ]
    
    def get_orders_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all orders for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, description, product_name, quantity, brand_preference, 
                       additional_details, created_at
                FROM orders 
                WHERE session_id = ?
                ORDER BY created_at DESC
            ''', (session_id,))
            
            rows = cursor.fetchall()
            return [
                {
                    'title': row[0],
                    'description': row[1],
                    'product_name': row[2],
                    'quantity': row[3],
                    'brand_preference': row[4],
                    'additional_details': json.loads(row[5]) if row[5] else {},
                    'created_at': row[6]
                }
                for row in rows
            ]
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_id, title, description, product_name, quantity, 
                       brand_preference, additional_details, created_at
                FROM orders 
                ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            return [
                {
                    'session_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'product_name': row[3],
                    'quantity': row[4],
                    'brand_preference': row[5],
                    'additional_details': json.loads(row[6]) if row[6] else {},
                    'created_at': row[7]
                }
                for row in rows
            ]
