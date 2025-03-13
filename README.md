# IntelliAssistant

An intelligent data analysis assistant powered by Google's Gemini AI. This application provides an interactive interface for data analysis, visualization, and insights generation.

## Features

- Interactive chat interface for data analysis
- Support for uploading and analyzing various data formats (CSV, Excel)
- Real-time data visualization
- Dataset management and preview
- Modern, responsive UI built with React and Material UI
- Powered by Google's Gemini AI for intelligent analysis

## Tech Stack

### Frontend
- React.js
- Material UI
- Axios for API communication
- Chart.js for visualizations

### Backend
- Python
- Flask
- Pandas for data processing
- Google Gemini AI for analysis
- SQLite for data storage

## Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- Google Gemini API key

### Backend Setup
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   export GEMINI_API_KEY="your_api_key"  # On Windows: set GEMINI_API_KEY=your_api_key
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

## Running the Application

1. Start the backend server:
   ```bash
   python run.py
   ```
2. In a separate terminal, start the frontend development server:
   ```bash
   cd frontend
   npm start
   ```
3. Access the application at `http://localhost:3000`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 