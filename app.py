import streamlit as st
import os
from io import BytesIO
from PIL import Image
import PyPDF2
from pdf2image import convert_from_bytes
import folium
from streamlit_folium import st_folium
import logging
from pathlib import Path
from dotenv import load_dotenv
from gtts import gTTS
import tempfile
import speech_recognition as sr

from gemini_helper import analyze_blood_report, chatbot_response, generate_summary_report, summarize_report
from gcp_services import extract_text_from_image, translate_text_gcp
from maps_helper import find_nearby_hospitals
from medical_parser import parse_blood_test_results, get_normal_ranges, determine_status

logging.basicConfig(level=logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

st.set_page_config(
    page_title="Health Assistant AI",
    page_icon="🏥",
    layout="wide"
)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'lab_results' not in st.session_state:
    st.session_state.lab_results = {}
if 'analysis' not in st.session_state:
    st.session_state.analysis = {}
if 'uploaded_image_bytes' not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if 'report_summary' not in st.session_state:
    st.session_state.report_summary = ""
if 'report_summary_translations' not in st.session_state:
    st.session_state.report_summary_translations = {}
if 'voice_answer' not in st.session_state:
    st.session_state.voice_answer = ""

LANGUAGES = ["English", "Hindi", "Spanish", "French", "German"]

st.title("🏥 AI Health Assistant")
st.markdown("*Upload medical reports, chat with AI, and find nearby hospitals*")

selected_language = st.sidebar.selectbox("🌍 Select Language", LANGUAGES, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 About")
st.sidebar.info(
    "This app helps you:\n"
    "- Analyze various medical reports\n"
    "- Get AI health insights\n"
    "- Chat about your health\n"
    "- Find nearby hospitals"
)

tab1, tab2, tab3 = st.tabs(["📊 Report Analysis", "💬 Health Chatbot", "🏥 Hospital Finder"])

with tab1:
    st.header("📊 Medical Report Analysis")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload Report")
        uploaded_file = st.file_uploader(
            "Upload your medical report (PDF or Image)",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Upload a clear image or PDF of your medical report"
        )
        
        if uploaded_file:
            file_type = uploaded_file.type
            
            with st.spinner("Processing your report..."):
                try:
                    if 'pdf' in file_type:
                        pdf_bytes = uploaded_file.read()
                        images = convert_from_bytes(pdf_bytes)
                        
                        if images:
                            img_byte_arr = BytesIO()
                            images[0].save(img_byte_arr, format='PNG')
                            img_byte_arr = img_byte_arr.getvalue()
                            
                            st.image(images[0], caption="First page of PDF", use_container_width=True)
                            
                            extracted_text = extract_text_from_image(img_byte_arr)
                            st.session_state.uploaded_image_bytes = img_byte_arr
                        else:
                            st.error("Could not extract images from PDF")
                            extracted_text = ""
                    else:
                        image_bytes = uploaded_file.read()
                        image = Image.open(BytesIO(image_bytes))
                        st.image(image, caption="Uploaded Image", use_container_width=True)
                        
                        extracted_text = extract_text_from_image(image_bytes)
                        st.session_state.uploaded_image_bytes = image_bytes
                    
                    if extracted_text and not extracted_text.startswith("Error"):
                        st.session_state.extracted_text = extracted_text
                        st.success("✅ Text extracted successfully!")
                        
                        with st.expander("View Extracted Text"):
                            st.text_area("", extracted_text, height=200)
                        
                        lab_results = parse_blood_test_results(extracted_text)
                        st.session_state.lab_results = lab_results
                        
                        if lab_results:
                            st.success(f"✅ Found {len(lab_results)} test parameters")
                        else:
                            st.warning("No standard medical test parameters detected. You can still chat about the report.")
                    else:
                        st.error(f"Error: {extracted_text}")
                        
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
        
        if st.session_state.lab_results and st.button("🔍 Analyze Results", type="primary"):
            with st.spinner("Analyzing your results..."):
                try:
                    analysis = analyze_blood_report(
                        st.session_state.extracted_text,
                        st.session_state.lab_results
                    )
                    st.session_state.analysis = analysis
                except Exception as e:
                    st.error(f"Error analyzing results: {str(e)}")
    
    with col2:
        st.subheader("Analysis Results")
        
        if st.session_state.lab_results:
            st.markdown("### 📋 Detected Parameters")
            
            for test_name, data in st.session_state.lab_results.items():
                value = float(data['value'])
                unit = data['unit']
                status = determine_status(test_name, value)
                
                if status == "Normal":
                    color = "🟢"
                elif status == "High":
                    color = "🔴"
                elif status == "Low":
                    color = "🟡"
                else:
                    color = "⚪"
                
                st.markdown(f"{color} **{test_name}**: {value} {unit} - *{status}*")
        
        if st.session_state.analysis and 'results' in st.session_state.analysis:
            st.markdown("--")
            st.markdown("### 🤖 AI Analysis")
            
            analysis_results = st.session_state.analysis['results']
            
            for result in analysis_results:
                with st.expander(f"📌 {result['test_name']} - {result['status']}"):
                    explanation = result['explanation']
                    tip = result['tip']
                    
                    if selected_language != "English":
                        with st.spinner(f"Translating to {selected_language}..."): 
                            explanation = translate_text_gcp(explanation, selected_language)
                            tip = translate_text_gcp(tip, selected_language)
                    
                    st.write(f"**Value:** {result['value']}")
                    st.write(f"**Status:** {result['status']}")
                    st.write(f"**Explanation:** {explanation}")
                    if result['status'] != "Normal":
                        st.info(f"💡 **Tip:** {tip}")
            
            if 'overall_summary' in st.session_state.analysis:
                st.markdown("--")
                st.markdown("### 📝 Overall Summary")
                summary = st.session_state.analysis['overall_summary']
                
                if selected_language != "English":
                    with st.spinner(f"Translating to {selected_language}..."): 
                        summary = translate_text_gcp(summary, selected_language)
                
                st.info(summary)
            
            st.markdown("--")
            if st.button("📄 Generate Detailed Summary Report", type="secondary"):
                with st.spinner("Generating comprehensive summary report..."):
                    try:
                        summary_report = generate_summary_report(
                            st.session_state.extracted_text,
                            st.session_state.lab_results,
                            st.session_state.analysis
                        )
                        
                        if selected_language != "English":
                            summary_report = translate_text_gcp(summary_report, selected_language)
                        
                        st.markdown("### 📋 Comprehensive Health Summary Report")
                        st.markdown(summary_report)
                        
                        st.download_button(
                            label="💾 Download Report as Text",
                            data=summary_report,
                            file_name=f"health_summary_report_{selected_language}.txt",
                            mime="text/plain"
                        )
                    except Exception as e:
                        st.error(f"Error generating summary report: {str(e)}")

        st.markdown("--")
        st.subheader("📝 General Report Summary")
        if st.button("📝 Summarize Uploaded Report", type="primary"):
            with st.spinner("Summarizing your report..."):
                try:
                    summary_text = summarize_report(
                        image_bytes=st.session_state.get('uploaded_image_bytes'),
                        text=st.session_state.get('extracted_text')
                    )
                    st.session_state.report_summary = summary_text or ""
                    st.session_state.report_summary_translations = {}
                except Exception as e:
                    st.error(f"Error summarizing report: {str(e)}")
        
        if st.session_state.report_summary:
            st.markdown("### 📝 Summary")
            st.markdown(st.session_state.report_summary)
            st.download_button(
                label="💾 Download Summary",
                data=st.session_state.report_summary,
                file_name=f"report_summary_{selected_language}.txt",
                mime="text/plain"
            )

            st.markdown("--")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🧑‍⚕️ Generate Doctor Prep Pack"):
                    with st.spinner("Preparing your doctor pack..."):
                        from gemini_helper import generate_doctor_pack
                        doc_pack = generate_doctor_pack(
                            st.session_state.get('extracted_text', ''),
                            st.session_state.get('lab_results', {}),
                            st.session_state.get('analysis', {})
                        )
                        if selected_language != "English" and doc_pack:
                            doc_pack = translate_text_gcp(doc_pack, selected_language)
                        st.session_state['doctor_pack'] = doc_pack
            with col_b:
                if st.button("📅 Generate 7-Day Action Plan"):
                    with st.spinner("Creating your action plan..."):
                        from gemini_helper import generate_action_plan
                        plan = generate_action_plan(
                            st.session_state.get('report_summary', ''),
                            st.session_state.get('lab_results', {})
                        )
                        if selected_language != "English" and plan:
                            plan = translate_text_gcp(plan, selected_language)
                        st.session_state['action_plan'] = plan

            if st.session_state.get('doctor_pack'):
                st.markdown("### 🧑‍⚕️ Doctor Prep Pack")
                st.markdown(st.session_state['doctor_pack'])
                st.download_button(
                    label="💾 Download Doctor Pack",
                    data=st.session_state['doctor_pack'],
                    file_name=f"doctor_prep_pack_{selected_language}.txt",
                    mime="text/plain"
                )

            if st.session_state.get('action_plan'):
                st.markdown("### 📅 7-Day Action Plan")
                st.markdown(st.session_state['action_plan'])
                st.download_button(
                    label="💾 Download Action Plan",
                    data=st.session_state['action_plan'],
                    file_name=f"action_plan_{selected_language}.txt",
                    mime="text/plain"
                )

            translate_choices = [l for l in LANGUAGES if l != "English"]
            selected_translations = st.multiselect(
                "Select languages for translation",
                translate_choices,
                default=[selected_language] if selected_language in translate_choices else []
            )
            if st.button("🌐 Generate Translated Summaries"):
                with st.spinner("Translating summary..."):
                    translations = {}
                    for lang in selected_translations:
                        try:
                            translations[lang] = translate_text_gcp(st.session_state.report_summary, lang)
                        except Exception as e:
                            translations[lang] = f"Error translating to {lang}: {str(e)}"
                    st.session_state.report_summary_translations = translations

            if st.session_state.report_summary_translations:
                st.markdown("### 🌐 Translated Summaries")
                for lang, text in st.session_state.report_summary_translations.items():
                    with st.expander(f"{lang}"):
                        st.markdown(text)
                        st.download_button(
                            label=f"💾 Download ({lang})",
                            data=text,
                            file_name=f"report_summary_{lang}.txt",
                            mime="text/plain"
                        )

            st.markdown("--")
            st.subheader("🎧 Hear My Report")
            # Map app languages to gTTS codes
            tts_lang_map = {
                "English": "en",
                "Hindi": "hi",
                "Spanish": "es",
                "French": "fr",
                "German": "de",
            }
            tts_language = st.selectbox("Select audio language", list(tts_lang_map.keys()), index=0, key="tts_lang")
            if st.button("🔊 Generate Audio"):
                try:
                    code = tts_lang_map.get(tts_language, "en")
                    text = st.session_state.report_summary
                    if not text:
                        st.warning("No summary available. Generate a summary first.")
                    else:
                        tts = gTTS(text=text, lang=code, slow=False)
                        tmp_dir = tempfile.gettempdir()
                        out_path = os.path.join(tmp_dir, f"report_tts_{code}.mp3")
                        tts.save(out_path)
                        with open(out_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label=f"💾 Download Audio ({tts_language})",
                            data=audio_bytes,
                            file_name=f"report_audio_{code}.mp3",
                            mime="audio/mpeg"
                        )
                except Exception as e:
                    st.error(f"TTS error: {str(e)}")

            st.markdown("--")
            st.subheader("👀 Visual Explanation")
            if st.session_state.lab_results:
                for test_name, data in st.session_state.lab_results.items():
                    try:
                        value = float(data['value'])
                    except Exception:
                        continue
                    unit = data.get('unit', '')
                    status = determine_status(test_name, value)
                    color = "🟢" if status == "Normal" else ("🔴" if status == "High" else ("🟡" if status == "Low" else "⚪"))
                    tips = {
                        "High": "🍭🚫  💧  🚶‍♂",
                        "Low": "🍎  💤  ☀",
                        "Normal": "✅",
                    }
                    tip_icons = tips.get(status, "")
                    st.markdown(f"{color} **{test_name}**: {value} {unit} — *{status}*  {tip_icons}")
            else:
                st.info("No parameters detected yet. Upload a report and extract text to see visuals.")

            st.markdown("--")
            st.subheader("🎙 Talk to Your Report")
            st.caption("Upload a short WAV/FLAC audio question. We'll transcribe and answer, then you can hear the reply.")
            audio_file = st.file_uploader("Upload your voice question (WAV/FLAC)", type=["wav", "flac"], key="voice_uploader")
            voice_lang_map = {
                "English (India)": "en-IN",
                "Hindi": "hi-IN",
            }
            voice_lang = st.selectbox("Spoken language", list(voice_lang_map.keys()), index=0, key="voice_lang")
            reply_tts_lang = st.selectbox("Reply audio language", list(tts_lang_map.keys()), index=0, key="reply_tts_lang")
            if st.button("📝 Transcribe & Answer"):
                if not audio_file:
                    st.warning("Please upload an audio file.")
                else:
                    try:
                        recognizer = sr.Recognizer()
                        with sr.AudioFile(audio_file) as source:
                            audio = recognizer.record(source)
                        query = recognizer.recognize_google(audio, language=voice_lang_map[voice_lang])
                        st.markdown(f"**You (transcribed):** {query}")
                        report_context = ""
                        if st.session_state.lab_results:
                            report_context = f"User's medical test results: {st.session_state.lab_results}"
                        answer = chatbot_response(query, st.session_state.chat_history, report_context)
                        st.session_state.voice_answer = answer
                        st.markdown(f"**AI Assistant:** {answer}")
                    except Exception as e:
                        st.error(f"Voice processing error: {str(e)}")

            if st.session_state.voice_answer:
                if st.button("🔊 Speak Answer"):
                    try:
                        code = tts_lang_map.get(reply_tts_lang, "en")
                        tts = gTTS(text=st.session_state.voice_answer, lang=code, slow=False)
                        tmp_dir = tempfile.gettempdir()
                        out_path = os.path.join(tmp_dir, f"voice_answer_{code}.mp3")
                        tts.save(out_path)
                        with open(out_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label=f"💾 Download Answer Audio ({reply_tts_lang})",
                            data=audio_bytes,
                            file_name=f"voice_answer_{code}.mp3",
                            mime="audio/mpeg"
                        )
                    except Exception as e:
                        st.error(f"TTS error: {str(e)}")

with tab2:
    st.header("💬 Health Chatbot")
    st.markdown("Ask questions about your health or medical results")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**AI Assistant:** {message['content']}")
                st.markdown("--")
    
    user_input = st.chat_input("Type your health question here...")
    
    if user_input:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        report_context = ""
        if st.session_state.lab_results:
            report_context = f"User's medical test results: {st.session_state.lab_results}"
        
        with st.spinner("AI is thinking..."):
            response = chatbot_response(
                user_input,
                st.session_state.chat_history,
                report_context
            )
            
            if selected_language != "English":
                response = translate_text_gcp(response, selected_language)
            
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
        
        st.rerun()

with tab3:
    st.header("🏥 Nearby Hospital Finder")
    st.markdown("Find hospitals and medical centers near you")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Search Location")
        
        location_input = st.text_input(
            "Enter your location",
            placeholder="e.g., New Delhi, Mumbai, Bangalore",
            help="Enter a city, address, or area name"
        )
        
        radius = st.slider(
            "Search radius (km)",
            min_value=1,
            max_value=20,
            value=5,
            help="Distance to search for hospitals"
        )
        
        search_button = st.button("🔍 Find Hospitals", type="primary")
        
        if search_button and location_input:
            with st.spinner("Searching for nearby hospitals..."):
                try:
                    results = find_nearby_hospitals(location_input, radius * 1000)
                    
                    if 'error' in results:
                        st.error(f"Error: {results['error']}")
                        st.info("💡 Make sure you have set up your Google Maps API key")
                    else:
                        st.session_state.hospital_results = results
                        st.success(f"✅ Found {len(results['hospitals'])} hospitals")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("Map View")
        
        if 'hospital_results' in st.session_state and st.session_state.hospital_results:
            results = st.session_state.hospital_results
            center = results['center']
            hospitals = results['hospitals']
            
            m = folium.Map(
                location=[center['lat'], center['lng']],
                zoom_start=13
            )
            
            folium.Marker(
                [center['lat'], center['lng']],
                popup="Your Location",
                tooltip="You are here",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            
            for hospital in hospitals:
                popup_text = f"""
                <b>{hospital['name']}</b><br>
                {hospital['address']}<br>
                Rating: {hospital['rating']}/5
                """
                
                folium.Marker(
                    [hospital['lat'], hospital['lng']],
                    popup=folium.Popup(popup_text, max_width=250),
                    tooltip=hospital['name'],
                    icon=folium.Icon(color='red', icon='plus', prefix='fa')
                ).add_to(m)
            
            st_folium(m, width=700, height=500)
            
            st.markdown("--")
            st.subheader("📋 Hospital List")
            
            for idx, hospital in enumerate(hospitals, 1):
                with st.expander(f"{idx}. {hospital['name']} ⭐ {hospital['rating']}"):
                    st.write(f"**Address:** {hospital['address']}")
                    st.write(f"**Rating:** {hospital['rating']}/5")
                    
                    if hospital['open_now'] is not None:
                        status = "🟢 Open Now" if hospital['open_now'] else "🔴 Closed"
                        st.write(f"**Status:** {status}")
                    
                    st.write(f"**Coordinates:** {hospital['lat']}, {hospital['lng']}")
        else:
            st.info("🗺️ Enter a location and click 'Find Hospitals' to see results on the map")
            
            default_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
            st_folium(default_map, width=700, height=500)

st.markdown("--")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "⚠️ This is an AI assistant. Always consult healthcare professionals for medical advice."
    "</div>",
    unsafe_allow_html=True
)
