
from analyzer.ai_analyzer import analyze_code

code = """
class Main {
    public static void main(String[] args) {
        int number = 10;
        System.out.println(number);
    }
}
"""

print("Testing corrected Java code...")
result = analyze_code(code, "Java")
print(result)
