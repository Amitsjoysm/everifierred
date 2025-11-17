from typing import List
import openpyxl
import csv
from io import BytesIO
import re


def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def extract_emails_from_csv(file_content: bytes) -> List[str]:
    """Extract emails from CSV file"""
    emails = []
    try:
        content = file_content.decode('utf-8')
        reader = csv.reader(content.splitlines())
        for row in reader:
            for cell in row:
                if is_valid_email(cell.strip()):
                    emails.append(cell.strip())
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")
    return emails


def extract_emails_from_excel(file_content: bytes) -> List[str]:
    """Extract emails from Excel file"""
    emails = []
    try:
        wb = openpyxl.load_workbook(BytesIO(file_content))
        ws = wb.active
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str) and is_valid_email(cell.value.strip()):
                    emails.append(cell.value.strip())
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")
    return emails


def extract_emails_from_text(text: str) -> List[str]:
    """Extract emails from plain text"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    return list(set(emails))  # Remove duplicates
