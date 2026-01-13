# 🔍 Problem Statement Generator (psgen_)

A LangChain-based tool that uses DuckDuckGo search to find localized news, extracts problems, and generates AI-powered solution suggestions.

## ✨ Features

- 🗺️ **Interactive Map Selection**: Choose any location on an interactive map
- 📰 **Local News Search**: Uses DuckDuckGo to fetch latest local news
- 🤖 **AI-Powered Analysis**: Leverages Google GenerativeAI (Gemini) to:
  - Extract problems from news articles
  - Estimate number of people affected
  - Sort problems by impact
  - Generate detailed solutions with implementation steps
- ✅ **Pydantic Validation**: Ensures data quality and structure
- 🎨 **Beautiful Web UI**: Built with Streamlit for easy interaction

## 📸 Screenshots

### Main Interface - Location Selection
![Main Interface](https://github.com/user-attachments/assets/30709c6a-d626-4a2f-a007-c7bf5cae4e98)

The main interface features:
- **Left Sidebar**: Configuration panel with API key input and adjustable settings for number of news articles
- **Main Area**: Two-tab interface for selecting location and viewing results
- **About Section**: Lists the technologies used (DuckDuckGo, Google GenAI, Pydantic, Interactive map)
- **Interactive Map**: Click anywhere on the map to select a location for analysis

### Results View - Problems & Solutions
![Results View](https://github.com/user-attachments/assets/7c5e23bd-b1b2-4142-b1b0-6c74e8ee15c1)

The results view shows:
- **Step-by-step workflow**: Clear guidance through the analysis process
- **Problems sorted by impact**: Most affected communities appear first
- **Color-coded severity**: Visual indicators for critical, high, medium, and low severity issues
- **AI-generated solutions**: Detailed implementation plans with difficulty ratings

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/djmahe4/psgen_.git
cd psgen_
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys:
```bash
cp .env.example .env
# Edit .env and add your Google GenerativeAI API key
```

Get your Google GenAI API key from: https://makersuite.google.com/app/apikey

## 📖 Usage

### Running the Web Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Using the Application

1. **Configure API Key**: Enter your Google GenAI API key in the sidebar
2. **Select Location**: Click on the map to select a location or enter a custom location name
3. **Generate Problems**: Click "Generate Problem Statements" to analyze local news
4. **Review Results**: Switch to the "View Problems & Solutions" tab to see:
   - Problems sorted by number of people affected
   - Severity levels (critical, high, medium, low)
   - AI-generated solutions with:
     - Necessity explanation
     - Implementation difficulty
     - Step-by-step implementation guide
     - Estimated impact
5. **Download Results**: Export results as JSON for further analysis

### Using as a Python Library

```python
from psgen import ProblemStatementGenerator

# Initialize with your API key
generator = ProblemStatementGenerator(google_api_key="your_api_key")

# Generate problem statements for a location
results = generator.generate_problem_statements("Mumbai, India", max_news=10)

# Access results
for item in results:
    print(f"Problem: {item.problem.description}")
    print(f"Affected: {item.problem.affected_people} people")
    print(f"Solution: {item.solution.necessity}")
```

## 🏗️ Architecture

### Components

1. **models.py**: Pydantic models for data validation
   - `NewsItem`: Structure for news articles
   - `Problem`: Extracted problem with metadata
   - `Solution`: AI-generated solution details
   - `ProblemWithSolution`: Combined problem and solution

2. **psgen.py**: Core backend logic
   - `NewsSearchTool`: DuckDuckGo search integration
   - `ProblemExtractor`: AI-powered problem extraction
   - `SolutionGenerator`: AI-powered solution generation
   - `ProblemStatementGenerator`: Main orchestrator

3. **app.py**: Streamlit web interface
   - Interactive map with Folium
   - Problem and solution display
   - Configuration and API key management

### Data Flow

```
User Selects Location
    ↓
DuckDuckGo Search (News)
    ↓
Google GenAI (Extract Problems)
    ↓
Sort by Affected People
    ↓
Google GenAI (Generate Solutions)
    ↓
Display in UI / Return Results
```

## 🛠️ Technologies Used

- **LangChain**: Framework for LLM applications
- **DuckDuckGo Search**: Privacy-focused search engine
- **Google GenerativeAI (Gemini)**: AI model for analysis
- **Pydantic**: Data validation and parsing
- **Streamlit**: Web application framework
- **Folium**: Interactive mapping library

## 📋 Requirements

See `requirements.txt` for complete list:
- Python 3.8+
- langchain & langchain-community
- duckduckgo-search
- google-generativeai
- pydantic
- streamlit
- folium & streamlit-folium
- python-dotenv

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

See LICENSE file for details.

## 🔐 Privacy & Security

- API keys are stored locally in `.env` file (not committed to git)
- DuckDuckGo search does not track users
- No personal data is collected or stored
- All processing happens client-side or through configured APIs

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.
