import re
import unicodedata
from typing import List, Union, Optional

class TextProcessor:
    @staticmethod
    def clean_text(text: Union[str, None], 
                   lowercase: bool = True, 
                   remove_special_chars: bool = True,
                   trim_whitespace: bool = True) -> str:
        """
        Comprehensive text cleaning method
        
        Args:
            text: Input text to clean
            lowercase: Convert to lowercase
            remove_special_chars: Remove special characters
            trim_whitespace: Remove extra whitespaces
        
        Returns:
            Cleaned text
        """
        if text is None:
            return ""
        
        # Convert to string (in case of non-string input)
        text = str(text)
        
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove non-printable characters
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        # Lowercase
        if lowercase:
            text = text.lower()
        
        # Remove special characters (keeping Thai and English letters, numbers, spaces)
        if remove_special_chars:
            text = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s]', '', text)
        
        # Trim whitespace
        if trim_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def normalize_responsibilities(responsibilities: List[str]) -> List[str]:
        """
        Normalize list of responsibilities
        
        Args:
            responsibilities: List of responsibility strings
        
        Returns:
            Normalized list of responsibilities
        """
        normalized = []
        for resp in responsibilities:
            # Clean the responsibility
            cleaned_resp = TextProcessor.clean_text(resp)
            
            # Skip very short or empty responsibilities
            if len(cleaned_resp) < 5:
                continue
            
            # Remove numbered or bulleted prefixes
            cleaned_resp = re.sub(r'^[\d•\-*]+\s*', '', cleaned_resp)
            
            # Capitalize first letter
            cleaned_resp = cleaned_resp.capitalize()
            
            # Avoid duplicates
            if cleaned_resp and cleaned_resp not in normalized:
                normalized.append(cleaned_resp)
        
        return normalized
    
    @staticmethod
    def normalize_skills(skills: Union[str, List[str]]) -> List[str]:
        """
        Normalize skills to a consistent format
        
        Args:
            skills: Skills as a string or list of strings
        
        Returns:
            List of normalized skills
        """
        # Convert to list if it's a string
        if isinstance(skills, str):
            # Split by common delimiters
            skills = re.split(r'[,;/]', skills)
        
        normalized_skills = []
        for skill in skills:
            # Clean the skill
            cleaned_skill = TextProcessor.clean_text(skill)
            
            # Skip very short or empty skills
            if len(cleaned_skill) < 2:
                continue
            
            # Remove prefixes like "skill in", "knowledge of", etc.
            cleaned_skill = re.sub(r'^(skill in|knowledge of|expertise in)\s*', '', cleaned_skill)
            
            # Capitalize first letter
            cleaned_skill = cleaned_skill.capitalize()
            
            # Avoid duplicates
            if cleaned_skill and cleaned_skill not in normalized_skills:
                normalized_skills.append(cleaned_skill)
        
        return normalized_skills
    
    @staticmethod
    def extract_salary_range(salary_str: str) -> Optional[dict]:
        """
        Extract salary range from a string
        
        Args:
            salary_str: Salary string 
        
        Returns:
            Dictionary with min and max salary or None
        """
        # Remove any non-numeric characters except comma and hyphen
        clean_salary = re.sub(r'[^\d,\-]', '', salary_str)
        
        # Try to extract salary range
        range_match = re.match(r'(\d+(?:,\d+)?)\s*-\s*(\d+(?:,\d+)?)', clean_salary)
        
        if range_match:
            return {
                'min_salary': int(range_match.group(1).replace(',', '')),
                'max_salary': int(range_match.group(2).replace(',', '')),
                'original_range': salary_str
            }
        
        return None
    
    @staticmethod
    def normalize_job_titles(titles: List[str]) -> List[str]:
        """
        Normalize job titles
        
        Args:
            titles: List of job titles
        
        Returns:
            List of normalized job titles
        """
        normalized_titles = []
        for title in titles:
            # Clean the title
            cleaned_title = TextProcessor.clean_text(title, lowercase=False)
            
            # Remove common prefixes/suffixes
            cleaned_title = re.sub(r'^(senior|junior|mid-level|entry-level)\s*', '', cleaned_title, flags=re.IGNORECASE)
            
            # Capitalize each word
            cleaned_title = ' '.join(word.capitalize() for word in cleaned_title.split())
            
            # Special handling for technical acronyms
            special_acronyms = {
                'Ui': 'UI',
                'Ux': 'UX',
                'Api': 'API',
                'Qa': 'QA',
                'It': 'IT'
            }
            for old, new in special_acronyms.items():
                cleaned_title = cleaned_title.replace(old, new)
            
            # Avoid duplicates
            if cleaned_title and cleaned_title not in normalized_titles:
                normalized_titles.append(cleaned_title)
        
        return normalized_titles

# Example usage
def main():
    # Text Cleaning Example
    original_text = "  Hello, World! 🌍 こんにちは  "
    cleaned_text = TextProcessor.clean_text(original_text)
    print(f"Original: {original_text}")
    print(f"Cleaned: {cleaned_text}")

    # Responsibilities Normalization
    responsibilities = [
        "• Develop web applications",
        "1. Maintain software systems",
        "Debug and fix issues"
    ]
    normalized_resp = TextProcessor.normalize_responsibilities(responsibilities)
    print("\nNormalized Responsibilities:")
    print(normalized_resp)

    # Skills Normalization
    skills = "Python, JavaScript; skill in machine learning, Cloud computing"
    normalized_skills = TextProcessor.normalize_skills(skills)
    print("\nNormalized Skills:")
    print(normalized_skills)

    # Salary Range Extraction
    salary_range = TextProcessor.extract_salary_range("30,000 - 60,000 THB")
    print("\nSalary Range:")
    print(salary_range)

    # Job Titles Normalization
    titles = [
        "Senior Software Engineer",
        "UI/UX Designer",
        "IT Project Manager"
    ]
    normalized_titles = TextProcessor.normalize_job_titles(titles)
    print("\nNormalized Job Titles:")
    print(normalized_titles)

if __name__ == "__main__":
    main()