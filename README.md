# IntelliAssistant

An intelligent assistant application that helps users query and analyze data from various sources, including SQL databases. The application uses natural language processing to convert user questions into SQL queries.

## Features

- Natural language to SQL conversion
- Database schema analysis
- Financial data analysis
- Data visualization
- Integration with multiple data sources

## Architecture

The application consists of:

- Backend API built with Flask
- Frontend UI built with React
- SQL Server connectivity for database access
- Integration with Gemini for AI capabilities

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js and npm
- SQL Server instance (for database features)
- Gemini API key

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/IntelliAssistant.git
   cd IntelliAssistant
   ```

2. Set up the Python environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure the application
   ```
   cp config.py.example config.py
   ```
   Edit `config.py` to add your API keys and configuration settings.

4. Install frontend dependencies
   ```
   cd frontend
   npm install
   npm run build
   cd ..
   ```

5. Run the application
   ```
   python api.py
   ```

The application should now be running at `http://localhost:5000`.

## Environment Variables

Set the following environment variables:

- `GEMINI_API_KEY`: Your Gemini API key
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI features)

## Planned Enhancements

- Implementation of an agentic approach for more robust SQL generation
- Support for more database types
- Enhanced visualizations
- Local LLM integration

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
This project is licensed under the MIT License - see the LICENSE file for details. 