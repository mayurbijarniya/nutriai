# database.py - MongoDB Atlas Database Manager - VERCEL FIXED VERSION
import os
from pymongo import MongoClient
from datetime import datetime
import json
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING

# Load environment variables
load_dotenv()

class MongoDBManager:
    def __init__(self):
        # Get connection string from environment variable
        self.connection_string = os.getenv('MONGODB_URI')
        print(f"MongoDB URI exists: {bool(self.connection_string)}")
        
        if not self.connection_string:
            print("MONGODB_URI not found in environment variables!")
            self.client = None
            self.db = None
            return
        
        # Print partial URI for debugging (hide password)
        uri_parts = self.connection_string.split('@')
        if len(uri_parts) > 1:
            print(f"Connecting to: ...@{uri_parts[1][:50]}...")
        
        try:
            # Create MongoDB client with explicit timeout settings
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=10000,  # 10 seconds timeout
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=10,
                retryWrites=True
            )
            
            # Set database and collection
            self.db = self.client.diet_designer
            self.collection = self.db.analysis_history
            # Additional collections
            self.users = self.db.users
            self.logins = self.db.logins
            self.usage = self.db.usage  # Usage tracking
            self.share_links = self.db.share_links  # Shareable analysis links
            self.hydration_logs = self.db.hydration_logs  # Water intake per user/day

            # V3 feature collections
            self.meal_logs = self.db.meal_logs
            self.food_items = self.db.food_items
            self.barcode_cache = self.db.barcode_cache
            self.recipes = self.db.recipes
            self.meal_plans = self.db.meal_plans
            self.grocery_lists = self.db.grocery_lists
            self.weight_logs = self.db.weight_logs
            self.chat_sessions = self.db.chat_sessions
            self.challenges = self.db.challenges
            self.challenge_members = self.db.challenge_members
            self.activity_integrations = self.db.activity_integrations
            self.notification_settings = self.db.notification_settings
            self.migration_state = self.db.migration_state
            
            # User Profile collections
            self.user_profiles = self.db.user_profiles
            self.nutrition_goals = self.db.nutrition_goals
            self.diet_preferences = self.db.diet_preferences

            # Ensure indexes
            try:
                # User indexes
                self.users.create_index([('email', ASCENDING)], unique=True, sparse=True)
                self.users.create_index([('google_sub', ASCENDING)], unique=True, sparse=True)
                
                # Analysis indexes
                self.collection.create_index([('created_at', ASCENDING)])
                self.collection.create_index([('user_id', ASCENDING)])
                self.collection.create_index([('guest_session_id', ASCENDING)])
                
                # Login tracking indexes
                self.logins.create_index([('when', ASCENDING)])
                
                # Usage tracking indexes (compound index for scope + date)
                self.usage.create_index([('scope', ASCENDING), ('date', ASCENDING)], unique=True)
                
                # Share links indexes
                self.share_links.create_index([('token', ASCENDING)], unique=True)
                self.share_links.create_index([('user_id', ASCENDING), ('is_active', ASCENDING)])
                self.share_links.create_index([('expires_at', ASCENDING)])  # For cleanup
                
                # User Profile indexes
                self.user_profiles.create_index([('user_id', ASCENDING)], unique=True)
                self.nutrition_goals.create_index([('user_id', ASCENDING)])
                self.diet_preferences.create_index([('user_id', ASCENDING)], unique=True)
                # Hydration indexes
                self.hydration_logs.create_index([('user_id', ASCENDING), ('date', ASCENDING)], unique=True)

                # V3 indexes
                self.meal_logs.create_index([('user_id', ASCENDING), ('logged_at', DESCENDING)])
                self.meal_logs.create_index([('source', ASCENDING), ('created_at', DESCENDING)])
                self.meal_logs.create_index([('schema_version', ASCENDING)])

                self.food_items.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])

                self.barcode_cache.create_index([('barcode', ASCENDING)], unique=True)
                self.barcode_cache.create_index([('updated_at', DESCENDING)])

                self.recipes.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])
                self.recipes.create_index([('is_public', ASCENDING), ('diet_tags', ASCENDING)])

                self.meal_plans.create_index([('user_id', ASCENDING), ('week_start', ASCENDING)], unique=True)
                self.grocery_lists.create_index([('user_id', ASCENDING), ('week_start', ASCENDING)], unique=True)

                self.weight_logs.create_index([('user_id', ASCENDING), ('date', ASCENDING)], unique=True)
                self.weight_logs.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])

                self.chat_sessions.create_index([('user_id', ASCENDING), ('updated_at', DESCENDING)])

                self.challenges.create_index([('is_active', ASCENDING), ('created_at', DESCENDING)])
                self.challenges.create_index([('created_by', ASCENDING), ('created_at', DESCENDING)])

                self.challenge_members.create_index([('challenge_id', ASCENDING), ('user_id', ASCENDING)], unique=True)
                self.challenge_members.create_index([('user_id', ASCENDING), ('joined_at', DESCENDING)])

                self.activity_integrations.create_index([('user_id', ASCENDING), ('provider', ASCENDING)], unique=True)
                self.notification_settings.create_index([('user_id', ASCENDING)], unique=True)

                self.migration_state.create_index([('name', ASCENDING)], unique=True)
            except Exception as e:
                print(f"Index creation warning: {e}")
            
            # Test connection with ping
            print("Testing MongoDB connection...")
            self.client.admin.command('ping')
            print("Connected to MongoDB Atlas successfully!")
            
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # More detailed error info
            if "authentication failed" in str(e).lower():
                print("Authentication issue - check username/password in MongoDB URI")
            elif "timeout" in str(e).lower():
                print("Connection timeout - check network/firewall settings")
            elif "dns" in str(e).lower():
                print("DNS resolution issue - check MongoDB cluster hostname")
            
            self.client = None
            self.db = None
    
    def is_connected(self):
        """Check if database is connected"""
        if not self.client:
            return False
        try:
            self.client.admin.command('ping')
            return True
        except:
            return False
    
    def save_analysis(self, analysis_data):
        """Save analysis to MongoDB"""
        if not self.client:
            return {"success": False, "error": "Database not connected"}
        
        try:
            # Add timestamp if not present (UTC)
            if 'timestamp' not in analysis_data:
                analysis_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Add created_at for sorting (UTC)
            analysis_data['created_at'] = datetime.utcnow()

            # Ensure ownership fields exist (nullable)
            analysis_data.setdefault('user_id', None)
            analysis_data.setdefault('guest_session_id', None)
            
            print(f"Attempting to save analysis to MongoDB...")
            
            # Insert document
            result = self.collection.insert_one(analysis_data)
            
            print(f"Analysis saved with ID: {result.inserted_id}")
            return {"success": True, "id": str(result.inserted_id)}
            
        except Exception as e:
            print(f"Save error: {e}")
            print(f"Error type: {type(e).__name__}")
            return {"success": False, "error": str(e)}
    
    def get_history(self, limit=20):
        """Get analysis history from MongoDB"""
        if not self.client:
            print("Database not connected, returning empty history")
            return []
        
        try:
            print(f"Attempting to retrieve {limit} analyses...")
            
            # Get documents sorted by created_at (newest first)
            cursor = self.collection.find().sort("created_at", -1).limit(limit)
            
            # Convert to list and handle ObjectId serialization
            history = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc['_id'] = str(doc['_id'])
                
                # Ensure timestamp is in the format expected by templates
                if 'created_at' in doc:
                    doc['timestamp'] = doc['created_at'].isoformat()
                
                history.append(doc)
            
            print(f"Retrieved {len(history)} analyses from database")
            return history
            
        except Exception as e:
            print(f"History retrieval error: {e}")
            print(f"Error type: {type(e).__name__}")
            return []
    
    def delete_analysis(self, analysis_id):
        """Delete specific analysis by MongoDB ObjectId"""
        if not self.client:
            return {"success": False, "error": "Database not connected"}
        
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(analysis_id)
            
            # Delete document
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                print(f"Deleted analysis with ID: {analysis_id}")
                return {"success": True, "message": "Analysis deleted successfully"}
            else:
                return {"success": False, "error": "Analysis not found"}
                
        except Exception as e:
            print(f"Delete error: {e}")
            return {"success": False, "error": str(e)}
    
    def clear_all_history(self):
        """Clear all analysis history"""
        if not self.client:
            return {"success": False, "error": "Database not connected"}
        
        try:
            # Delete all documents
            result = self.collection.delete_many({})
            
            print(f"Cleared {result.deleted_count} analyses from database")
            return {"success": True, "message": f"Cleared {result.deleted_count} analyses"}
            
        except Exception as e:
            print(f"Clear history error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stats(self):
        """Get database statistics"""
        if not self.client:
            return {"error": "Database not connected"}
        
        try:
            total_analyses = self.collection.count_documents({})
            
            stats = {
                "total_analyses": total_analyses,
                "connected": True
            }
            
            # Only get advanced stats if we have data
            if total_analyses > 0:
                try:
                    db_stats = self.db.command("dbStats")
                    stats["database_size"] = db_stats.get("dataSize", 0)
                    
                    coll_stats = self.db.command("collStats", "analysis_history")
                    stats["collection_size"] = coll_stats.get("size", 0)
                except:
                    # Advanced stats failed, but basic stats work
                    pass
            
            return stats
            
        except Exception as e:
            print(f"Stats error: {e}")
            return {"error": str(e), "connected": False}

# Global database instance
db_manager = None

def get_db():
    """Get database manager instance"""
    global db_manager
    if db_manager is None:
        print("Initializing MongoDB connection...")
        db_manager = MongoDBManager()
    return db_manager
