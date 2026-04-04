# Usage Guide - Problem Statement Generator

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/djmahe4/psgen_.git
cd psgen_

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your Google Gemini API key
```

### 2. Get API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key and add it to your `.env` file

```env
GOOGLE_API_KEY=your_actual_api_key_here
```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Using the Web Interface

### Step 1: Configure Settings

In the left sidebar:
- **Google Gemini API Key**: Enter your API key (or set it in `.env`)
- **Number of News Articles**: Choose how many articles to analyze (5-20)

### Step 2: Select Location

1. Navigate to the "🗺️ Select Location" tab
2. Click anywhere on the interactive map to select a location
3. Alternatively, enter a custom location name (e.g., "Mumbai, India", "New York City")

### Step 3: Generate Problem Statements

1. Click the "🚀 Generate Problem Statements" button
2. Wait while the system:
   - Searches for local news using DuckDuckGo
   - Extracts problems using AI
   - Generates solutions with implementation steps
3. Progress indicators will show the current status

### Step 4: Review Results

1. Switch to the "📋 View Problems & Solutions" tab
2. Review the problems sorted by impact (number of people affected)
3. Each problem card shows:
   - **Description**: What the problem is
   - **Location**: Where it's occurring
   - **People Affected**: Estimated number of people impacted
   - **Severity**: Critical, High, Medium, or Low

4. Each solution includes:
   - **Necessity**: Why solving this is important
   - **Difficulty**: Easy, Medium, or Hard to implement
   - **Implementation Steps**: Detailed step-by-step guide
   - **Estimated Impact**: Expected outcomes

### Step 5: Export Results

Click "📥 Download Results as JSON" to save the analysis for later use or sharing.

## Using as a Python Library

### Basic Usage

```python
from psgen import ProblemStatementGenerator

# Initialize with API key
generator = ProblemStatementGenerator(google_api_key="your_api_key")

# Generate problem statements for a location
results = generator.generate_problem_statements(
    location="San Francisco, CA",
    max_news=10
)

# Process results
for item in results:
    problem = item.problem
    solution = item.solution
    
    print(f"Problem: {problem.description}")
    print(f"Affects: {problem.affected_people:,} people")
    print(f"Severity: {problem.severity}")
    print(f"Solution Difficulty: {solution.difficulty}")
    print(f"Steps: {len(solution.implementation_steps)}")
    print("-" * 50)
```

### Advanced Usage

```python
from psgen import NewsSearchTool, ProblemExtractor, SolutionGenerator
import os

# Use individual components
api_key = os.getenv("GOOGLE_API_KEY")

# Search news only
news_tool = NewsSearchTool()
news_items = news_tool.search_local_news("Boston, MA", max_results=15)

# Extract problems
extractor = ProblemExtractor(api_key)
problems = extractor.extract_problems(news_items, "Boston, MA")

# Generate solution for specific problem
solution_gen = SolutionGenerator(api_key)
solution = solution_gen.generate_solution(problems[0])
```

### Working with Pydantic Models

```python
from models import Problem, Solution, ProblemWithSolution

# Create a custom problem
problem = Problem(
    description="Heavy traffic congestion during rush hour",
    affected_people=50000,
    severity="high",
    location="Downtown"
)

# Validate data automatically
print(problem.model_dump())  # Convert to dictionary
print(problem.model_dump_json())  # Convert to JSON string

# Models enforce validation
try:
    invalid_problem = Problem(
        description="Test",
        affected_people=-100,  # Must be >= 0
        severity="invalid",    # Must be low/medium/high/critical
        location="Test"
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

## Understanding the Output

### Problem Severity Levels

- **Critical**: Immediate threat to health, safety, or basic needs
- **High**: Significant impact on quality of life or local economy
- **Medium**: Notable concern requiring attention
- **Low**: Minor inconvenience or developing issue

### Solution Difficulty Levels

- **Easy**: Can be implemented quickly with minimal resources (weeks to months)
- **Medium**: Requires planning and coordination (months to a year)
- **Hard**: Complex, long-term initiative requiring significant resources (1+ years)

### Sorting Logic

Problems are automatically sorted by the number of people affected (descending), so the most impactful issues appear first.

## Best Practices

### For Accurate Results

1. **Be Specific with Locations**: Use city names, districts, or neighborhoods for better results
2. **Adjust News Count**: More articles provide broader coverage but take longer to process
3. **Review Context**: AI-generated estimates are approximations; verify critical information
4. **Iterate**: Try different locations or time periods to build comprehensive understanding

### For Performance

1. **Start Small**: Begin with 5-10 articles to test, increase as needed
2. **Reuse API Keys**: Store in `.env` to avoid repeated entry
3. **Batch Processing**: If analyzing multiple locations, run them separately to manage costs

### For Privacy

1. **Keep API Keys Secret**: Never commit `.env` files or share API keys
2. **Use Environment Variables**: Store sensitive data in `.env`, not in code
3. **Review Data**: Check what information is being sent to external APIs

## Troubleshooting

### No News Found
- Try a more well-known location name
- Check internet connectivity
- Verify DuckDuckGo is accessible in your region

### API Errors
- Verify your Google Gemini API key is valid
- Check if you have remaining quota
- Ensure the API is enabled in Google AI Studio

### Validation Errors
- Check that problem descriptions are meaningful
- Ensure severity and difficulty values are valid
- Verify numeric fields are positive

### Map Not Loading
- Check browser console for errors
- Ensure JavaScript is enabled
- Try refreshing the page

## Examples

### Example 1: Urban Planning

```python
generator = ProblemStatementGenerator(api_key="...")
results = generator.generate_problem_statements("Tokyo, Japan", max_news=15)

# Find transportation-related problems
transport_problems = [
    r for r in results 
    if 'traffic' in r.problem.description.lower() 
    or 'transport' in r.problem.description.lower()
]
```

### Example 2: Environmental Issues

```python
generator = ProblemStatementGenerator(api_key="...")
results = generator.generate_problem_statements("Los Angeles, CA", max_news=20)

# Focus on high-severity environmental issues
env_issues = [
    r for r in results 
    if r.problem.severity in ['high', 'critical']
    and any(word in r.problem.description.lower() 
            for word in ['air', 'water', 'pollution', 'environment'])
]
```

### Example 3: Comparative Analysis

```python
cities = ["Mumbai", "Delhi", "Bangalore"]
all_results = {}

for city in cities:
    results = generator.generate_problem_statements(f"{city}, India", max_news=10)
    all_results[city] = results
    print(f"{city}: {len(results)} problems found")
```

## API Reference

See the code documentation in each module:
- `models.py`: Data structures and validation
- `psgen.py`: Core functionality classes
- `app.py`: Web interface

## Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for similar problems
- Provide detailed information about your setup and the error

## License

See LICENSE file for details.
