
from executor.code_executor import execute_code

print("\nTEST 1: Python Runtime Error")

python_code = """
a = 10
b = 0
print(a / b)
"""

print(execute_code(python_code, "python"))


print("\nTEST 2: C Compilation Error")

c_code = """
#include <stdio.h>

int main() {
    int a = 10
    printf("%d", a);
    return 0;
}
"""

print(execute_code(c_code, "c"))
