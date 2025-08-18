#!/usr/bin/env python3
"""
AI Training System for Ki Wellness
Processes PDFs and files to improve AI responses through fine-tuning and RAG
"""

import os
import json
import requests
import ollama
from datetime import datetime
from pathlib import Path
import PyPDF2
import docx
import csv
import sqlite3
from typing import List, Dict, Any
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AITrainingSystem:
    def __init__(self):
        self.model_name = "mistral"  # Base model
        self.fine_tuned_model = "ki-wellness-mistral"  # Custom fine-tuned model
        self.ollama_base_url = "http://localhost:11434"
        self.training_data_dir = Path("training_data")
        self.embeddings_db = "embeddings.db"
        
        # Create directories
        self.training_data_dir.mkdir(exist_ok=True)
        self.processed_dir = self.training_data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self.init_embeddings_db()
    
    def init_embeddings_db(self):
        """Initialize SQLite database for storing embeddings and knowledge base"""
        conn = sqlite3.connect(self.embeddings_db)
        cursor = conn.cursor()
        
        # Create tables for knowledge base
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                embedding TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create table for training examples
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                context TEXT,
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create table for model performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                question TEXT NOT NULL,
                expected_answer TEXT,
                actual_answer TEXT,
                accuracy_score REAL,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_pdf(self, pdf_path: Path) -> List[str]:
        """Extract text content from PDF files"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_chunks = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        # Split into manageable chunks (500-1000 words)
                        chunks = self.split_text_into_chunks(text, max_words=800)
                        for chunk in chunks:
                            text_chunks.append({
                                'content': chunk,
                                'source': f"{pdf_path.name}_page_{page_num + 1}",
                                'type': 'pdf'
                            })
                
                return text_chunks
        except Exception as e:
            print(f"❌ Error processing PDF {pdf_path}: {e}")
            return []
    
    def process_docx(self, docx_path: Path) -> List[str]:
        """Extract text content from DOCX files"""
        try:
            doc = docx.Document(docx_path)
            text_chunks = []
            full_text = ""
            
            for paragraph in doc.paragraphs:
                full_text += paragraph.text + "\n"
            
            if full_text.strip():
                chunks = self.split_text_into_chunks(full_text, max_words=800)
                for chunk in chunks:
                    text_chunks.append({
                        'content': chunk,
                        'source': docx_path.name,
                        'type': 'docx'
                    })
            
            return text_chunks
        except Exception as e:
            print(f"❌ Error processing DOCX {docx_path}: {e}")
            return []
    
    def process_txt(self, txt_path: Path) -> List[str]:
        """Extract text content from TXT files"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                text = file.read()
                chunks = self.split_text_into_chunks(text, max_words=800)
                text_chunks = []
                
                for chunk in chunks:
                    text_chunks.append({
                        'content': chunk,
                        'source': txt_path.name,
                        'type': 'txt'
                    })
                
                return text_chunks
        except Exception as e:
            print(f"❌ Error processing TXT {txt_path}: {e}")
            return []
    
    def split_text_into_chunks(self, text: str, max_words: int = 800) -> List[str]:
        """Split text into manageable chunks for processing"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text using Ollama"""
        try:
            response = ollama.embeddings(
                model=self.model_name,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            return []
    
    def store_knowledge_base(self, chunks: List[Dict[str, Any]]):
        """Store processed chunks in the knowledge base"""
        conn = sqlite3.connect(self.embeddings_db)
        cursor = conn.cursor()
        
        for chunk in chunks:
            content_hash = hashlib.md5(chunk['content'].encode()).hexdigest()
            
            # Check if content already exists
            cursor.execute('SELECT id FROM knowledge_base WHERE content_hash = ?', (content_hash,))
            if cursor.fetchone():
                continue
            
            # Generate embeddings
            embedding = self.generate_embeddings(chunk['content'])
            
            # Store in database
            cursor.execute('''
                INSERT INTO knowledge_base (source_file, content, content_hash, embedding, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                chunk['source'],
                chunk['content'],
                content_hash,
                json.dumps(embedding),
                json.dumps({
                    'type': chunk['type'],
                    'processed_at': datetime.now().isoformat()
                })
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Stored {len(chunks)} chunks in knowledge base")
    
    def process_training_files(self, files_dir: str = "training_files"):
        """Process all training files in the specified directory"""
        files_path = Path(files_dir)
        
        if not files_path.exists():
            print(f"❌ Training files directory '{files_dir}' not found")
            return
        
        all_chunks = []
        
        # Process PDFs
        for pdf_file in files_path.glob("*.pdf"):
            print(f"📄 Processing PDF: {pdf_file.name}")
            chunks = self.process_pdf(pdf_file)
            all_chunks.extend(chunks)
        
        # Process DOCX files
        for docx_file in files_path.glob("*.docx"):
            print(f"📝 Processing DOCX: {docx_file.name}")
            chunks = self.process_docx(docx_file)
            all_chunks.extend(chunks)
        
        # Process TXT files
        for txt_file in files_path.glob("*.txt"):
            print(f"📄 Processing TXT: {txt_file.name}")
            chunks = self.process_txt(txt_file)
            all_chunks.extend(chunks)
        
        # Store in knowledge base
        if all_chunks:
            self.store_knowledge_base(all_chunks)
            print(f"✅ Processed {len(all_chunks)} total chunks from training files")
        else:
            print("❌ No content extracted from training files")
    
    def create_training_dataset(self, qa_pairs: List[Dict[str, str]]):
        """Create training dataset from Q&A pairs"""
        conn = sqlite3.connect(self.embeddings_db)
        cursor = conn.cursor()
        
        for qa in qa_pairs:
            cursor.execute('''
                INSERT INTO training_examples (question, answer, context, source_file)
                VALUES (?, ?, ?, ?)
            ''', (
                qa['question'],
                qa['answer'],
                qa.get('context', ''),
                qa.get('source_file', 'manual')
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Added {len(qa_pairs)} training examples")
    
    def generate_fine_tuning_data(self) -> str:
        """Generate fine-tuning dataset in the format required by Ollama"""
        conn = sqlite3.connect(self.embeddings_db)
        cursor = conn.cursor()
        
        # Get training examples
        cursor.execute('SELECT question, answer, context FROM training_examples')
        examples = cursor.fetchall()
        
        # Format for fine-tuning
        training_data = []
        for question, answer, context in examples:
            training_data.append({
                "prompt": question,
                "response": answer,
                "context": context
            })
        
        # Save to JSON file
        output_file = self.training_data_dir / "fine_tuning_data.json"
        with open(output_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        conn.close()
        print(f"✅ Generated fine-tuning dataset with {len(training_data)} examples")
        return str(output_file)
    
    def fine_tune_model(self, training_data_file: str):
        """Fine-tune the model using the training data"""
        try:
            # Create a Modelfile for fine-tuning
            modelfile_content = f"""
FROM {self.model_name}

# Add training data
TEMPLATE """{{"prompt": "{{.Input}}", "response": "{{.Response}}"}}"""

# Add system prompt for health coaching
SYSTEM """You are an expert AI Health Coach for Ki Wellness. You provide personalized, evidence-based health advice based on user data including nutrition, water intake, mood, and health goals. Always be encouraging, actionable, and specific to the user's situation."""

# Add training examples
{self.generate_modelfile_training_data(training_data_file)}
"""
            
            # Save Modelfile
            modelfile_path = self.training_data_dir / "Modelfile"
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            # Create fine-tuned model
            print("🔄 Creating fine-tuned model...")
            response = requests.post(
                f"{self.ollama_base_url}/api/create",
                json={
                    "name": self.fine_tuned_model,
                    "modelfile": str(modelfile_path)
                }
            )
            
            if response.status_code == 200:
                print(f"✅ Fine-tuned model '{self.fine_tuned_model}' created successfully")
                return True
            else:
                print(f"❌ Error creating fine-tuned model: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during fine-tuning: {e}")
            return False
    
    def generate_modelfile_training_data(self, training_data_file: str) -> str:
        """Generate training data section for Modelfile"""
        with open(training_data_file, 'r') as f:
            data = json.load(f)
        
        modelfile_data = ""
        for example in data[:50]:  # Limit to 50 examples for Modelfile
            prompt = example['prompt'].replace('"', '\\"')
            response = example['response'].replace('"', '\\"')
            modelfile_data += f'TRAIN "{prompt}" "{response}"\n'
        
        return modelfile_data
    
    def retrieve_relevant_context(self, question: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant context from knowledge base using embeddings"""
        try:
            # Generate embedding for the question
            question_embedding = self.generate_embeddings(question)
            
            if not question_embedding:
                return []
            
            # Get all embeddings from knowledge base
            conn = sqlite3.connect(self.embeddings_db)
            cursor = conn.cursor()
            cursor.execute('SELECT content, embedding FROM knowledge_base')
            results = cursor.fetchall()
            conn.close()
            
            # Calculate similarities and find top matches
            similarities = []
            for content, embedding_json in results:
                embedding = json.loads(embedding_json)
                similarity = self.cosine_similarity(question_embedding, embedding)
                similarities.append((similarity, content))
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [content for _, content in similarities[:top_k]]
            
        except Exception as e:
            print(f"❌ Error retrieving context: {e}")
            return []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def enhanced_ai_response(self, question: str, user_data: Dict = None) -> str:
        """Generate enhanced AI response using fine-tuned model and RAG"""
        try:
            # Retrieve relevant context
            context_chunks = self.retrieve_relevant_context(question)
            context = "\n\n".join(context_chunks) if context_chunks else ""
            
            # Build enhanced prompt
            enhanced_prompt = f"""
Context from training materials:
{context}

User Question: {question}

User Data: {json.dumps(user_data, indent=2) if user_data else 'Not provided'}

Please provide a comprehensive, personalized response based on the context and user data.
"""
            
            # Use fine-tuned model if available, otherwise use base model
            try:
                response = ollama.chat(
                    model=self.fine_tuned_model,
                    messages=[{"role": "user", "content": enhanced_prompt}]
                )
            except:
                # Fallback to base model
                response = ollama.chat(
                    model=self.model_name,
                    messages=[{"role": "user", "content": enhanced_prompt}]
                )
            
            return response['message']['content']
            
        except Exception as e:
            print(f"❌ Error generating enhanced response: {e}")
            return "I apologize, but I encountered an error while processing your request."
    
    def evaluate_model_performance(self, test_questions: List[Dict[str, str]]):
        """Evaluate model performance on test questions"""
        print("🔍 Evaluating model performance...")
        
        conn = sqlite3.connect(self.embeddings_db)
        cursor = conn.cursor()
        
        for test in test_questions:
            question = test['question']
            expected_answer = test['expected_answer']
            
            # Generate actual answer
            actual_answer = self.enhanced_ai_response(question)
            
            # Simple accuracy scoring (you can implement more sophisticated metrics)
            accuracy_score = self.calculate_answer_similarity(expected_answer, actual_answer)
            
            # Store performance data
            cursor.execute('''
                INSERT INTO model_performance (model_name, question, expected_answer, actual_answer, accuracy_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.fine_tuned_model,
                question,
                expected_answer,
                actual_answer,
                accuracy_score
            ))
        
        conn.commit()
        conn.close()
        print("✅ Model performance evaluation completed")
    
    def calculate_answer_similarity(self, expected: str, actual: str) -> float:
        """Calculate similarity between expected and actual answers"""
        # Simple word overlap similarity
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            return 0.0
        
        intersection = expected_words.intersection(actual_words)
        return len(intersection) / len(expected_words)

def main():
    """Main function to run the AI training system"""
    print("🚀 Starting AI Training System for Ki Wellness")
    
    # Initialize training system
    trainer = AITrainingSystem()
    
    # Process training files
    print("\n📚 Processing training files...")
    trainer.process_training_files()
    
    # Example training Q&A pairs (you can add your own)
    example_qa_pairs = [
        {
            "question": "How can I improve my water intake?",
            "answer": "To improve water intake, try setting daily goals, using a water bottle with measurements, adding flavor with lemon or cucumber, setting reminders, and tracking your intake. Aim for 8-10 glasses (64-80 oz) per day.",
            "context": "Water intake optimization strategies",
            "source_file": "hydration_guide.pdf"
        },
        {
            "question": "What should I eat for better mood?",
            "answer": "Foods that support better mood include omega-3 rich fish, dark chocolate, berries, nuts, leafy greens, and complex carbohydrates. These foods support serotonin production and brain health.",
            "context": "Nutrition and mental health",
            "source_file": "mood_nutrition.pdf"
        }
    ]
    
    # Add training examples
    print("\n📝 Adding training examples...")
    trainer.create_training_dataset(example_qa_pairs)
    
    # Generate fine-tuning data
    print("\n🔄 Generating fine-tuning dataset...")
    training_data_file = trainer.generate_fine_tuning_data()
    
    # Fine-tune model
    print("\n🎯 Fine-tuning model...")
    success = trainer.fine_tune_model(training_data_file)
    
    if success:
        print("\n✅ AI Training System setup completed successfully!")
        print(f"📊 Fine-tuned model: {trainer.fine_tuned_model}")
        print("🔧 You can now use enhanced_ai_response() for better AI responses")
    else:
        print("\n❌ Fine-tuning failed, but knowledge base is ready")

if __name__ == "__main__":
    main()
