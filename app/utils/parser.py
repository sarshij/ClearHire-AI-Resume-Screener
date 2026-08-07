"""
Resume Text Parser
Extracts text from PDF, TXT and DOCX files.
Features Layout-aware parsing, OCR fallback, and Language Detection.
"""
import io
import re
from app.logger import setup_logger
from langdetect import detect, LangDetectException

logger = setup_logger(__name__)

def parse_resume(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    logger.debug(f"Parsing: {filename} (format: {ext}, size: {len(file_bytes)} bytes)")
    
    text = ""
    if ext == 'pdf':
        text = parse_pdf(file_bytes)
    elif ext == 'txt':
        text = parse_txt(file_bytes)
    elif ext in ['docx', 'doc']:
        text = parse_docx(file_bytes)
    else:
        text = parse_txt(file_bytes)
        
    text = text.strip()
    
    # Language Detection
    if text:
        try:
            lang = detect(text)
            logger.debug(f"Detected language for {filename}: {lang}")
            # Multilingual SBERT will handle different languages natively
        except LangDetectException:
            logger.warning(f"Could not detect language for {filename}")
            
    return text

def parse_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber not installed")
        return "[PDF parser not available]"
        
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                # Extract text preserving layout/columns
                page_text = page.extract_text(layout=True)
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"pdfplumber failed: {e}")
        
    text = text.strip()
    
    # OCR Fallback for scanned PDFs
    if len(text) < 50:
        logger.info("PDF text too short, attempting OCR fallback...")
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            
            # OPTIMIZATION: Only OCR the first 2 pages max. 
            # OCR is extremely slow, and a real resume is rarely longer than 2 pages.
            # Processing a 20-page textbook chapter via OCR will cause a massive timeout.
            images = convert_from_bytes(file_bytes, first_page=1, last_page=2)
            ocr_text = ""
            for img in images:
                ocr_text += pytesseract.image_to_string(img) + "\n"
                
            if len(ocr_text.strip()) > len(text):
                logger.info("OCR fallback successful")
                return ocr_text.strip()
        except ImportError:
            logger.error("pytesseract or pdf2image not installed for OCR fallback")
        except Exception as e:
            logger.error(f"OCR fallback failed: {e}")
            
    return text

def parse_txt(file_bytes: bytes) -> str:
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try:
            text = file_bytes.decode(enc).strip()
            logger.debug(f"TXT parsed: {len(text)} chars (encoding: {enc})")
            return text
        except (UnicodeDecodeError, ValueError):
            continue
    logger.warning("TXT encoding detection failed, falling back to latin-1 with replace")
    return file_bytes.decode('latin-1', errors='replace').strip()

def parse_docx(file_bytes: bytes) -> str:
    try:
        import mammoth
    except ImportError:
        logger.error("mammoth not installed")
        return "[DOCX parser not available]"
        
    try:
        # Mammoth converts docx to plain text while preserving structure better
        result = mammoth.extract_raw_text(io.BytesIO(file_bytes))
        text = result.value
        logger.debug(f"DOCX parsed (mammoth): {len(text.strip())} chars")
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to parse DOCX with mammoth: {e}")
        # Fallback to python-docx if mammoth fails
        try:
            import docx
            document = docx.Document(io.BytesIO(file_bytes))
            text = '\n'.join([paragraph.text for paragraph in document.paragraphs])
            logger.debug(f"DOCX parsed (fallback): {len(text.strip())} chars")
            return text.strip()
        except Exception as fallback_e:
            logger.error(f"Fallback python-docx also failed: {fallback_e}")
            return "[DOCX parser error]"

def is_resume_format(text: str) -> bool:
    """
    Check if the text is genuinely a resume using a multi-signal scoring system.
    Evaluates contact info, section headers, NER density, structural formatting,
    and penalizes academic/proposal keywords.
    """
    if not text or len(text.strip()) < 50:
        return False
        
    lower_text = text.lower()
    score = 0
    
    # 1. Contact Information Density (Strong Signals)
    # Emails
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text):
        score += 25
    # Phone numbers (various formats, e.g., (123) 456-7890, +1 234 567 8900)
    if re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text) or re.search(r'\+\d{1,3}[-.\s]?\d{9,12}', text) or re.search(r'\b\d{10}\b', text):
        score += 20
    # URLs (LinkedIn, GitHub, Portfolio)
    if re.search(r'(linkedin\.com/in/|github\.com/|portfolio|behance\.net)', lower_text):
        score += 15
        
    # 2. Section Headers (Moderate Signals)
    education = ['education', 'university', 'college', 'bachelor', 'master', 'phd', 'coursework']
    experience = ['experience', 'employment', 'work history', 'career', 'professional background']
    skills = ['skills', 'technologies', 'certifications', 'languages', 'core competencies']
    
    if any(k in lower_text for k in education): score += 10
    if any(k in lower_text for k in experience): score += 10
    if any(k in lower_text for k in skills): score += 10
    
    # 3. Negative Keywords (Heavy Penalties for academic/proposals)
    negatives = [
        'table of contents', 'chapter', 'abstract', 'methodology', 
        'project proposal', 'concept note', 'literature review', 
        'bibliography', 'figure 1', 'hypothesis', 'introduction:',
        'midterm project', 'course syllabus', 'research question'
    ]
    for neg in negatives:
        if neg in lower_text:
            score -= 30
            logger.debug(f"Found negative keyword: {neg}")
            
    # 4. Structural Formatting Penalty (Walls of text)
    # Resumes have short bullet points. Papers have long paragraphs.
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        words_per_line = sum(len(line.split()) for line in lines) / len(lines)
        if words_per_line > 25:
            # Penalize long prose (textbooks, articles)
            score -= 25
            logger.debug(f"High words_per_line ({words_per_line:.1f}), penalizing.")
            
    # 5. Named Entity Density (spaCy NER)
    try:
        from app.utils.nlp import get_nlp_with_ruler
        nlp = get_nlp_with_ruler()
        if nlp:
            # Sample first 2000 chars for speed
            doc = nlp(text[:2000])
            orgs_dates = sum(1 for ent in doc.ents if ent.label_ in ['ORG', 'DATE', 'PERSON'])
            if orgs_dates > 5:
                score += 20
                logger.debug(f"High NER density ({orgs_dates}), rewarding.")
    except Exception as e:
        logger.warning(f"NER check failed in is_resume_format: {e}")
        
    logger.debug(f"is_resume_format final score: {score}")
    
    # A genuine resume should easily clear 45 points (e.g. Email(25) + Phone(20) = 45)
    return score >= 45

