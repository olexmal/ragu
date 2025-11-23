"""
Code Example Extraction Module
Extracts and highlights code examples from documentation.
"""
import re
from typing import List, Dict, Any, Optional
from .utils import setup_logging

logger = setup_logging()


def extract_code_blocks(text: str) -> List[Dict[str, Any]]:
    """
    Extract code blocks from text (markdown, HTML, or plain text).
    
    Args:
        text: Text content to extract code from
        
    Returns:
        List of code blocks with metadata
    """
    code_blocks = []
    
    # Extract markdown code blocks
    markdown_pattern = r'```(\w+)?\n(.*?)```'
    for match in re.finditer(markdown_pattern, text, re.DOTALL):
        language = match.group(1) or 'text'
        code = match.group(2).strip()
        code_blocks.append({
            'code': code,
            'language': language,
            'type': 'markdown',
            'start_pos': match.start(),
            'end_pos': match.end()
        })
    
    # Extract HTML <pre><code> blocks
    html_pattern = r'<pre><code(?:\s+class="language-(\w+)")?>(.*?)</code></pre>'
    for match in re.finditer(html_pattern, text, re.DOTALL | re.IGNORECASE):
        language = match.group(1) or 'text'
        code = match.group(2).strip()
        # Decode HTML entities
        import html
        code = html.unescape(code)
        code_blocks.append({
            'code': code,
            'language': language,
            'type': 'html',
            'start_pos': match.start(),
            'end_pos': match.end()
        })
    
    # Extract inline code (for short examples)
    inline_pattern = r'`([^`]+)`'
    for match in re.finditer(inline_pattern, text):
        code = match.group(1)
        if len(code) > 10:  # Only include substantial inline code
            code_blocks.append({
                'code': code,
                'language': 'text',
                'type': 'inline',
                'start_pos': match.start(),
                'end_pos': match.end()
            })
    
    return code_blocks


def extract_java_examples(text: str) -> List[Dict[str, Any]]:
    """
    Extract Java code examples specifically.
    
    Args:
        text: Text content to extract Java code from
        
    Returns:
        List of Java code examples
    """
    java_blocks = []
    
    # Extract Java class definitions
    java_class_pattern = r'(public\s+(?:abstract\s+)?(?:class|interface|enum)\s+\w+.*?\{.*?\})'
    for match in re.finditer(java_class_pattern, text, re.DOTALL):
        java_blocks.append({
            'code': match.group(1),
            'language': 'java',
            'type': 'class',
            'start_pos': match.start(),
            'end_pos': match.end()
        })
    
    # Extract method definitions
    java_method_pattern = r'(public\s+(?:static\s+)?\w+\s+\w+\s*\([^)]*\)\s*\{[^}]*\})'
    for match in re.finditer(java_method_pattern, text, re.DOTALL):
        java_blocks.append({
            'code': match.group(1),
            'language': 'java',
            'type': 'method',
            'start_pos': match.start(),
            'end_pos': match.end()
        })
    
    # Also get code blocks marked as Java
    all_blocks = extract_code_blocks(text)
    java_blocks.extend([
        block for block in all_blocks
        if block['language'].lower() in ['java', 'javacode', 'java-code']
    ])
    
    return java_blocks


def highlight_code(code: str, language: str = 'text') -> str:
    """
    Simple code highlighting (basic syntax highlighting).
    For production, consider using Pygments library.
    
    Args:
        code: Code to highlight
        language: Programming language
        
    Returns:
        Highlighted code (currently returns as-is, can be enhanced)
    """
    # Basic keyword highlighting for Java
    if language.lower() == 'java':
        keywords = ['public', 'private', 'protected', 'class', 'interface', 
                   'extends', 'implements', 'return', 'if', 'else', 'for', 
                   'while', 'try', 'catch', 'finally', 'throw', 'throws',
                   'import', 'package', 'static', 'final', 'abstract']
        
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            code = re.sub(pattern, f'**{keyword}**', code)
    
    return code


def extract_code_from_document(doc_content: str, language: str = None) -> Dict[str, Any]:
    """
    Extract all code examples from a document.
    
    Args:
        doc_content: Document content
        language: Filter by specific language (optional)
        
    Returns:
        Dictionary with extracted code blocks
    """
    if language and language.lower() == 'java':
        code_blocks = extract_java_examples(doc_content)
    else:
        code_blocks = extract_code_blocks(doc_content)
    
    if language:
        code_blocks = [b for b in code_blocks if b['language'].lower() == language.lower()]
    
    return {
        'total_blocks': len(code_blocks),
        'blocks': code_blocks,
        'languages': list(set(b['language'] for b in code_blocks))
    }


def format_code_for_response(code_block: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a code block for API response.
    
    Args:
        code_block: Code block dictionary
        
    Returns:
        Formatted code block
    """
    return {
        'code': code_block['code'],
        'language': code_block['language'],
        'type': code_block.get('type', 'unknown'),
        'length': len(code_block['code']),
        'highlighted': highlight_code(code_block['code'], code_block['language'])
    }

