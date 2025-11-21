# Setting Up Google Cloud Vision API

## Steps to Enable Cloud Vision API

### 1. Upload Your Service Account JSON Key

You have two options:

#### Option A: Upload via Replit Files (Recommended)
1. In the Replit Files pane (left sidebar), navigate to the `credentials` folder
2. Click the three dots (...) next to the folder name
3. Select "Upload file"
4. Upload your service account JSON file
5. Rename it to `google-cloud-key.json` if needed

#### Option B: Create the file manually
1. Create a new file in the `credentials` folder called `google-cloud-key.json`
2. Copy and paste the entire contents of your downloaded JSON key file into it
3. Save the file

### 2. The App Will Automatically Detect It

The app is already configured to look for the credentials file at:
```
credentials/google-cloud-key.json
```

Once you upload the file, the app will automatically:
- Use Google Cloud Vision API for better OCR accuracy
- Use Google Cloud Translation API for more accurate translations
- Fall back to Gemini AI if credentials are not found

### 3. Restart the App (if needed)

After uploading the credentials file, the app should automatically detect it. If not, you can restart the workflow.

## Security Note

⚠️ **Important**: The credentials file contains sensitive information. Make sure:
- Never share your credentials file publicly
- The file is only accessible in your Replit workspace
- Keep your Google Cloud project secure

## How to Get a Service Account JSON Key

If you need to create one:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Cloud Vision API and Cloud Translation API
4. Go to "IAM & Admin" → "Service Accounts"
5. Click "Create Service Account"
6. Give it a name and grant it the "Cloud Vision API User" and "Cloud Translation API User" roles
7. Click "Create Key" and choose JSON format
8. Download the JSON file
9. Upload it to the `credentials` folder in your Replit project

## Current Status

- ✅ Gemini Vision API (currently active) - works with GEMINI_API_KEY
- ⏳ Google Cloud Vision API - will activate once you upload credentials
- ⏳ Google Cloud Translation API - will activate once you upload credentials
