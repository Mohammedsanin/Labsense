import re
import logging

def parse_blood_test_results(text: str) -> dict:
    """Parse blood test results from extracted text"""
    results = {}
    
    patterns = {
        'Hemoglobin': r'(?:hemoglobin|hb|hgb)[\s:]*(\d+\.?\d*)\s*(?:g/dl|gm/dl)?',
        'Glucose': r'(?:glucose|sugar|blood sugar)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
        'WBC': r'(?:wbc|white blood cell|leucocyte)[\s:]*(\d+\.?\d*)\s*(?:cells/cumm|/μl|thou/ul)?',
        'RBC': r'(?:rbc|red blood cell|erythrocyte)[\s:]*(\d+\.?\d*)\s*(?:mill/cumm|/μl)?',
        'Platelets': r'(?:platelet|plt)[\s:]*(\d+\.?\d*)\s*(?:lakhs/cumm|thou/ul|/μl)?',
        'Cholesterol': r'(?:cholesterol|total cholesterol)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
        'HDL': r'(?:hdl|hdl cholesterol)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
        'LDL': r'(?:ldl|ldl cholesterol)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
        'Triglycerides': r'(?:triglycerides|tg)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
        'Creatinine': r'(?:creatinine|creat)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
        'Urea': r'(?:urea|blood urea)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
        'TSH': r'(?:tsh|thyroid)[\s:]*(\d+\.?\d*)\s*(?:μIU/ml|mIU/L)?',
    }
    
    text_lower = text.lower()
    
    for test_name, pattern in patterns.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            value = match.group(1)
            results[test_name] = {
                'value': value,
                'unit': get_unit(test_name)
            }
    
    return results

def get_unit(test_name: str) -> str:
    """Get standard units for blood test parameters"""
    units = {
        'Hemoglobin': 'g/dL',
        'Glucose': 'mg/dL',
        'WBC': 'thou/μL',
        'RBC': 'mill/μL',
        'Platelets': 'thou/μL',
        'Cholesterol': 'mg/dL',
        'HDL': 'mg/dL',
        'LDL': 'mg/dL',
        'Triglycerides': 'mg/dL',
        'Creatinine': 'mg/dL',
        'Urea': 'mg/dL',
        'TSH': 'μIU/mL',
    }
    return units.get(test_name, '')

def get_normal_ranges() -> dict:
    """Return normal reference ranges for blood tests"""
    return {
        'Hemoglobin': {'min': 12.0, 'max': 17.0, 'unit': 'g/dL'},
        'Glucose': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
        'WBC': {'min': 4.0, 'max': 11.0, 'unit': 'thou/μL'},
        'RBC': {'min': 4.2, 'max': 6.1, 'unit': 'mill/μL'},
        'Platelets': {'min': 150, 'max': 400, 'unit': 'thou/μL'},
        'Cholesterol': {'min': 0, 'max': 200, 'unit': 'mg/dL'},
        'HDL': {'min': 40, 'max': 1000, 'unit': 'mg/dL'},
        'LDL': {'min': 0, 'max': 100, 'unit': 'mg/dL'},
        'Triglycerides': {'min': 0, 'max': 150, 'unit': 'mg/dL'},
        'Creatinine': {'min': 0.6, 'max': 1.2, 'unit': 'mg/dL'},
        'Urea': {'min': 7, 'max': 20, 'unit': 'mg/dL'},
        'TSH': {'min': 0.4, 'max': 4.0, 'unit': 'μIU/mL'},
    }

def determine_status(test_name: str, value: float) -> str:
    """Determine if test result is normal, high, or low"""
    ranges = get_normal_ranges()
    
    if test_name not in ranges:
        return "Unknown"
    
    normal_range = ranges[test_name]
    
    if value < normal_range['min']:
        return "Low"
    elif value > normal_range['max']:
        return "High"
    else:
        return "Normal"
