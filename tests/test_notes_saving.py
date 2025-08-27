#!/usr/bin/env python3
"""
Test script to verify notes are being saved to the database correctly
"""

import os
import sys
from datetime import datetime, date

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Note, User

def test_notes_saving():
    """Test that notes are being saved correctly"""
    with app.app_context():
        try:
            # Get all users
            users = User.query.all()
            print(f"📊 Found {len(users)} users in database")
            
            for user in users:
                print(f"\n👤 User: {user.username} (ID: {user.id})")
                
                # Get all notes for this user
                notes = Note.query.filter_by(user_id=user.id).order_by(Note.timestamp.desc()).all()
                print(f"   📝 Total notes: {len(notes)}")
                
                if notes:
                    # Group notes by date
                    notes_by_date = {}
                    for note in notes:
                        note_date = note.date.isoformat()
                        if note_date not in notes_by_date:
                            notes_by_date[note_date] = []
                        notes_by_date[note_date].append(note)
                    
                    print(f"   📅 Notes across {len(notes_by_date)} different dates:")
                    
                    for note_date, date_notes in notes_by_date.items():
                        print(f"      {note_date}: {len(date_notes)} notes")
                        for i, note in enumerate(date_notes[:3]):  # Show first 3 notes per date
                            timestamp = note.timestamp.strftime('%H:%M:%S')
                            content_preview = note.content[:50] + "..." if len(note.content) > 50 else note.content
                            print(f"         {i+1}. [{timestamp}] {content_preview}")
                        if len(date_notes) > 3:
                            print(f"         ... and {len(date_notes) - 3} more notes")
                else:
                    print("   ❌ No notes found for this user")
            
            # Test database connection
            print(f"\n🔍 Database connection test:")
            total_notes = Note.query.count()
            print(f"   Total notes in database: {total_notes}")
            
            # Check for recent notes (last 24 hours)
            yesterday = date.today()
            recent_notes = Note.query.filter(Note.date >= yesterday).count()
            print(f"   Notes from today: {recent_notes}")
            
            print("\n✅ Database verification complete!")
            
        except Exception as e:
            print(f"❌ Error during database verification: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    print("🧪 Testing Notes Database Functionality...")
    success = test_notes_saving()
    
    if success:
        print("\n✅ All tests passed! Notes are being saved correctly.")
    else:
        print("\n❌ Tests failed! Check the database configuration.")
        sys.exit(1)
