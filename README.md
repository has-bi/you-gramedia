# Gramedia Display Competition Form 📚

A mobile-first data collection system for Gramedia store display competitions. Built with Streamlit and Google Cloud Platform.

## Features

- 📱 **Mobile-optimized UI** - Clean, responsive design for field usage
- 📊 **Google Sheets integration** - Automatic data storage to specified spreadsheet
- 🖼️ **Multi-photo management** - Education, poster, and display competition photos
- 👥 **Dynamic dropdowns** - Auto-populated store and employee lists
- 🏆 **Competition tracking** - Participation status and reasoning
- 🔐 **Secure authentication** - Google Cloud service account integration
- ☁️ **Cloud deployment** - Ready for Google Cloud Run deployment

## Form Fields

1. **Store Name** - Dropdown with option to add new stores
2. **Youvitarian/Employee Name** - Dropdown with option to add new employees
3. **Date** - Date picker for entry date
4. **Education Photo** - Required photo upload
5. **Poster Photo** - Required photo upload
6. **Display Competition Participation** - Yes/No selection
   - If **Yes**: Upload display competition photo
   - If **No**: Provide reason for not participating

## Tech Stack

- **Frontend**: Streamlit with custom CSS (Gramedia green theme)
- **Backend**: Python 3.11+
- **Storage**: Google Cloud Storage
- **Database**: Google Sheets (ID: 1IBAPr6UMH1EwBY5WzKiwMEcGZQdcWzF5_3eTJl4U9MU)
- **Authentication**: Google Cloud Service Account
- **Deployment**: Google Cloud Run

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account
- Access to the Gramedia spreadsheet
- Google Cloud Storage bucket (to be configured)

### Local Development

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd gramedia-display
   ```

2. **Set up virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up Google Cloud credentials**

   - Download service account JSON file
   - Place as `credentials.json` in project root
   - Share Google Spreadsheet with service account email

6. **Run locally**
   ```bash
   streamlit run app.py
   ```

### Production Deployment

1. **Set up Google Cloud secrets**

   ```bash
   ./setup-secrets.sh
   ```

2. **Deploy to Cloud Run**
   ```bash
   ./deploy-gramedia.sh
   ```

## Configuration

### Environment Variables

| Variable                         | Description           | Example                                        |
| -------------------------------- | --------------------- | ---------------------------------------------- |
| `GOOGLE_CLOUD_PROJECT`           | GCP Project ID        | `your-project-id`                              |
| `GCS_BUCKET_NAME`                | Storage bucket name   | `gramedia-display`                             |
| `SPREADSHEET_ID`                 | Google Sheets ID      | `1IBAPr6UMH1EwBY5WzKiwMEcGZQdcWzF5_3eTJl4U9MU` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Credentials file path | `./credentials.json`                           |

### Google Cloud Setup

1. **Enable APIs**

   - Google Sheets API
   - Google Drive API
   - Google Cloud Storage API
   - Secret Manager API

2. **Create Service Account**

   - Download credentials JSON
   - Grant necessary permissions:
     - Storage Object Admin
     - Secret Manager Secret Accessor
   - Share spreadsheet with service account email

3. **Set up Storage Bucket**
   - Create GCS bucket (name to be provided)
   - Configure appropriate access controls

## Data Structure

### Spreadsheet Columns

1. `Store_Name` - Name of the Gramedia store
2. `Employee_Name` - Name of the Youvitarian/Employee
3. `Date` - Entry date
4. `Education_Photo_URL` - URL to education photo in GCS
5. `Poster_Photo_URL` - URL to poster photo in GCS
6. `Participation_Competition` - Yes/No
7. `Display_Competition_Photo_URL` - URL to display photo (if participating)
8. `Non_Participation_Reason` - Reason text (if not participating)
9. `Timestamp` - Submission timestamp
10. `Status` - Entry status (Submitted)

### Storage Structure

Images are organized in Google Cloud Storage as:

```
gramedia-display/
├── {store_name}/
│   ├── {employee_name}/
│   │   ├── {date}/
│   │   │   ├── education/
│   │   │   ├── poster/
│   │   │   └── display_competition/
```

## Usage

1. **Access the app** (locally at http://localhost:8501)
2. **Select or add store** from dropdown
3. **Select or add employee** from dropdown
4. **Choose date** for the entry
5. **Upload education and poster photos** (required)
6. **Select participation status**
   - If participating: Upload display competition photo
   - If not: Provide reason
7. **Submit** to save data and images

## Security

- ✅ Credentials never committed to Git
- ✅ Environment variables for sensitive data
- ✅ Google Cloud Secret Manager for production
- ✅ Service account authentication
- ✅ Proper .gitignore configuration

## Differences from You-POSM

- **Theme**: Green color scheme for Gramedia branding
- **Form Fields**: Different photo requirements and competition tracking
- **Spreadsheet**: Uses Gramedia-specific spreadsheet
- **Storage Path**: Uses `gramedia-display/` prefix
- **Data Structure**: Includes competition participation fields

## Support

For support, please contact the development team or create an issue in the repository.

## License

This project is licensed under the MIT License.
