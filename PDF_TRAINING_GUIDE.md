# 📚 PDF Training Guide for Ki Wellness AI

This guide will walk you through training your AI model with PDFs to create a personalized health coaching assistant.

## 🚀 Quick Start

### Step 1: Prepare Your PDFs
1. **Add your PDFs** to the `training_files` directory:
   ```bash
   # Copy PDFs from Downloads
   cp ~/Downloads/*.pdf training_files/
   
   # Or move them from another location
   mv /path/to/your/pdfs/*.pdf training_files/
   ```

2. **Supported file types:**
   - 📄 PDF files (`.pdf`)
   - 📝 Word documents (`.docx`)
   - 📄 Text files (`.txt`)

### Step 2: Start Ollama
Make sure Ollama is running:
```bash
ollama serve
```

### Step 3: Run the Training Script
```bash
python train_with_pdfs.py
```

## 📋 Detailed Process

### What Happens During Training

1. **📚 File Processing**
   - Extracts text from your PDFs
   - Splits content into manageable chunks
   - Creates embeddings for each chunk

2. **🧠 Knowledge Base Creation**
   - Stores processed content in a database
   - Enables semantic search for relevant information
   - Links content to source files

3. **🎯 Model Fine-tuning**
   - Creates training examples from your content
   - Fine-tunes the Mistral model with your data
   - Creates a custom `ki-wellness-mistral` model

4. **✅ Testing & Validation**
   - Tests the fine-tuned model
   - Provides sample responses
   - Validates training success

### Interactive Features

The training script will:
- ✅ Check if Ollama is running
- ✅ Verify your training files exist
- ✅ Process all your PDFs automatically
- ❓ Ask if you want to add custom Q&A pairs
- 🧪 Test the model after training

## 📊 Expected Output

After successful training, you'll see:
```
✅ Training completed successfully!
📊 Your fine-tuned model: ki-wellness-mistral
🔧 You can now use the enhanced AI responses in your application
```

## 🔧 Using Your Trained Model

### In Your Application
```python
from ai_training_system import AITrainingSystem

# Initialize the trained system
trainer = AITrainingSystem()

# Get enhanced responses
response = trainer.enhanced_ai_response("How can I improve my nutrition?")
print(response)
```

### Enhanced Features
- **Context-aware responses** based on your PDF content
- **Personalized health advice** using your training data
- **Semantic search** through your knowledge base
- **Improved accuracy** for health-related questions

## 📁 File Structure

After training, you'll have:
```
ki_wellness/
├── training_files/          # Your PDFs here
├── training_data/           # Generated training data
│   ├── fine_tuning_data.json
│   └── Modelfile
├── embeddings.db            # Knowledge base
└── train_with_pdfs.py       # Training script
```

## 🛠️ Troubleshooting

### Common Issues

1. **"Ollama not running"**
   ```bash
   ollama serve
   ```

2. **"No training files found"**
   - Add PDFs to `training_files/` directory
   - Check file extensions (.pdf, .docx, .txt)

3. **"Training failed"**
   - Check Ollama is running
   - Verify PDFs are readable
   - Check available disk space

### Getting Help

If you encounter issues:
1. Check the error messages in the terminal
2. Verify all prerequisites are met
3. Ensure your PDFs are not corrupted
4. Check that Ollama has enough memory

## 🎯 Best Practices

### For Better Training Results

1. **Quality PDFs**
   - Use high-quality, text-based PDFs
   - Avoid scanned images without OCR
   - Ensure content is relevant to health/wellness

2. **Content Variety**
   - Include different types of health content
   - Mix nutrition, exercise, mental health topics
   - Add both general and specific advice

3. **Regular Updates**
   - Retrain periodically with new content
   - Update Q&A pairs based on user feedback
   - Monitor model performance

## 📈 Monitoring Performance

The system tracks:
- Training examples added
- Model accuracy scores
- Response quality metrics
- Knowledge base size

Check the database for performance data:
```python
import sqlite3
conn = sqlite3.connect('embeddings.db')
# Query training_examples and model_performance tables
```

---

**Ready to train?** Add your PDFs to `training_files/` and run `python train_with_pdfs.py`!
