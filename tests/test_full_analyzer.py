
from analyzer.full_analyzer import analyze_full_code

code = """
a = 10
b = 0
print(a / b)
"""

result = analyze_full_code(code, "python")

print("\n========== EXECUTION RESULT ==========")
print(result["execution"])

print("\n========== GEMINI AI REPORT ==========")
print(result["ai_analysis"])
