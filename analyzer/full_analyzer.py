
from executor.code_executor import execute_code
from analyzer.ai_analyzer import analyze_code


def analyze_full_code(code, language, user_input=""):

    execution_result = execute_code(
        code,
        language,
        user_input=user_input
    )

    ai_report = analyze_code(
        code,
        language,
        execution_result
    )

    return {
        "language": language,
        "execution": execution_result,
        "ai_analysis": ai_report
    }
