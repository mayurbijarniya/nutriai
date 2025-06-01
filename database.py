# database.py - MongoDB Atlas Database Manager
import os
from pymongo import MongoClient
from datetime import datetime
import json
from bson import ObjectId

class MongoDBManager:
    def __init__(self):
        # Get connection string from environment variable
        self.connection_string = os.getenv('MONGODB_URI')
        if not self.connection_string:
            print("⚠️ Warning: MONGODB_URI not found in environment variables!")
            self.client = None
            self.db = None
        else:
            try:
                self.client = MongoClient(self.connection_string)
                self.db = self.client.diet_designer
                self.collection = self.db.analysis_history
                
                # Test connection
                self.client.admin.command('ping')
                print("✅ Connected to MongoDB Atlas successfully!")
                
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
                self.client = None
                self.db = None
    
    def save_analysis(self, analysis_data):
        """Save analysis to MongoDB"""
        if not self.client:
            return {"success": False, "error": "Database not connected"}
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in analysis_data:
                analysis_data['timestamp'] = datetime.now().isoformat()
            
            # Add created_at for sorting
            analysis_data['created_at'] = datetime.now()
            
            # Insert document
            result = self.collection.insert_one(analysis_data)
            
            print(f"💾 Analysis saved with ID: {result.inserted_id}")
            return {"success": True, "id": str(result.inserted_id)}
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_history(self, limit=20):
        """Get analysis history from MongoDB"""
        if not self.client:
            print("⚠️ Database not connected, returning empty history")
            return []
        
        try:
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
            
            print(f"📚 Retrieved {len(history)} analyses from database")
            return history
            
        except Exception as e:
            print(f"❌ History retrieval error: {e}")
            return []
    
    def delete_analysis(self, analysis_id):
        """Delete specific analysis by MongoDB ObjectId"""
        if not self.client:
            return {"success": False, "error": "Database not connected"}
        
        try:
            # Convert string ID to ObjectId
            from bson import ObjectId
            object_id = ObjectId(analysis_id)
            
            # Delete document
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                print(f"🗑️ Deleted analysis with ID: {analysis_id}")
                return {"success": True, "message": "Analysis deleted successfully"}
            else:
                return {"success": False, "error": "Analysis not found"}
                
        except Exception as e:
            print(f"❌ Delete error: {e}")
            return {"success": False, "error": str(e)}
    
    def clear_all_history(self):
        """Clear all analysis history"""
        if not self.client:
            return {"success": False, "error": "Database not connected"}
        
        try:
            # Delete all documents
            result = self.collection.delete_many({})
            
            print(f"🗑️ Cleared {result.deleted_count} analyses from database")
            return {"success": True, "message": f"Cleared {result.deleted_count} analyses"}
            
        except Exception as e:
            print(f"❌ Clear history error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stats(self):
        """Get database statistics"""
        if not self.client:
            return {}
        
        try:
            stats = {
                "total_analyses": self.collection.count_documents({}),
                "database_size": self.db.command("dbStats")["dataSize"],
                "collection_size": self.db.command("collStats", "analysis_history")["size"] if self.collection.count_documents({}) > 0 else 0
            }
            return stats
        except Exception as e:
            print(f"⚠️ Stats error: {e}")
            return {}

# Global database instance
db_manager = None

def get_db():
    """Get database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = MongoDBManager()
    return db_manager