import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_add_recipes():
    """Add recipe tables to the database"""
    print("🔄 Starting recipe tables migration...")
    
    # Database connection
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
    else:
        db_url = 'sqlite:///ki_wellness.db'
    
    engine = create_engine(db_url)
    
    # SQL statements to create recipe tables
    sql_statements = [
        # Recipe table
        """
        CREATE TABLE IF NOT EXISTS recipe (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            servings INTEGER DEFAULT 1,
            prep_time INTEGER,
            cook_time INTEGER,
            difficulty VARCHAR(20),
            category VARCHAR(50),
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE
        )
        """,
        
        # Recipe ingredient table
        """
        CREATE TABLE IF NOT EXISTS recipe_ingredient (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL,
            food_name VARCHAR(200) NOT NULL,
            amount FLOAT NOT NULL,
            unit VARCHAR(50) NOT NULL,
            calories FLOAT DEFAULT 0,
            protein FLOAT DEFAULT 0,
            carbs FLOAT DEFAULT 0,
            fat FLOAT DEFAULT 0,
            fiber FLOAT DEFAULT 0,
            sugar FLOAT DEFAULT 0,
            sodium FLOAT DEFAULT 0,
            food_id INTEGER,
            FOREIGN KEY (recipe_id) REFERENCES recipe (id) ON DELETE CASCADE,
            FOREIGN KEY (food_id) REFERENCES food_log (id) ON DELETE SET NULL
        )
        """,
        
        # Recipe instruction table
        """
        CREATE TABLE IF NOT EXISTS recipe_instruction (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            instruction TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipe (id) ON DELETE CASCADE
        )
        """,
        
        # Indexes for performance
        "CREATE INDEX IF NOT EXISTS idx_recipe_user_id ON recipe(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_recipe_category ON recipe(category)",
        "CREATE INDEX IF NOT EXISTS idx_recipe_ingredient_recipe_id ON recipe_ingredient(recipe_id)",
        "CREATE INDEX IF NOT EXISTS idx_recipe_instruction_recipe_id ON recipe_instruction(recipe_id)"
    ]
    
    try:
        with engine.connect() as conn:
            for i, statement in enumerate(sql_statements, 1):
                print(f"  📝 Executing statement {i}/{len(sql_statements)}...")
                conn.execute(text(statement))
            conn.commit()
        
        print("✅ Recipe tables created successfully!")
        print("📊 Tables created:")
        print("   - recipe (main recipe table)")
        print("   - recipe_ingredient (recipe ingredients)")
        print("   - recipe_instruction (cooking instructions)")
        print("   - Performance indexes")
        
    except Exception as e:
        print(f"❌ Error creating recipe tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_add_recipes()
