# AI-Powered Smart Banking Assistant

## Project Overview
The AI-Powered Smart Banking Assistant is a web-based application developed using Python and Flask. It integrates Artificial Intelligence to provide users with conversational banking assistance and supports banking-related interactions through an easy-to-use interface.

The application uses Google Gemini AI for chatbot responses and Gmail SMTP for email notifications.

## Key Features
- AI-powered banking chatbot.
- Conversational responses using Google Gemini API.
- Banking-related user interactions.
- Email notifications using Gmail SMTP.
- Flask-based web application.
- User-friendly frontend interface.
- Secure session management using Flask Secret Key.

## Technologies Used

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| AI Integration | Google Gemini API |
| Email Service | Gmail SMTP |
| Database | As configured in the project |
| Deployment | Render |
| Version Control | Git and GitHub |

## Project Structure

```text
AI-Powered-Smart-Banking-Assistant/
│
├── app.py
├── chatbot_logic.py
├── db_utils.py
├── email_service.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── templates/
│
├── static/
│
└── Other project files
```

*Note: The actual folders and files may differ depending on your project structure.*

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Arpita-292/AI-Powered-Smart-Banking-Assistant.git
```

### 2. Open the project folder

```bash
cd AI-Powered-Smart-Banking-Assistant
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the root directory and configure the following variables:

```env
GEMINI_API_KEY=your_gemini_api_key
SMTP_PASSWORD=your_gmail_app_password
SECRET_KEY=your_flask_secret_key
```

Add any other SMTP configuration variables required by your application.

**Important:** Never upload your actual `.env` file, API keys, passwords or secret credentials to GitHub.

### 7. Run the application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## Deployment

The application is deployed using Render.

**Live Application:**  
https://ai-powered-smart-banking-assistant.onrender.com/

## API Integrations

- **Google Gemini API:** Used to generate AI-powered chatbot responses.
- **Gmail SMTP:** Used for sending application-related email notifications.

## Version Control

The project source code is maintained using Git and GitHub.

**GitHub Repository:**  
https://github.com/Arpita-292/AI-Powered-Smart-Banking-Assistant

## Future Enhancements

- Add more advanced AI-based banking assistance.
- Improve chatbot response accuracy.
- Introduce additional banking features.
- Enhance security and user authentication.
- Improve application performance and scalability.

## Author

**Arpita Patil**

B.Tech – Computer Science and Engineering

AI-Powered Smart Banking Assistant