"""
Streamlit Web UI for Problem Statement Generator.
"""
import os
import json
import streamlit as st
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv
from psgen import ProblemStatementGenerator

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Problem Statement Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .problem-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1f77b4;
    }
    .solution-card {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        border-left: 5px solid #2ca02c;
    }
    .severity-critical {
        color: #d62728;
        font-weight: bold;
    }
    .severity-high {
        color: #ff7f0e;
        font-weight: bold;
    }
    .severity-medium {
        color: #ffbb00;
        font-weight: bold;
    }
    .severity-low {
        color: #2ca02c;
        font-weight: bold;
    }
    .difficulty-hard {
        color: #d62728;
    }
    .difficulty-medium {
        color: #ff7f0e;
    }
    .difficulty-easy {
        color: #2ca02c;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'problems_generated' not in st.session_state:
    st.session_state.problems_generated = False
if 'problem_solutions' not in st.session_state:
    st.session_state.problem_solutions = []
if 'selected_location' not in st.session_state:
    st.session_state.selected_location = None


def create_map(center_lat=20.5937, center_lon=78.9629, zoom=4):
    """Create a folium map centered on India."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )
    
    # Add click functionality instructions
    folium.Marker(
        [center_lat, center_lon],
        popup="Click anywhere on the map to select a location",
        tooltip="Select a location",
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)
    
    return m


def get_location_name(lat, lon):
    """Get approximate location name from coordinates."""
    # This is a simple approximation. In production, use reverse geocoding API
    return f"Location ({lat:.4f}, {lon:.4f})"


def display_problem(problem_solution, index):
    """Display a problem with its solution."""
    problem = problem_solution.problem
    solution = problem_solution.solution
    
    # Severity color class
    severity_class = f"severity-{problem.severity}"
    
    st.markdown(f"""
    <div class="problem-card">
        <h3>Problem #{index}: {problem.description}</h3>
        <p><strong>Location:</strong> {problem.location}</p>
        <p><strong>People Affected:</strong> {problem.affected_people:,}</p>
        <p><strong>Severity:</strong> <span class="{severity_class}">{problem.severity.upper()}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    if solution:
        difficulty_class = f"difficulty-{solution.difficulty}"
        
        st.markdown(f"""
        <div class="solution-card">
            <h4>💡 Solution</h4>
            <p><strong>Necessity:</strong> {solution.necessity}</p>
            <p><strong>Difficulty:</strong> <span class="{difficulty_class}">{solution.difficulty.upper()}</span></p>
            <p><strong>Estimated Impact:</strong> {solution.estimated_impact}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Implementation Steps:**")
        for i, step in enumerate(solution.implementation_steps, 1):
            st.markdown(f"{i}. {step}")


def main():
    """Main application."""
    
    # Header
    st.markdown('<div class="main-header">🔍 Problem Statement Generator</div>', unsafe_allow_html=True)
    st.markdown("Find local problems and get AI-powered solution suggestions")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Google GenAI API Key",
            type="password",
            value=os.getenv("GOOGLE_API_KEY", ""),
            help="Enter your Google GenerativeAI API key"
        )
        
        # Number of news articles
        max_news = st.slider(
            "Number of News Articles",
            min_value=5,
            max_value=20,
            value=10,
            help="Maximum number of news articles to analyze"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool uses:
        - 🔍 DuckDuckGo for news search
        - 🤖 Google GenAI for analysis
        - 📊 Pydantic for validation
        - 🗺️ Interactive map selection
        """)
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["🗺️ Select Location", "📋 View Problems & Solutions"])
    
    with tab1:
        st.markdown('<div class="sub-header">Step 1: Select Location on Map</div>', unsafe_allow_html=True)
        st.markdown("Click on the map to select a location for analysis")
        
        # Create and display map
        map_obj = create_map()
        map_data = st_folium(map_obj, width=700, height=500)
        
        # Get clicked location
        if map_data and map_data.get('last_clicked'):
            lat = map_data['last_clicked']['lat']
            lon = map_data['last_clicked']['lng']
            location_name = get_location_name(lat, lon)
            
            st.success(f"✅ Selected location: {location_name}")
            st.session_state.selected_location = location_name
            
            # Option to enter custom location name
            custom_location = st.text_input(
                "Or enter a specific location name:",
                value="",
                placeholder="e.g., Mumbai, India"
            )
            
            if custom_location:
                st.session_state.selected_location = custom_location
                st.info(f"Using custom location: {custom_location}")
        
        # Generate button
        if st.session_state.selected_location:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Generate Problem Statements", type="primary", use_container_width=True):
                    if not api_key:
                        st.error("❌ Please enter your Google GenAI API key in the sidebar")
                    else:
                        # Generate problem statements
                        with st.spinner("🔄 Searching for news and analyzing problems..."):
                            try:
                                generator = ProblemStatementGenerator(api_key)
                                problem_solutions = generator.generate_problem_statements(
                                    st.session_state.selected_location,
                                    max_news
                                )
                                
                                if problem_solutions:
                                    st.session_state.problem_solutions = problem_solutions
                                    st.session_state.problems_generated = True
                                    st.success(f"✅ Found {len(problem_solutions)} problems with solutions!")
                                    st.info("👉 Switch to the 'View Problems & Solutions' tab to see results")
                                else:
                                    st.warning("⚠️ No problems found for this location. Try a different area.")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.markdown('<div class="sub-header">Step 2: Review Problems & Solutions</div>', unsafe_allow_html=True)
        
        if not st.session_state.problems_generated:
            st.info("ℹ️ Please select a location and generate problem statements first")
        else:
            st.markdown(f"**Location:** {st.session_state.selected_location}")
            st.markdown(f"**Total Problems Found:** {len(st.session_state.problem_solutions)}")
            st.markdown("---")
            
            # Display all problems and solutions
            for i, prob_sol in enumerate(st.session_state.problem_solutions, 1):
                display_problem(prob_sol, i)
                st.markdown("---")
            
            # Download option
            if st.session_state.problem_solutions:
                # Prepare data for download
                export_data = []
                for ps in st.session_state.problem_solutions:
                    export_data.append({
                        "problem": ps.problem.model_dump(),
                        "solution": ps.solution.model_dump() if ps.solution else None
                    })
                
                json_str = json.dumps(export_data, indent=2)
                st.download_button(
                    label="📥 Download Results as JSON",
                    data=json_str,
                    file_name=f"problems_{st.session_state.selected_location.replace(' ', '_')}.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()
