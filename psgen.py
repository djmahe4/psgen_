"""
Core backend functionality for problem statement generation.
"""
import os
import json
import re
from typing import List
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from models import NewsItem, Problem, Solution, ProblemWithSolution


def sanitize_input(text: str, max_length: int = 200) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters and limit length
    text = text.strip()[:max_length]
    
    # Remove any potential command injection characters
    # Keep only alphanumeric, spaces, commas, hyphens, and basic punctuation
    text = re.sub(r'[^\w\s,.\-()]', '', text)
    
    return text


class NewsSearchTool:
    """Tool for searching localized news using LangChain's DuckDuckGo integration."""
    
    def __init__(self):
        self.search = DuckDuckGoSearchRun()
    
    def search_local_news(self, location: str, max_results: int = 10) -> List[NewsItem]:
        """
        Search for local news in a specific location.
        
        Args:
            location: The location to search news for
            max_results: Maximum number of results to return
            
        Returns:
            List of NewsItem objects
        """
        # Sanitize location input to prevent injection
        location = sanitize_input(location, max_length=100)
        if not location:
            logging.warning("Empty location provided after sanitization")
            return []
        
        # Create search query for local news and problems
        query = f"{location} local news problems issues"
        
        try:
            # DuckDuckGoSearchRun returns a string with search results
            results_text = self.search.run(query)
            
            # Parse the results and create NewsItem objects
            # The results are typically formatted as snippets
            news_items = []
            
            # Split results into sections (each result is typically on its own line or paragraph)
            result_sections = results_text.split('\n\n') if '\n\n' in results_text else [results_text]
            
            for i, section in enumerate(result_sections[:max_results]):
                if section.strip():
                    # Create a news item from each section
                    news_item = NewsItem(
                        title=f"News Item {i+1} - {location}",
                        snippet=section.strip(),
                        link=f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                        source="DuckDuckGo Search"
                    )
                    news_items.append(news_item)
            
            # If we didn't get enough items, create at least one with all results
            if not news_items and results_text.strip():
                news_items.append(NewsItem(
                    title=f"Search Results - {location}",
                    snippet=results_text.strip()[:500],  # Limit to 500 chars
                    link=f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                    source="DuckDuckGo Search"
                ))
            
            return news_items
        except Exception as e:
            logging.error(f"Error searching news: {e}", exc_info=True)
            return []


class ProblemExtractor:
    """Extract problems from news items using LangChain Google GenAI."""
    
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-latest",
            google_api_key=api_key,
            temperature=0.7
        )
    
    def extract_problems(self, news_items: List[NewsItem], location: str) -> List[Problem]:
        """
        Extract problems from news items using AI.
        
        Args:
            news_items: List of news items to analyze
            location: The location context
            
        Returns:
            List of Problem objects sorted by number of affected people
        """
        # Sanitize location input to prevent prompt injection
        location = sanitize_input(location, max_length=100)
        if not location:
            logging.warning("Empty location provided after sanitization")
            return []
        
        # Prepare news content for analysis
        news_content = "\n\n".join([
            f"Title: {item.title}\nContent: {item.snippet}"
            for item in news_items
        ])
        
        prompt = f"""
Analyze the following news articles from {location} and extract distinct problems or issues.
For each problem, estimate:
1. A clear description of the problem
2. The number of people affected (provide a realistic estimate)
3. The severity level (low, medium, high, or critical)
4. The specific location

Return the response as a JSON array of objects with keys: description, affected_people, severity, location

News Articles:
{news_content}

Response format (JSON array):
[
  {{
    "description": "Problem description",
    "affected_people": 1000,
    "severity": "high",
    "location": "{location}"
  }}
]
"""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            problems_data = json.loads(response_text)
            
            # Validate and create Problem objects
            problems = []
            for prob_data in problems_data:
                try:
                    problem = Problem(**prob_data)
                    problems.append(problem)
                except Exception as e:
                    logging.error(f"Error validating problem: {e}")
                    continue
            
            # Sort by number of affected people (descending)
            problems.sort(key=lambda x: x.affected_people, reverse=True)
            
            return problems
        except Exception as e:
            logging.error(f"Error extracting problems: {e}", exc_info=True)
            return []


class SolutionGenerator:
    """Generate solutions for problems using LangChain Google GenAI."""
    
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-latest",
            google_api_key=api_key,
            temperature=0.7
        )
    
    def generate_solution(self, problem: Problem) -> Solution:
        """
        Generate a solution for a given problem.
        
        Args:
            problem: The problem to solve
            
        Returns:
            Solution object with implementation details
        """
        prompt = f"""
Analyze the following problem and provide a detailed solution:

Problem: {problem.description}
Location: {problem.location}
People Affected: {problem.affected_people}
Severity: {problem.severity}

Provide:
1. Why this solution is necessary (necessity)
2. Difficulty level to implement (easy, medium, or hard)
3. Step-by-step implementation steps (as a list)
4. Estimated impact of the solution

Return the response as a JSON object with keys: necessity, difficulty, implementation_steps (array), estimated_impact

Response format (JSON):
{{
  "necessity": "Explanation of why this solution is needed",
  "difficulty": "medium",
  "implementation_steps": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "estimated_impact": "Description of expected impact"
}}
"""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            solution_data = json.loads(response_text)
            solution = Solution(**solution_data)
            
            return solution
        except Exception as e:
            logging.error(f"Error generating solution: {e}", exc_info=True)
            # Return a default solution if generation fails
            return Solution(
                necessity="Unable to generate solution details",
                difficulty="medium",
                implementation_steps=["Consult with local authorities", "Gather more information"],
                estimated_impact="Unknown"
            )


class ProblemStatementGenerator:
    """Main class orchestrating the problem statement generation."""
    
    def __init__(self, google_api_key: str):
        self.news_tool = NewsSearchTool()
        self.problem_extractor = ProblemExtractor(google_api_key)
        self.solution_generator = SolutionGenerator(google_api_key)
    
    def generate_problem_statements(self, location: str, max_news: int = 10) -> List[ProblemWithSolution]:
        """
        Generate problem statements with solutions for a location.
        
        Args:
            location: The location to analyze
            max_news: Maximum number of news articles to fetch
            
        Returns:
            List of ProblemWithSolution objects
        """
        # Step 1: Search for local news
        print(f"Searching for news in {location}...")
        news_items = self.news_tool.search_local_news(location, max_news)
        
        if not news_items:
            print("No news items found")
            return []
        
        print(f"Found {len(news_items)} news articles")
        
        # Step 2: Extract problems
        print("Extracting problems from news...")
        problems = self.problem_extractor.extract_problems(news_items, location)
        
        if not problems:
            print("No problems extracted")
            return []
        
        print(f"Extracted {len(problems)} problems")
        
        # Step 3: Generate solutions
        problem_solutions = []
        for i, problem in enumerate(problems, 1):
            print(f"Generating solution for problem {i}/{len(problems)}...")
            solution = self.solution_generator.generate_solution(problem)
            problem_solutions.append(ProblemWithSolution(
                problem=problem,
                solution=solution
            ))
        
        return problem_solutions
