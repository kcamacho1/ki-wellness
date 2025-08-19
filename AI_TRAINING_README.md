# AI Training System for Ki Wellness

This system allows you to train and fine-tune the AI model on your own PDFs, documents, and files to improve responses for health coaching.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Training Directory
```bash
python manage_training.py
```
Select option 1 to create the training files directory.

### 3. Add Your Training Files
Place your PDF, DOCX, and TXT files in the `training_files/` directory:
- Health guides and research papers
- Nutrition information
- Wellness tips and strategies
- Any health-related content

### 4. Run Training
```bash
python manage_training.py
```
Select option 3 to process your files and train the AI.

## 📚 How It Works

### 1. **Document Processing**
- Extracts text from PDFs, DOCX, and TXT files
- Splits content into manageable chunks
- Generates embeddings for semantic search

### 2. **Knowledge Base Creation**
- Stores processed content in SQLite database
- Creates searchable knowledge base
- Enables Retrieval-Augmented Generation (RAG)

### 3. **Model Fine-tuning**
- Creates training dataset from your documents
- Fine-tunes the Mistral model with your content
- Generates custom `ki-wellness-mistral` model

### 4. **Enhanced Responses**
- Uses fine-tuned model for better responses
- Retrieves relevant context from your documents
- Provides personalized, evidence-based advice

## 🛠️ Features

### **Supported File Types**
- ✅ PDF files (*.pdf)
- ✅ Word documents (*.docx)
- ✅ Text files (*.txt)

### **Training Methods**
1. **Fine-tuning**: Trains the model on your specific content
2. **RAG (Retrieval-Augmented Generation)**: Retrieves relevant context from your documents
3. **Hybrid Approach**: Combines both methods for best results

### **Performance Tracking**
- Tracks model performance over time
- Stores training examples and responses
- Enables continuous improvement

## 📁 File Structure

```
ki_wellness/
├── training_files/          # Your training documents
├── training_data/           # Processed training data
│   ├── processed/          # Extracted content
│   └── fine_tuning_data.json
├── embeddings.db           # Knowledge base database
├── ai_training_system.py   # Main training system
├── manage_training.py      # Training management interface
└── AI_TRAINING_README.md   # This file
```

## 🔧 Usage Examples

### Basic Training
```python
from ai_training_system import AITrainingSystem

# Initialize training system
trainer = AITrainingSystem()

# Process your training files
trainer.process_training_files()

# Create training dataset
qa_pairs = [
    {
        "question": "How can I improve my water intake?",
        "answer": "To improve water intake, try setting daily goals...",
        "context": "Hydration strategies",
        "source_file": "hydration_guide.pdf"
    }
]
trainer.create_training_dataset(qa_pairs)

# Fine-tune the model
trainer.fine_tune_model("training_data/fine_tuning_data.json")
```

### Enhanced AI Responses
```python
# Generate enhanced responses
response = trainer.enhanced_ai_response(
    "How can I improve my nutrition?",
    user_data={"age": 30, "goals": "weight loss"}
)
```

## 📊 Training Data Format

### Q&A Pairs
```json
{
    "question": "User question here",
    "answer": "Expected answer based on your documents",
    "context": "Brief context description",
    "source_file": "source_document.pdf"
}
```

### Custom Training Examples
You can add your own Q&A pairs in `manage_training.py`:

```python
custom_qa_pairs = [
    {
        "question": "What are the best foods for energy?",
        "answer": "Based on research, the best foods for energy include...",
        "context": "Energy-boosting nutrition",
        "source_file": "energy_nutrition.pdf"
    }
]
```

## 🎯 Best Practices

### **Document Preparation**
1. **Quality Content**: Use high-quality, accurate health information
2. **Diverse Sources**: Include various perspectives and research
3. **Structured Content**: Well-organized documents work better
4. **Relevant Topics**: Focus on nutrition, wellness, and health coaching

### **Training Optimization**
1. **Start Small**: Begin with a few key documents
2. **Test Regularly**: Evaluate responses and adjust
3. **Iterate**: Continuously improve with new content
4. **Monitor Performance**: Track accuracy and user satisfaction

### **Content Guidelines**
- ✅ Evidence-based health information
- ✅ Nutrition and wellness guides
- ✅ Research papers and studies
- ✅ Practical health tips
- ❌ Avoid outdated or inaccurate information
- ❌ Don't include personal medical advice

## 🔍 Testing and Evaluation

### Test Enhanced Responses
```bash
python manage_training.py
```
Select option 4 to test the enhanced AI responses.

### Performance Metrics
- **Accuracy**: How well responses match expected answers
- **Relevance**: How relevant responses are to questions
- **Completeness**: How comprehensive responses are
- **User Satisfaction**: Feedback from actual users

## 🚨 Troubleshooting

### Common Issues

**1. Ollama Not Running**
```bash
# Start Ollama
ollama serve

# Pull the base model
ollama pull mistral
```

**2. File Processing Errors**
- Check file format support
- Ensure files are not corrupted
- Verify file permissions

**3. Fine-tuning Failures**
- Check available disk space
- Ensure sufficient RAM
- Verify Ollama API connectivity

**4. Poor Response Quality**
- Add more training examples
- Improve document quality
- Adjust training parameters

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Continuous Improvement

### Regular Updates
1. **Add New Documents**: Keep content current and relevant
2. **Update Training Data**: Add new Q&A pairs based on user feedback
3. **Retrain Model**: Periodically retrain with new data
4. **Evaluate Performance**: Monitor and improve response quality

### Feedback Loop
1. Collect user feedback on AI responses
2. Identify areas for improvement
3. Add new training examples
4. Retrain and test
5. Deploy improved model

## 📈 Advanced Features

### Custom Embeddings
```python
# Generate custom embeddings
embedding = trainer.generate_embeddings("Your text here")
```

### Context Retrieval
```python
# Retrieve relevant context
context = trainer.retrieve_relevant_context("User question", top_k=3)
```

### Performance Evaluation
```python
# Evaluate model performance
test_questions = [
    {"question": "Test question", "expected_answer": "Expected response"}
]
trainer.evaluate_model_performance(test_questions)
```

## 🤝 Contributing

To improve the AI training system:

1. **Add New File Types**: Support for more document formats
2. **Improve Processing**: Better text extraction and chunking
3. **Enhanced Models**: Support for different base models
4. **Better Evaluation**: More sophisticated performance metrics

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Test with simple examples first
4. Ensure all dependencies are installed

---

**Note**: This system requires Ollama to be running locally. Make sure you have sufficient computational resources for fine-tuning.
