import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import storage
from PIL import Image
import io
from datetime import datetime, date
import os
import json
import uuid
import time
from typing import Optional, Tuple, List
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Gramedia Display Competition",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-first, clean styling
st.markdown("""
<style>
    /* Hide Streamlit elements for cleaner mobile UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Mobile-optimized container */
    .main .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* Clean header */
    .main-header {
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
    }
    
    /* Status indicator */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    .status-connected {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .status-error {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    /* Form styling */
    .form-section {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
    }
    
    .form-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2E7D32;
        margin: 0 0 1rem 0;
        text-align: center;
    }
    
    /* Image upload areas */
    .upload-area {
        border: 2px dashed #66BB6A;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
        background: #f1f8e9;
    }
    
    /* Success/Error messages */
    .message-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .success-box {
        background: #d4edda;
        color: #155724;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background: #f8d7da;
        color: #721c24;
        border-left: 4px solid #dc3545;
    }
    .warning-box {
        background: #fff3cd;
        color: #856404;
        border-left: 4px solid #ffc107;
    }
    .info-box {
        background: #d1ecf1;
        color: #0c5460;
        border-left: 4px solid #17a2b8;
    }
    
    /* Mobile button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        .form-section {
            padding: 1rem;
        }
    }
    
    @media (max-width: 480px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        .form-section {
            padding: 0.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class GramediaDisplayHandler:
    """Gramedia Display Competition handler with Google Cloud backend"""
    
    def __init__(self):
        self.gc = None
        self.storage_client = None
        self.bucket = None
        self.main_worksheet = None
        self.employee_worksheet = None
        self.store_worksheet = None
        self.connection_status = {"sheets": False, "storage": False}
        self._setup_connections()
    
    def _get_secret(self, secret_name: str, project_id: str) -> Optional[str]:
        """Get secret from Secret Manager with error handling"""
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            st.warning(f"Could not get {secret_name} from Secret Manager: {str(e)}")
            return None
    
    def _setup_connections(self):
        """Setup Google Cloud connections using Secret Manager or environment variables"""
        try:
            # Get project ID from environment or default
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "youvit-ai-chatbot")
            
            # Initialize variables
            bucket_name = None
            # Updated spreadsheet ID for Gramedia
            spreadsheet_id = "1IBAPr6UMH1EwBY5WzKiwMEcGZQdcWzF5_3eTJl4U9MU"
            creds_dict = None
            
            # Try to get configuration from Secret Manager first
            try:
                # Get secrets from Secret Manager
                bucket_name = self._get_secret("gramedia-gcs-bucket", project_id)
                # Use the hardcoded spreadsheet ID for Gramedia
                
                # Get credentials from Secret Manager
                creds_json = self._get_secret("gramedia-google-credentials", project_id)
                if creds_json:
                    creds_dict = json.loads(creds_json)
                    
            except ImportError:
                st.info("🔄 Secret Manager not available, using environment variables")
            except Exception as e:
                st.info(f"🔄 Secret Manager access failed: {str(e)}, falling back to environment variables")
            
            # Fallback to environment variables if Secret Manager failed
            if not bucket_name:
                bucket_name = os.getenv("GCS_BUCKET_NAME", "gramedia-display")
            
            if not creds_dict:
                # Try environment variables for credentials
                google_creds_json = os.getenv("GOOGLE_CREDENTIALS")
                if google_creds_json:
                    try:
                        creds_dict = json.loads(google_creds_json)
                    except json.JSONDecodeError:
                        # Maybe it's a file path
                        if os.path.exists(google_creds_json):
                            with open(google_creds_json, 'r') as f:
                                creds_dict = json.load(f)
                
                # Try default credentials.json file (for local development)
                if not creds_dict and os.path.exists("credentials.json"):
                    with open("credentials.json", 'r') as f:
                        creds_dict = json.load(f)
            
            # Validate required configuration
            if not bucket_name:
                st.error("❌ GCS bucket name not found in Secret Manager or environment variables")
                return False
                
            if not spreadsheet_id:
                st.error("❌ Spreadsheet ID not configured")
                return False
            
            if not creds_dict:
                st.error("❌ Google Cloud credentials not found")
                return False
            
            # Setup Google Sheets
            try:
                sheets_creds = Credentials.from_service_account_info(
                    creds_dict, 
                    scopes=[
                        "https://www.googleapis.com/auth/spreadsheets", 
                        "https://www.googleapis.com/auth/drive"
                    ]
                )
                self.gc = gspread.authorize(sheets_creds)
                
                # Connect to the Gramedia spreadsheet
                spreadsheet = self.gc.open_by_key(spreadsheet_id)
                
                # Get main worksheet (Sheet1)
                try:
                    self.main_worksheet = spreadsheet.sheet1
                except:
                    self.main_worksheet = spreadsheet.add_worksheet(title="Sheet1", rows="1000", cols="12")
                
                # Get or create employee worksheet
                try:
                    self.employee_worksheet = spreadsheet.worksheet("Employee Sheet")
                except:
                    self.employee_worksheet = spreadsheet.add_worksheet(title="Employee Sheet", rows="1000", cols="1")
                    self.employee_worksheet.append_row(['Employee_Name'])
                
                # Get or create store worksheet
                try:
                    self.store_worksheet = spreadsheet.worksheet("Store Sheet")
                except:
                    self.store_worksheet = spreadsheet.add_worksheet(title="Store Sheet", rows="1000", cols="1")
                    self.store_worksheet.append_row(['Store_Name'])
                
                # Verify sheet structure and create headers if needed
                self._ensure_sheet_structure()
                
                self.connection_status["sheets"] = True
                
            except Exception as e:
                st.error(f"❌ Cannot connect to Google Sheets: {str(e)}")
                self.connection_status["sheets"] = False
            
            # Setup Google Cloud Storage
            try:
                storage_creds = Credentials.from_service_account_info(
                    creds_dict, 
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                self.storage_client = storage.Client(credentials=storage_creds)
                self.bucket = self.storage_client.bucket(bucket_name)
                
                # Test bucket access
                self.bucket.exists()
                self.connection_status["storage"] = True
                
            except Exception as e:
                st.error(f"❌ Cannot connect to storage bucket '{bucket_name}': {str(e)}")
                self.connection_status["storage"] = False
                
        except Exception as e:
            st.error(f"❌ Setup error: {str(e)}")
            return False
    
    def _ensure_sheet_structure(self):
        """Ensure the spreadsheets have the correct headers for Gramedia Display Competition"""
        try:
            # Main sheet headers for Gramedia Display Competition
            main_expected_headers = [
                'Store_Name', 
                'Employee_Name', 
                'Date',
                'Education_Photo_URL',
                'Poster_Photo_URL',
                'Participation_Competition',
                'Display_Competition_Photo_URL',
                'Non_Participation_Reason',
                'Timestamp',
                'Status'
            ]
            
            # Get current headers for main sheet
            try:
                current_main_headers = self.main_worksheet.row_values(1)
            except:
                current_main_headers = []
            
            # Only add headers if sheet is empty
            if not current_main_headers:
                try:
                    all_values = self.main_worksheet.get_all_values()
                    if not all_values or (len(all_values) == 1 and not any(all_values[0])):
                        self.main_worksheet.clear()
                        self.main_worksheet.append_row(main_expected_headers)
                        st.info("📋 Main spreadsheet headers configured")
                except:
                    st.warning("⚠️ Could not verify main sheet structure")
            
            # Employee sheet headers
            employee_expected_headers = ['Employee_Name']
            
            try:
                current_employee_headers = self.employee_worksheet.row_values(1)
            except:
                current_employee_headers = []
            
            if not current_employee_headers:
                try:
                    all_values = self.employee_worksheet.get_all_values()
                    if not all_values or (len(all_values) == 1 and not any(all_values[0])):
                        self.employee_worksheet.clear()
                        self.employee_worksheet.append_row(employee_expected_headers)
                        st.info("📋 Employee spreadsheet headers configured")
                except:
                    st.warning("⚠️ Could not verify employee sheet structure")
            
            # Store sheet headers
            store_expected_headers = ['Store_Name']
            
            try:
                current_store_headers = self.store_worksheet.row_values(1)
            except:
                current_store_headers = []
            
            if not current_store_headers:
                try:
                    all_values = self.store_worksheet.get_all_values()
                    if not all_values or (len(all_values) == 1 and not any(all_values[0])):
                        self.store_worksheet.clear()
                        self.store_worksheet.append_row(store_expected_headers)
                        st.info("📋 Store spreadsheet headers configured")
                except:
                    st.warning("⚠️ Could not verify store sheet structure")
                
        except Exception as e:
            st.warning(f"Could not verify spreadsheet structure: {str(e)}")
            st.info("📌 Continuing without header verification")
    
    def get_stores_and_employees(self) -> Tuple[List[str], List[str]]:
        """Get stores from Store Sheet and employees from Employee Sheet"""
        try:
            stores = []
            employees = []
            
            # Get stores
            if self.store_worksheet:
                records = self.store_worksheet.get_all_records()
                if records:
                    df = pd.DataFrame(records)
                    if 'Store_Name' in df.columns:
                        stores = sorted([s for s in df['Store_Name'].dropna().unique().tolist() if s])
            
            # Get employees
            if self.employee_worksheet:
                records = self.employee_worksheet.get_all_records()
                if records:
                    df = pd.DataFrame(records)
                    if 'Employee_Name' in df.columns:
                        employees = sorted([e for e in df['Employee_Name'].dropna().unique().tolist() if e])
            
            return stores, employees
            
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            return [], []
    
    def add_store_to_sheet(self, store_name: str) -> bool:
        """Add new store to Store Sheet"""
        try:
            if not self.store_worksheet:
                return False
            
            # Check if store already exists
            records = self.store_worksheet.get_all_records()
            for record in records:
                if record.get('Store_Name', '').strip() == store_name.strip():
                    return True
            
            # Add new store
            self.store_worksheet.append_row([store_name.strip()])
            return True
            
        except Exception as e:
            st.error(f"❌ Error adding store: {str(e)}")
            return False
    
    def add_employee_to_sheet(self, employee_name: str) -> bool:
        """Add new employee to Employee Sheet"""
        try:
            if not self.employee_worksheet:
                return False
            
            # Check if employee already exists
            records = self.employee_worksheet.get_all_records()
            for record in records:
                if record.get('Employee_Name', '').strip() == employee_name.strip():
                    return True
            
            # Add new employee
            self.employee_worksheet.append_row([employee_name.strip()])
            return True
            
        except Exception as e:
            st.error(f"❌ Error adding employee: {str(e)}")
            return False
    
    def upload_image(self, image: Image.Image, store: str, employee: str, img_type: str) -> Optional[str]:
        """Upload image to GCS and make it publicly accessible"""
        try:
            if not self.bucket:
                st.error("❌ Storage bucket not connected")
                return None
            
            # Clean names for folder structure
            clean_store = "".join(c for c in store if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            clean_employee = "".join(c for c in employee if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            
            # Generate path for Gramedia
            date_str = datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.now().strftime("%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            path = f"gramedia-display/{clean_store}/{clean_employee}/{date_str}/{img_type}/{timestamp}_{unique_id}.jpg"
            
            # Auto-orient the image based on EXIF data
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
            
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            # Resize while maintaining aspect ratio
            if image.width > 1920 or image.height > 1920:
                if image.width > image.height:
                    new_width = 1920
                    new_height = int((1920 * image.height) / image.width)
                else:
                    new_height = 1920
                    new_width = int((1920 * image.width) / image.height)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Upload to GCS
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG', quality=85, optimize=True)
            img_bytes.seek(0)
            
            blob = self.bucket.blob(path)
            blob.upload_from_file(img_bytes, content_type='image/jpeg')
            
            # Make the blob publicly readable
            try:
                blob.make_public()
                st.success(f"✅ Image uploaded: {img_type}")
            except Exception as e:
                st.warning(f"⚠️ Image uploaded but could not make public: {str(e)}")
            
            # Return public URL
            public_url = f"https://storage.googleapis.com/{self.bucket.name}/{path}"
            return public_url
            
        except Exception as e:
            st.error(f"❌ Image upload failed: {str(e)}")
            return None
    
    def save_data(self, data: dict) -> bool:
        """Save data to main spreadsheet"""
        try:
            if not self.main_worksheet:
                st.error("❌ Main spreadsheet not connected")
                return False
            
            # Prepare row data matching Gramedia spreadsheet structure
            row_data = [
                data['store_name'],                           # Store_Name
                data['employee_name'],                        # Employee_Name
                data['date'],                                # Date
                data['education_photo_url'],                 # Education_Photo_URL
                data['poster_photo_url'],                    # Poster_Photo_URL
                data['participation_competition'],           # Participation_Competition
                data.get('display_competition_photo_url', ''), # Display_Competition_Photo_URL
                data.get('non_participation_reason', ''),    # Non_Participation_Reason
                data['timestamp'],                           # Timestamp
                data['status']                               # Status
            ]
            
            self.main_worksheet.append_row(row_data)
            return True
            
        except Exception as e:
            st.error(f"❌ Data save failed: {str(e)}")
            return False

def main():
    # Clean header with Gramedia theme
    st.markdown("""
    <div class="main-header">
        <h1>📚 Gramedia Display Competition</h1>
        <p>Store Display Data Collection Form</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize handler
    if 'handler' not in st.session_state:
        with st.spinner("🔧 Initializing connections..."):
            st.session_state.handler = GramediaDisplayHandler()
    
    # Connection status
    if st.session_state.handler.connection_status["sheets"] and st.session_state.handler.connection_status["storage"]:
        st.markdown('<div class="status-badge status-connected">✅ System Ready</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge status-error">❌ Connection Error</div>', unsafe_allow_html=True)
    
    # Check if properly configured
    if not (st.session_state.handler.connection_status["sheets"] and st.session_state.handler.connection_status["storage"]):
        st.error("""
        ❌ **Configuration Required**
        
        The system needs proper configuration to work. Please check:
        - Secret Manager secrets are configured
        - Service account has proper permissions
        - Google Spreadsheet is shared with service account
        """)
        st.stop()
    
    # Get store and employee data
    with st.spinner("📊 Loading store and employee data..."):
        stores, employees = st.session_state.handler.get_stores_and_employees()
    
    # Main data collection form
    st.markdown('<div class="form-title">➕ Add New Display Entry</div>', unsafe_allow_html=True)
    
    with st.form("display_form", clear_on_submit=True):
        # Store and Employee selection
        col1, col2 = st.columns(2)
        
        with col1:
            # Store selection
            store_options = ["Select Store..."] + stores + ["+ New Store"]
            store_selection = st.selectbox("🏪 Store Name", store_options, key="store_select")
            
            store_name = ""
            if store_selection == "+ New Store":
                store_name = st.text_input("New Store Name", placeholder="Enter store name", key="new_store")
            elif store_selection and store_selection != "Select Store...":
                store_name = store_selection
        
        with col2:
            # Employee selection
            employee_options = ["Select Employee..."] + employees + ["+ New Employee"]
            employee_selection = st.selectbox("👤 Youvitarian / Employee", employee_options, key="employee_select")
            
            employee_name = ""
            if employee_selection == "+ New Employee":
                employee_name = st.text_input("New Employee Name", placeholder="Enter employee name", key="new_employee")
            elif employee_selection and employee_selection != "Select Employee...":
                employee_name = employee_selection
        
        # Date selection
        entry_date = st.date_input("📅 Date", value=date.today())
        
        # Required photo uploads
        st.markdown("### **📸 Required Photos**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Education Photo**")
            education_photo = st.file_uploader(
                "Upload Education Photo", 
                type=['png', 'jpg', 'jpeg'],
                key="education_photo"
            )
            if education_photo:
                st.image(education_photo, use_container_width=True)
        
        with col2:
            st.markdown("**Poster Photo**")
            poster_photo = st.file_uploader(
                "Upload Poster Photo", 
                type=['png', 'jpg', 'jpeg'],
                key="poster_photo"
            )
            if poster_photo:
                st.image(poster_photo, use_container_width=True)
        
        # Display Competition Participation
        st.markdown("### **🏆 Display Competition Participation**")
        participation = st.radio(
            "Are you participating in the display competition?",
            options=["Select...", "Yes", "No"],
            key="participation_select",
            horizontal=True
        )
        
        # Conditional fields based on participation
        display_competition_photo = None
        non_participation_reason = ""
        
        if participation == "Yes":
            st.markdown("""
            <div class="message-box info-box">
                <strong>📷 Great! Please upload your display competition photo.</strong>
            </div>
            """, unsafe_allow_html=True)
            
            display_competition_photo = st.file_uploader(
                "Upload Display Competition Photo",
                type=['png', 'jpg', 'jpeg'],
                key="display_photo"
            )
            if display_competition_photo:
                st.image(display_competition_photo, use_container_width=True)
                
        elif participation == "No":
            st.markdown("""
            <div class="message-box warning-box">
                <strong>📝 Please provide the reason for not participating.</strong>
            </div>
            """, unsafe_allow_html=True)
            
            non_participation_reason = st.text_area(
                "Reason for not participating in display competition",
                placeholder="Please explain why you're not participating...",
                key="reason_input",
                height=100
            )
        
        # Submit button
        submitted = st.form_submit_button("💾 Submit Entry", type="primary")
        
        if submitted:
            # Validation
            errors = []
            if not store_name.strip():
                errors.append("Store name is required")
            if not employee_name.strip():
                errors.append("Employee name is required")
            if not education_photo:
                errors.append("Education photo is required")
            if not poster_photo:
                errors.append("Poster photo is required")
            if participation == "Select...":
                errors.append("Please select participation status")
            if participation == "Yes" and not display_competition_photo:
                errors.append("Display competition photo is required when participating")
            if participation == "No" and not non_participation_reason.strip():
                errors.append("Reason is required when not participating")
            
            if errors:
                st.markdown(f"""
                <div class="message-box error-box">
                    <strong>❌ Please complete:</strong><br>
                    • {('<br>• ').join(errors)}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Process submission
                with st.spinner("📤 Uploading entry..."):
                    try:
                        # Handle new store
                        if store_selection == "+ New Store":
                            success = st.session_state.handler.add_store_to_sheet(store_name)
                            if not success:
                                st.error("❌ Failed to add store")
                                st.stop()
                        
                        # Handle new employee
                        if employee_selection == "+ New Employee":
                            success = st.session_state.handler.add_employee_to_sheet(employee_name)
                            if not success:
                                st.error("❌ Failed to add employee")
                                st.stop()
                        
                        # Upload required photos
                        education_img = Image.open(education_photo)
                        poster_img = Image.open(poster_photo)
                        
                        education_url = st.session_state.handler.upload_image(
                            education_img, store_name, employee_name, "education"
                        )
                        poster_url = st.session_state.handler.upload_image(
                            poster_img, store_name, employee_name, "poster"
                        )
                        
                        # Upload display competition photo if participating
                        display_url = ""
                        if participation == "Yes" and display_competition_photo:
                            display_img = Image.open(display_competition_photo)
                            display_url = st.session_state.handler.upload_image(
                                display_img, store_name, employee_name, "display_competition"
                            )
                        
                        if education_url and poster_url:
                            # Prepare data
                            data = {
                                'store_name': store_name.strip(),
                                'employee_name': employee_name.strip(),
                                'date': entry_date.strftime("%Y-%m-%d"),
                                'education_photo_url': education_url,
                                'poster_photo_url': poster_url,
                                'participation_competition': participation,
                                'display_competition_photo_url': display_url if participation == "Yes" else '',
                                'non_participation_reason': non_participation_reason if participation == "No" else '',
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'status': 'Submitted'
                            }
                            
                            # Save to spreadsheet
                            if st.session_state.handler.save_data(data):
                                # Success message based on participation
                                if participation == "Yes":
                                    success_msg = "✅ Display Competition Entry Submitted!"
                                    detail_msg = f'Entry saved with display competition photo for {store_name}.'
                                else:
                                    success_msg = "✅ Entry Submitted Successfully!"
                                    detail_msg = f'Entry saved for {store_name} (not participating in competition).'
                                
                                st.markdown(f"""
                                <div class="message-box success-box">
                                    <strong>{success_msg}</strong><br>
                                    {detail_msg}
                                </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                                
                                # Show uploaded images
                                st.markdown("### **📷 Uploaded Images:**")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.image(education_url, caption=f"Education - {store_name}", use_container_width=True)
                                with col2:
                                    st.image(poster_url, caption=f"Poster - {store_name}", use_container_width=True)
                                
                                if participation == "Yes" and display_url:
                                    st.markdown("**Display Competition Photo:**")
                                    st.image(display_url, caption=f"Display Competition - {store_name}", use_container_width=True)
                                
                                # Show summary
                                st.markdown("### **📊 Submission Summary:**")
                                st.write(f"- **Store:** {store_name}")
                                st.write(f"- **Employee:** {employee_name}")
                                st.write(f"- **Date:** {entry_date.strftime('%Y-%m-%d')}")
                                st.write(f"- **Competition:** {'Participating' if participation == 'Yes' else 'Not Participating'}")
                                if participation == "No":
                                    st.write(f"- **Reason:** {non_participation_reason}")
                                
                                # Auto-refresh in 3 seconds
                                time.sleep(3)
                                st.rerun()
                            else:
                                st.error("❌ Failed to save data to spreadsheet")
                        else:
                            st.error("❌ Failed to upload images")
                            
                    except Exception as e:
                        st.error(f"❌ Error processing submission: {str(e)}")

if __name__ == "__main__":
    main()