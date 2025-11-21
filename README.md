# 🏥 AI Health Assistant

A comprehensive Streamlit web application for analyzing test reports, providing AI health consultations, and finding nearby hospitals.

## Features

### 📊 Multi-Test Report Analysis
- Upload various medical reports (PDF or Image) including blood tests, X-rays, prescriptions, and more.
- Automatic text extraction using OCR
- Parse key lab results (Hemoglobin, Glucose, WBC, Platelets, Cholesterol, etc.)
- AI-powered health explanations with status indicators (Normal/High/Low)
- Personalized lifestyle tips for abnormal readings
- Multi-language support

### 💬 Health Chatbot
- Interactive AI assistant for health questions
- Context-aware responses based on uploaded reports
- Conversational chat interface with history
- Multi-language support

### 🏥 Hospital Finder
- Search nearby hospitals based on location
- Interactive map visualization
- Hospital details (name, address, rating, opening hours)
- Adjustable search radius (1-20 km)

### 🌍 Multi-Language Support
- English
- Hindi
- Spanish
- French
- German

## Setup Instructions

### 1. API Keys Required

#### Minimum Setup (Gemini API Only)
For basic functionality, you only need:
- **GEMINI_API_KEY**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

This enables:
- OCR text extraction (using Gemini Vision)
- Medical report analysis
- Health chatbot
- Translation to multiple languages

#### Full GCP Setup (Optional)
For enhanced features, you can also configure:

**Google Cloud Vision & Translation:**
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Vision API and Translation API
3. Create a service account and download JSON key file
4. Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key.json`

**Google Maps API:**
- **GOOGLE_MAPS_API_KEY**: Enable Places API in Google Cloud Console

### 2. Setting Up API Keys

1. Create a `.env` file in the root of the project.
2. Add your API keys to the `.env` file:
   ```
   GEMINI_API_KEY="your-gemini-api-key"
   GOOGLE_MAPS_API_KEY="your-maps-api-key"
   GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
   ```

### 3. Running the Application

```bash
pip install -r requirements.txt
streamlit run app.py --server.port 5000
```

## How to Use

### Analyzing Medical Reports
1. Go to the "Report Analysis" tab
2. Upload your medical report (PDF, Image)
3. Wait for text extraction and parsing
4. Click "Analyze Results" to get AI insights
5. Select your preferred language from the sidebar

### Chatting with AI
1. Go to the "Health Chatbot" tab
2. Type your health questions in the chat input
3. Get personalized responses based on your uploaded reports
4. Chat history is maintained for context

### Finding Hospitals
1. Go to the "Hospital Finder" tab
2. Enter your location (city, address, or area)
3. Adjust the search radius if needed
4. Click "Find Hospitals" to see results on the map
5. View detailed information about each hospital

## Technical Stack

- **Frontend**: Streamlit
- **OCR**: Google Cloud Vision API / Gemini Vision API
- **AI/NLP**: Google Gemini 2.5 Flash/Pro
- **Translation**: Google Cloud Translation API / Gemini
- **Maps**: Google Maps Places API
- **PDF Processing**: PyPDF2, pdf2image
- **Image Processing**: Pillow
- **Map Visualization**: Folium, streamlit-folium

## Architecture

```
app.py                 # Main Streamlit application
gemini_helper.py      # Gemini AI functions (analysis, chatbot, translation)
gcp_services.py       # Google Cloud services (Vision, Translation)
maps_helper.py        # Google Maps integration
medical_parser.py     # Medical report parsing logic
```

## Important Notes

⚠️ **Medical Disclaimer**: This is an AI assistant for informational purposes only. Always consult qualified healthcare professionals for medical advice, diagnosis, or treatment.

🔒 **Privacy**: Your uploaded reports are processed in real-time and not stored permanently. API calls are made securely to Google services.

💡 **API Costs**: Be aware that using Google Cloud APIs may incur costs based on usage. Gemini API has a free tier available.

## Troubleshooting

**OCR not working?**
- Ensure GEMINI_API_KEY is set (minimum requirement)
- For better accuracy, set up GOOGLE_APPLICATION_CREDENTIALS with Vision API

**Translation not working?**
- App uses Gemini for translation by default if GCP credentials not available
- Ensure GEMINI_API_KEY is set

**Hospital finder not working?**
- Ensure GOOGLE_MAPS_API_KEY is set and Places API is enabled
- Check that your location query is specific enough

**App not loading?**
- Check that all required Python packages are installed
- Verify the Streamlit server is running on port 5000

## Future Enhancements

- Report history and trend analysis
- Downloadable PDF reports
- Voice input/output for chatbot
- Emergency services integration
- Appointment booking with hospitals
- Support for more languages
- Mobile app version
