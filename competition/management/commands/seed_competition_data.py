from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import ParticipantProfile
from competition.models import (
    CompetitionSettings, Round, Question, MCQOption,
    CodingChallenge, FlowchartQuestion, TestCase, ParticipantRound
)
from results.models import RoundResult

class Command(BaseCommand):
    help = "Seeds complete questions, rounds, competition settings, and demo users for BUG HUNTERS."

    def handle(self, *args, **kwargs):
        self.stdout.write("Initializing BUG HUNTERS Competition Data...")

        # 1. Setup Competition Settings
        settings = CompetitionSettings.get_settings()
        settings.title = "BUG HUNTERS 2026"
        settings.tagline = "Think Smart. Debug Fast. Code Better."
        settings.college_name = "National Institute of Technology"
        settings.r1_qualifying_marks = 9
        settings.r1_total_questions = 15
        settings.r1_time_per_question_seconds = 60
        settings.r2_qualifying_marks = 15
        settings.r2_total_questions = 5
        settings.r2_time_per_question_seconds = 300
        settings.r3_total_questions = 3
        settings.r3_time_per_question_seconds = 600
        settings.leaderboard_published = True
        settings.save()
        self.stdout.write(self.style.SUCCESS("✓ Competition Settings configured."))

        # 2. Setup Rounds
        Round.objects.all().delete()
        r1 = Round.objects.create(
            round_number=1,
            name="Code Quest",
            tagline="Multiple Choice Questions Challenge",
            description="Test your programming fundamentals across C, Python, and Java. 15 questions with 1 minute per question. Minimum qualifying score: 9/15.",
            difficulty="MEDIUM",
            total_questions=15,
            marks_per_question=1.0,
            total_marks=15.0,
            time_per_question_minutes=1,
            qualifying_marks=9.0,
            is_active=True
        )

        r2 = Round.objects.create(
            round_number=2,
            name="Bug Bounty",
            tagline="Error Line Coding & Debugging",
            description="Examine buggy code snippets, identify subtle compiler, syntax, and algorithmic logic errors, and rewrite clean working code. Choose your language: C, Python, or Java.",
            difficulty="HARD",
            total_questions=5,
            marks_per_question=5.0,
            total_marks=25.0,
            time_per_question_minutes=5,
            qualifying_marks=15.0,
            is_active=True
        )

        r3 = Round.objects.create(
            round_number=3,
            name="Logic Launch",
            tagline="Visual Flowchart to Executable Code",
            description="Analyze visual algorithmic flowcharts with branching logic, state transitions, and loops, then construct fully functional programs passing hidden test cases.",
            difficulty="VERY_HARD",
            total_questions=3,
            marks_per_question=10.0,
            total_marks=30.0,
            time_per_question_minutes=10,
            qualifying_marks=0.0,
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS("✓ 3 Competition Rounds created."))

        # 3. Seed Round 1: 15 Medium MCQs
        Question.objects.all().delete()
        mcq_data = [
            {
                "order": 1,
                "category": "Python",
                "text": "What is the output of the following Python snippet?\n\ndef func(val, item_list=[]):\n    item_list.append(val)\n    return item_list\n\nprint(func(10))\nprint(func(20))",
                "explanation": "In Python, default parameter values are evaluated once when the function is defined, not each time it is called. Thus, item_list persists and accumulates values across calls.",
                "options": [
                    ("A", "[10]\n[20]", False),
                    ("B", "[10]\n[10, 20]", True),
                    ("C", "[10]\n[10]", False),
                    ("D", "TypeError: default list mutation", False)
                ]
            },
            {
                "order": 2,
                "category": "C",
                "text": "What is the printed value of the following C program?\n\n#include <stdio.h>\nint main() {\n    int arr[] = {10, 20, 30, 40, 50};\n    int *ptr = arr + 1;\n    printf(\"%d\", *(ptr + 2));\n    return 0;\n}",
                "explanation": "arr + 1 points to arr[1] (20). Then *(ptr + 2) accesses arr[1 + 2] = arr[3], which is 40.",
                "options": [
                    ("A", "30", False),
                    ("B", "20", False),
                    ("C", "40", True),
                    ("D", "50", False)
                ]
            },
            {
                "order": 3,
                "category": "Java",
                "text": "What will be the output of the following Java code?\n\nString s1 = \"BugHunter\";\nString s2 = new String(\"BugHunter\");\nSystem.out.println((s1 == s2) + \" \" + s1.equals(s2));",
                "explanation": "s1 is stored in the String Constant Pool, while s2 refers to a new object allocated on the heap. '==' checks reference identity (false), while equals() checks content equivalence (true).",
                "options": [
                    ("A", "true true", False),
                    ("B", "false true", True),
                    ("C", "false false", False),
                    ("D", "true false", False)
                ]
            },
            {
                "order": 4,
                "category": "Python",
                "text": "In Python, what is the output of the following expression?\n\nnums = [1, 2, 3, 4, 5, 6]\nprint(nums[::-2])",
                "explanation": "The slice [::-2] starts from the last element and steps backward by 2: index 5 (6), index 3 (4), index 1 (2) -> [6, 4, 2].",
                "options": [
                    ("A", "[6, 4, 2]", True),
                    ("B", "[5, 3, 1]", False),
                    ("C", "[1, 3, 5]", False),
                    ("D", "[6, 5, 4, 3, 2, 1]", False)
                ]
            },
            {
                "order": 5,
                "category": "C",
                "text": "What will be the output of the following code snippet in C?\n\nint a = 5, b = 2;\nint res = a++ * ++b;\nprintf(\"%d %d %d\", res, a, b);",
                "explanation": "a++ uses current value 5, then increments a to 6. ++b increments b from 2 to 3, then uses 3. res = 5 * 3 = 15. a = 6, b = 3.",
                "options": [
                    ("A", "18 6 3", False),
                    ("B", "15 6 3", True),
                    ("C", "15 5 3", False),
                    ("D", "12 6 2", False)
                ]
            },
            {
                "order": 6,
                "category": "Java",
                "text": "What does the following Java snippet print?\n\ntry {\n    int a = 10 / 0;\n} catch (ArithmeticException e) {\n    System.out.print(\"Catch \");\n} finally {\n    System.out.print(\"Finally \");\n}\nSystem.out.print(\"Done\");",
                "explanation": "The exception is caught printing 'Catch ', then the finally block always executes printing 'Finally ', followed by normal flow 'Done'.",
                "options": [
                    ("A", "Catch Finally Done", True),
                    ("B", "Catch Done", False),
                    ("C", "Finally Done", False),
                    ("D", "Compilation Error", False)
                ]
            },
            {
                "order": 7,
                "category": "Logic",
                "text": "What is the time complexity of the following code snippet?\n\nint count = 0;\nfor (int i = 1; i <= n; i *= 2) {\n    for (int j = 1; j <= i; j++) {\n        count++;\n    }\n}",
                "explanation": "The inner loop runs 1 + 2 + 4 + ... + 2^k times, where 2^k <= n. The sum of geometric series 1 + 2 + 4 + ... + n is 2n - 1, which is O(n).",
                "options": [
                    ("A", "O(n log n)", False),
                    ("B", "O(n)", True),
                    ("C", "O(log n)", False),
                    ("D", "O(n^2)", False)
                ]
            },
            {
                "order": 8,
                "category": "C",
                "text": "What will be the output of the following bitwise operation in C?\n\nunsigned int x = 12; // Binary: 0000 1100\nunsigned int res = x ^ (x >> 2);\nprintf(\"%u\", res);",
                "explanation": "x = 12 (1100 in binary). x >> 2 = 3 (0011 in binary). 1100 XOR 0011 = 1111 in binary = 15 in decimal.",
                "options": [
                    ("A", "15", True),
                    ("B", "12", False),
                    ("C", "9", False),
                    ("D", "3", False)
                ]
            },
            {
                "order": 9,
                "category": "Python",
                "text": "What is the output of the following code?\n\nd = {'a': 1, 'b': 2}\nprint(d.get('c', 3) + d.setdefault('c', 4))\nprint(d['c'])",
                "explanation": "d.get('c', 3) returns 3 without mutating d. Then d.setdefault('c', 4) inserts 'c': 4 and returns 4. 3 + 4 = 7. Finally d['c'] is 4.",
                "options": [
                    ("A", "7\n4", True),
                    ("B", "7\n3", False),
                    ("C", "6\n4", False),
                    ("D", "KeyError on 'c'", False)
                ]
            },
            {
                "order": 10,
                "category": "Java",
                "text": "In Java, what is the output of the following method call?\n\nstatic int test() {\n    try {\n        return 1;\n    } finally {\n        return 2;\n    }\n}",
                "explanation": "A return statement in a finally block takes precedence over and overrides the return statement in the try block, returning 2.",
                "options": [
                    ("A", "1", False),
                    ("B", "2", True),
                    ("C", "Compilation error: unreachable return", False),
                    ("D", "3", False)
                ]
            },
            {
                "order": 11,
                "category": "C",
                "text": "What does a 'Dangling Pointer' represent in C?",
                "explanation": "A dangling pointer points to a memory location that has already been deallocated or freed.",
                "options": [
                    ("A", "A pointer that has not been initialized to any address", False),
                    ("B", "A pointer that points to deallocated memory", True),
                    ("C", "A pointer with NULL value", False),
                    ("D", "A pointer pointing to a read-only constant memory segment", False)
                ]
            },
            {
                "order": 12,
                "category": "Python",
                "text": "What is the output of this Python generator expression?\n\ngen = (x * 2 for x in range(3))\nprint(list(gen))\nprint(list(gen))",
                "explanation": "A generator is an iterator that is exhausted once consumed. The first list(gen) produces [0, 2, 4], and the second yields an empty list [].",
                "options": [
                    ("A", "[0, 2, 4]\n[]", True),
                    ("B", "[0, 2, 4]\n[0, 2, 4]", False),
                    ("C", "TypeError: generator object not iterable twice", False),
                    ("D", "[0, 1, 2]\n[]", False)
                ]
            },
            {
                "order": 13,
                "category": "Java",
                "text": "Which collection in Java preserves insertion order, allows duplicate elements, and permits null elements?",
                "explanation": "ArrayList implements List and preserves the sequence of inserted elements while allowing duplicates and nulls.",
                "options": [
                    ("A", "HashSet", False),
                    ("B", "TreeSet", False),
                    ("C", "ArrayList", True),
                    ("D", "HashMap", False)
                ]
            },
            {
                "order": 14,
                "category": "Logic",
                "text": "What is the output of the recursive function call mystery(48, 18)?\n\nint mystery(int a, int b) {\n    if (b == 0) return a;\n    return mystery(b, a % b);\n}",
                "explanation": "This is Euclid's algorithm for Greatest Common Divisor (GCD). GCD(48, 18) = GCD(18, 12) = GCD(12, 6) = GCD(6, 0) = 6.",
                "options": [
                    ("A", "12", False),
                    ("B", "6", True),
                    ("C", "3", False),
                    ("D", "2", False)
                ]
            },
            {
                "order": 15,
                "category": "Python",
                "text": "What is the output of the following list comprehension?\n\nmatrix = [[1, 2], [3, 4]]\nflatten = [num for row in matrix for num in row if num % 2 == 0]\nprint(flatten)",
                "explanation": "Nested list comprehension loops over rows, then each num in row, filtering for even numbers: 2 and 4.",
                "options": [
                    ("A", "[2, 4]", True),
                    ("B", "[1, 3]", False),
                    ("C", "[[2], [4]]", False),
                    ("D", "[4, 2]", False)
                ]
            }
        ]

        for q in mcq_data:
            question_obj = Question.objects.create(
                order=q["order"],
                category=q["category"],
                question_text=q["text"],
                explanation=q["explanation"],
                marks=1.0
            )
            for opt_id, text, is_correct in q["options"]:
                MCQOption.objects.create(
                    question=question_obj,
                    identifier=opt_id,
                    option_text=text,
                    is_correct=is_correct
                )
        self.stdout.write(self.style.SUCCESS(f"✓ 15 Round 1 MCQs created."))

        # 4. Seed Round 2: Bug Bounty (5 for C, 5 for Python, 5 for Java = 15 challenges)
        CodingChallenge.objects.all().delete()
        TestCase.objects.all().delete()

        # Python Challenges
        py_challenges = [
            {
                "title": "Palindrome String Validator",
                "description": "Fix the bug in the palindrome verification function. The function should ignore spaces and case sensitivity, and return 'True' or 'False'.",
                "language": "python",
                "buggy_code": "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    n = len(s)\n    for i in range(n):\n        # BUG: Off-by-one error in indexing from the end\n        if s[i] != s[n - i]:\n            return False\n    return True\n\nline = input().strip()\nprint(is_palindrome(line))",
                "corrected": "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    n = len(s)\n    for i in range(n // 2):\n        if s[i] != s[n - 1 - i]:\n            return False\n    return True\n\nline = input().strip()\nprint(is_palindrome(line))",
                "cases": [
                    ("racecar", "True", False),
                    ("hello", "False", False),
                    ("A man a plan a canal panama", "True", True),
                ]
            },
            {
                "title": "Array Two-Sum Target Indexer",
                "description": "Find the zero-based indices of two distinct elements in a space-separated array that sum up to target. Output the indices in ascending order separated by a space.",
                "language": "python",
                "buggy_code": "def two_sum(nums, target):\n    seen = {}\n    for i in range(len(nums)):\n        diff = target - nums[i]\n        # BUG: checking index instead of value and reversed storage\n        if i in seen:\n            return [seen[i], diff]\n        seen[i] = nums[i]\n    return []\n\ntarget = int(input().strip())\nnums = list(map(int, input().strip().split()))\nres = two_sum(nums, target)\nprint(f\"{res[0]} {res[1]}\")",
                "corrected": "def two_sum(nums, target):\n    seen = {}\n    for i in range(len(nums)):\n        diff = target - nums[i]\n        if diff in seen:\n            return [seen[diff], i]\n        seen[nums[i]] = i\n    return []\n\ntarget = int(input().strip())\nnums = list(map(int, input().strip().split()))\nres = two_sum(nums, target)\nprint(f\"{res[0]} {res[1]}\")",
                "cases": [
                    ("9\n2 7 11 15", "0 1", False),
                    ("6\n3 2 4", "1 2", False),
                    ("10\n1 5 3 7 9", "2 3", True),
                ]
            },
            {
                "title": "Fibonacci Term Calculator",
                "description": "Compute the N-th Fibonacci number where Fib(0)=0 and Fib(1)=1. The current recursive code has incorrect base returns and missing termination.",
                "language": "python",
                "buggy_code": "def fib(n):\n    # BUG: incorrect base cases\n    if n == 0:\n        return 1\n    if n == 1:\n        return 0\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return b\n\nn = int(input().strip())\nprint(fib(n))",
                "corrected": "def fib(n):\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n\nn = int(input().strip())\nprint(fib(n))",
                "cases": [
                    ("0", "0", False),
                    ("7", "13", False),
                    ("10", "55", True),
                ]
            },
            {
                "title": "Character Frequency Aggregator",
                "description": "Output the character frequencies in the given string formatted as 'char:count' sorted alphabetically by character.",
                "language": "python",
                "buggy_code": "s = input().strip()\ncounts = {}\nfor ch in s:\n    # BUG: crashes on unseen characters\n    counts[ch] = counts[ch] + 1\n\nfor k in sorted(counts.keys()):\n    print(f\"{k}:{counts[k]}\")",
                "corrected": "s = input().strip()\ncounts = {}\nfor ch in s:\n    counts[ch] = counts.get(ch, 0) + 1\n\nfor k in sorted(counts.keys()):\n    print(f\"{k}:{counts[k]}\")",
                "cases": [
                    ("banana", "a:3\nb:1\nn:2", False),
                    ("code", "c:1\nd:1\ne:1\no:1", False),
                    ("mississippi", "i:4\nm:1\np:2\ns:4", True),
                ]
            },
            {
                "title": "Square Matrix Transpose",
                "description": "Given N followed by an N x N matrix, print its transpose. The current implementation has a shallow row replication bug.",
                "language": "python",
                "buggy_code": "n = int(input().strip())\nmatrix = []\nfor _ in range(n):\n    matrix.append(list(map(int, input().strip().split())))\n\n# BUG: All rows reference the same memory list\ntransposed = [[0] * n] * n\nfor i in range(n):\n    for j in range(n):\n        transposed[j][i] = matrix[i][j]\n\nfor row in transposed:\n    print(' '.join(map(str, row)))",
                "corrected": "n = int(input().strip())\nmatrix = []\nfor _ in range(n):\n    matrix.append(list(map(int, input().strip().split())))\n\ntransposed = [[0 for _ in range(n)] for _ in range(n)]\nfor i in range(n):\n    for j in range(n):\n        transposed[j][i] = matrix[i][j]\n\nfor row in transposed:\n    print(' '.join(map(str, row)))",
                "cases": [
                    ("2\n1 2\n3 4", "1 3\n2 4", False),
                    ("3\n1 2 3\n4 5 6\n7 8 9", "1 4 7\n2 5 8\n3 6 9", True),
                ]
            }
        ]

        # C Challenges
        c_challenges = [
            {
                "title": "In-Place String Inversion",
                "description": "Reverse a null-terminated string in place. Fix the pointer/indexing error and loop boundary condition.",
                "language": "c",
                "buggy_code": "#include <stdio.h>\n#include <string.h>\n\nvoid reverse(char str[]) {\n    int len = strlen(str);\n    // BUG: loops through entire string reversing twice, and off-by-one with <= len\n    for (int i = 0; i <= len; i++) {\n        char temp = str[i];\n        str[i] = str[len - i];\n        str[len - i] = temp;\n    }\n}\n\nint main() {\n    char str[200];\n    if (fgets(str, sizeof(str), stdin)) {\n        str[strcspn(str, \"\\r\\n\")] = 0;\n        reverse(str);\n        printf(\"%s\\n\", str);\n    }\n    return 0;\n}",
                "corrected": "#include <stdio.h>\n#include <string.h>\n\nvoid reverse(char str[]) {\n    int len = strlen(str);\n    for (int i = 0; i < len / 2; i++) {\n        char temp = str[i];\n        str[i] = str[len - 1 - i];\n        str[len - 1 - i] = temp;\n    }\n}\n\nint main() {\n    char str[200];\n    if (fgets(str, sizeof(str), stdin)) {\n        str[strcspn(str, \"\\r\\n\")] = 0;\n        reverse(str);\n        printf(\"%s\\n\", str);\n    }\n    return 0;\n}",
                "cases": [
                    ("algorithm", "mhtirogla", False),
                    ("cyber", "rebyc", False),
                    ("debugging", "gniggubed", True),
                ]
            },
            {
                "title": "Binary Search Index Locator",
                "description": "Search for a target value in a sorted array of N numbers. Print the zero-based index or -1 if not found. Fix the infinite loop bug in bounds updating.",
                "language": "c",
                "buggy_code": "#include <stdio.h>\n\nint binary_search(int arr[], int n, int target) {\n    int low = 0, high = n - 1;\n    while (low <= high) {\n        int mid = (low + high) / 2;\n        if (arr[mid] == target) {\n            return mid;\n        } else if (arr[mid] < target) {\n            // BUG: causes infinite loop\n            low = mid;\n        } else {\n            high = mid;\n        }\n    }\n    return -1;\n}\n\nint main() {\n    int n, target;\n    if (scanf(\"%d %d\", &n, &target) == 2) {\n        int arr[100];\n        for (int i = 0; i < n; i++) {\n            scanf(\"%d\", &arr[i]);\n        }\n        printf(\"%d\\n\", binary_search(arr, n, target));\n    }\n    return 0;\n}",
                "corrected": "#include <stdio.h>\n\nint binary_search(int arr[], int n, int target) {\n    int low = 0, high = n - 1;\n    while (low <= high) {\n        int mid = low + (high - low) / 2;\n        if (arr[mid] == target) {\n            return mid;\n        } else if (arr[mid] < target) {\n            low = mid + 1;\n        } else {\n            high = mid - 1;\n        }\n    }\n    return -1;\n}\n\nint main() {\n    int n, target;\n    if (scanf(\"%d %d\", &n, &target) == 2) {\n        int arr[100];\n        for (int i = 0; i < n; i++) {\n            scanf(\"%d\", &arr[i]);\n        }\n        printf(\"%d\\n\", binary_search(arr, n, target));\n    }\n    return 0;\n}",
                "cases": [
                    ("5 30\n10 20 30 40 50", "2", False),
                    ("4 25\n10 20 30 40", "-1", False),
                    ("6 100\n5 12 45 78 99 100", "5", True),
                ]
            },
            {
                "title": "Prime Number Verifier",
                "description": "Determine if a given positive integer N is prime. Print 'PRIME' or 'NOT PRIME'. Fix boundary conditions and loop bounds.",
                "language": "c",
                "buggy_code": "#include <stdio.h>\n\nint is_prime(int n) {\n    // BUG: Missing 1 check and division by zero on i=0\n    for (int i = 0; i < n; i++) {\n        if (n % i == 0) return 0;\n    }\n    return 1;\n}\n\nint main() {\n    int n;\n    if (scanf(\"%d\", &n) == 1) {\n        if (is_prime(n)) printf(\"PRIME\\n\");\n        else printf(\"NOT PRIME\\n\");\n    }\n    return 0;\n}",
                "corrected": "#include <stdio.h>\n\nint is_prime(int n) {\n    if (n <= 1) return 0;\n    for (int i = 2; i * i <= n; i++) {\n        if (n % i == 0) return 0;\n    }\n    return 1;\n}\n\nint main() {\n    int n;\n    if (scanf(\"%d\", &n) == 1) {\n        if (is_prime(n)) printf(\"PRIME\\n\");\n        else printf(\"NOT PRIME\\n\");\n    }\n    return 0;\n}",
                "cases": [
                    ("17", "PRIME", False),
                    ("1", "NOT PRIME", False),
                    ("49", "NOT PRIME", True),
                ]
            },
            {
                "title": "Maximum Subarray Sum (Kadane)",
                "description": "Find the maximum sum of a contiguous subarray in an array of N integers. Fix negative array initialization bug.",
                "language": "c",
                "buggy_code": "#include <stdio.h>\n\nint max_subarray(int arr[], int n) {\n    // BUG: max_so_far initialized to 0 fails when all numbers are negative\n    int max_so_far = 0;\n    int curr_max = 0;\n    for (int i = 0; i < n; i++) {\n        curr_max += arr[i];\n        if (curr_max < 0) curr_max = 0;\n        if (curr_max > max_so_far) max_so_far = curr_max;\n    }\n    return max_so_far;\n}\n\nint main() {\n    int n;\n    if (scanf(\"%d\", &n) == 1) {\n        int arr[100];\n        for (int i = 0; i < n; i++) scanf(\"%d\", &arr[i]);\n        printf(\"%d\\n\", max_subarray(arr, n));\n    }\n    return 0;\n}",
                "corrected": "#include <stdio.h>\n\nint max_subarray(int arr[], int n) {\n    int max_so_far = arr[0];\n    int curr_max = arr[0];\n    for (int i = 1; i < n; i++) {\n        curr_max = (arr[i] > curr_max + arr[i]) ? arr[i] : curr_max + arr[i];\n        if (curr_max > max_so_far) max_so_far = curr_max;\n    }\n    return max_so_far;\n}\n\nint main() {\n    int n;\n    if (scanf(\"%d\", &n) == 1) {\n        int arr[100];\n        for (int i = 0; i < n; i++) scanf(\"%d\", &arr[i]);\n        printf(\"%d\\n\", max_subarray(arr, n));\n    }\n    return 0;\n}",
                "cases": [
                    ("5\n-2 -3 -1 -5 -4", "-1", False),
                    ("6\n-2 1 -3 4 -1 2", "5", False),
                    ("4\n1 2 3 4", "10", True),
                ]
            },
            {
                "title": "Factorial of Large Integers",
                "description": "Calculate N! for N up to 20 without 32-bit integer overflow. Fix datatype.",
                "language": "c",
                "buggy_code": "#include <stdio.h>\n\n// BUG: 32-bit int overflows for N > 12\nint factorial(int n) {\n    int res = 1;\n    for (int i = 1; i <= n; i++) {\n        res *= i;\n    }\n    return res;\n}\n\nint main() {\n    int n;\n    if (scanf(\"%d\", &n) == 1) {\n        printf(\"%d\\n\", factorial(n));\n    }\n    return 0;\n}",
                "corrected": "#include <stdio.h>\n\nlong long factorial(int n) {\n    long long res = 1;\n    for (int i = 1; i <= n; i++) {\n        res *= i;\n    }\n    return res;\n}\n\nint main() {\n    int n;\n    if (scanf(\"%d\", &n) == 1) {\n        printf(\"%lld\\n\", factorial(n));\n    }\n    return 0;\n}",
                "cases": [
                    ("5", "120", False),
                    ("15", "1307674368000", True),
                ]
            }
        ]

        # Java Challenges
        java_challenges = [
            {
                "title": "Balanced Parentheses Checker",
                "description": "Verify if brackets '()', '{}', '[]' are balanced in a string. Print 'VALID' or 'INVALID'. Fix empty stack pop exception.",
                "language": "java",
                "buggy_code": "import java.util.*;\n\npublic class Solution {\n    public static boolean isValid(String s) {\n        Stack<Character> stack = new Stack<>();\n        for (char c : s.toCharArray()) {\n            if (c == '(' || c == '{' || c == '[') {\n                stack.push(c);\n            } else {\n                // BUG: Throws EmptyStackException on strings starting with closing brackets\n                char top = stack.pop();\n                if (c == ')' && top != '(') return false;\n                if (c == '}' && top != '{') return false;\n                if (c == ']' && top != '[') return false;\n            }\n        }\n        return stack.isEmpty();\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) {\n            String s = sc.nextLine().trim();\n            System.out.println(isValid(s) ? \"VALID\" : \"INVALID\");\n        }\n    }\n}",
                "corrected": "import java.util.*;\n\npublic class Solution {\n    public static boolean isValid(String s) {\n        Stack<Character> stack = new Stack<>();\n        for (char c : s.toCharArray()) {\n            if (c == '(' || c == '{' || c == '[') {\n                stack.push(c);\n            } else if (c == ')' || c == '}' || c == ']') {\n                if (stack.isEmpty()) return false;\n                char top = stack.pop();\n                if (c == ')' && top != '(') return false;\n                if (c == '}' && top != '{') return false;\n                if (c == ']' && top != '[') return false;\n            }\n        }\n        return stack.isEmpty();\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) {\n            String s = sc.nextLine().trim();\n            System.out.println(isValid(s) ? \"VALID\" : \"INVALID\");\n        }\n    }\n}",
                "cases": [
                    ("{[()]}", "VALID", False),
                    ("({[)]}", "INVALID", False),
                    (")(", "INVALID", True),
                ]
            },
            {
                "title": "Bubble Sort Boundary Exception",
                "description": "Sort an array of integers ascending. Fix the array index out of bounds error in the inner loop condition.",
                "language": "java",
                "buggy_code": "import java.util.*;\n\npublic class Solution {\n    public static void bubbleSort(int[] arr) {\n        int n = arr.length;\n        for (int i = 0; i < n; i++) {\n            // BUG: j + 1 causes ArrayIndexOutOfBoundsException\n            for (int j = 0; j < n; j++) {\n                if (arr[j] > arr[j + 1]) {\n                    int temp = arr[j];\n                    arr[j] = arr[j + 1];\n                    arr[j + 1] = temp;\n                }\n            }\n        }\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int n = sc.nextInt();\n            int[] arr = new int[n];\n            for (int i = 0; i < n; i++) arr[i] = sc.nextInt();\n            bubbleSort(arr);\n            for (int i = 0; i < n; i++) {\n                System.out.print(arr[i] + (i == n - 1 ? \"\" : \" \"));\n            }\n            System.out.println();\n        }\n    }\n}",
                "corrected": "import java.util.*;\n\npublic class Solution {\n    public static void bubbleSort(int[] arr) {\n        int n = arr.length;\n        for (int i = 0; i < n - 1; i++) {\n            for (int j = 0; j < n - 1 - i; j++) {\n                if (arr[j] > arr[j + 1]) {\n                    int temp = arr[j];\n                    arr[j] = arr[j + 1];\n                    arr[j + 1] = temp;\n                }\n            }\n        }\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int n = sc.nextInt();\n            int[] arr = new int[n];\n            for (int i = 0; i < n; i++) arr[i] = sc.nextInt();\n            bubbleSort(arr);\n            for (int i = 0; i < n; i++) {\n                System.out.print(arr[i] + (i == n - 1 ? \"\" : \" \"));\n            }\n            System.out.println();\n        }\n    }\n}",
                "cases": [
                    ("4\n4 3 2 1", "1 2 3 4", False),
                    ("5\n10 1 5 3 8", "1 3 5 8 10", True),
                ]
            },
            {
                "title": "String Word Frequency Counter",
                "description": "Count occurrences of words separated by spaces. Output in alphabetical order as 'word:count'. Fix string equality bug.",
                "language": "java",
                "buggy_code": "import java.util.*;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) {\n            String[] words = sc.nextLine().trim().split(\"\\\\s+\");\n            Map<String, Integer> map = new TreeMap<>();\n            for (String w : words) {\n                // BUG: == reference equality or unboxed null pointer\n                Integer count = map.get(w);\n                if (count == null) map.put(w, 1);\n                else map.put(w, count + 1);\n            }\n            for (Map.Entry<String, Integer> entry : map.entrySet()) {\n                System.out.println(entry.getKey() + \":\" + entry.getValue());\n            }\n        }\n    }\n}",
                "corrected": "import java.util.*;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLine()) {\n            String line = sc.nextLine().trim();\n            if (line.isEmpty()) return;\n            String[] words = line.split(\"\\\\s+\");\n            Map<String, Integer> map = new TreeMap<>();\n            for (String w : words) {\n                map.put(w, map.getOrDefault(w, 0) + 1);\n            }\n            for (Map.Entry<String, Integer> entry : map.entrySet()) {\n                System.out.println(entry.getKey() + \":\" + entry.getValue());\n            }\n        }\n    }\n}",
                "cases": [
                    ("java code java hunter", "code:1\nhunter:1\njava:2", False),
                    ("apple banana apple", "apple:2\nbanana:1", True),
                ]
            },
            {
                "title": "Power of a Number (x^n)",
                "description": "Calculate x raised to power n for non-negative integers x and n. Fix incorrect loop initialization.",
                "language": "java",
                "buggy_code": "import java.util.*;\n\npublic class Solution {\n    public static long power(long x, int n) {\n        // BUG: result initialized to 0 gives 0 for any power\n        long res = 0;\n        for (int i = 0; i < n; i++) {\n            res *= x;\n        }\n        return res;\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long x = sc.nextLong();\n            int n = sc.nextInt();\n            System.out.println(power(x, n));\n        }\n    }\n}",
                "corrected": "import java.util.*;\n\npublic class Solution {\n    public static long power(long x, int n) {\n        if (n == 0) return 1;\n        long res = 1;\n        for (int i = 0; i < n; i++) {\n            res *= x;\n        }\n        return res;\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long x = sc.nextLong();\n            int n = sc.nextInt();\n            System.out.println(power(x, n));\n        }\n    }\n}",
                "cases": [
                    ("2 5", "32", False),
                    ("5 0", "1", False),
                    ("3 4", "81", True),
                ]
            },
            {
                "title": "Array Second Largest Finder",
                "description": "Find the second largest unique element in an array of N integers. Print the value, or -1 if no distinct second largest exists.",
                "language": "java",
                "buggy_code": "import java.util.*;\n\npublic class Solution {\n    public static int getSecondLargest(int[] arr) {\n        int first = -1, second = -1;\n        for (int x : arr) {\n            // BUG: fails if duplicates or incorrect condition\n            if (x > first) {\n                first = x;\n            } else if (x > second) {\n                second = x;\n            }\n        }\n        return second;\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int n = sc.nextInt();\n            int[] arr = new int[n];\n            for (int i = 0; i < n; i++) arr[i] = sc.nextInt();\n            System.out.println(getSecondLargest(arr));\n        }\n    }\n}",
                "corrected": "import java.util.*;\n\npublic class Solution {\n    public static int getSecondLargest(int[] arr) {\n        int first = Integer.MIN_VALUE, second = Integer.MIN_VALUE;\n        for (int x : arr) {\n            if (x > first) {\n                second = first;\n                first = x;\n            } else if (x > second && x != first) {\n                second = x;\n            }\n        }\n        return (second == Integer.MIN_VALUE) ? -1 : second;\n    }\n\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int n = sc.nextInt();\n            int[] arr = new int[n];\n            for (int i = 0; i < n; i++) arr[i] = sc.nextInt();\n            System.out.println(getSecondLargest(arr));\n        }\n    }\n}",
                "cases": [
                    ("5\n12 35 1 10 34", "34", False),
                    ("3\n10 10 10", "-1", True),
                ]
            }
        ]

        all_challenges = py_challenges + c_challenges + java_challenges
        for idx, item in enumerate(all_challenges):
            ch = CodingChallenge.objects.create(
                title=item["title"],
                description=item["description"],
                language=item["language"],
                buggy_code=item["buggy_code"],
                corrected_reference_code=item["corrected"],
                marks=5.0,
                order=(idx % 5) + 1
            )
            for in_d, out_d, hidden in item["cases"]:
                TestCase.objects.create(
                    coding_challenge=ch,
                    input_data=in_d,
                    expected_output=out_d,
                    is_hidden=hidden
                )
        self.stdout.write(self.style.SUCCESS(f"✓ 15 Round 2 Coding Challenges (C, Python, Java) created."))

        # 5. Seed Round 3: Logic Launch (3 for C, 3 for Python, 3 for Java = 9 questions)
        FlowchartQuestion.objects.all().delete()

        svg_collatz = """<svg viewBox="0 0 500 420" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradP" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f0ff" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#0072ff" stop-opacity="0.3"/>
    </linearGradient>
  </defs>
  <!-- Start Oval -->
  <rect x="180" y="10" width="140" height="40" rx="20" fill="url(#gradP)" stroke="#00f0ff" stroke-width="2"/>
  <text x="250" y="35" text-anchor="middle" fill="#ffffff" font-size="14" font-weight="bold">START (Read N)</text>
  
  <line x1="250" y1="50" x2="250" y2="80" stroke="#00f0ff" stroke-width="2" marker-end="url(#arrow)"/>
  
  <!-- Process Box: Init -->
  <rect x="150" y="80" width="200" height="45" rx="6" fill="#0d1b2a" stroke="#0072ff" stroke-width="2"/>
  <text x="250" y="100" text-anchor="middle" fill="#e0e1dd" font-size="13">steps = 0; peak = N</text>
  <text x="250" y="118" text-anchor="middle" fill="#90e0ef" font-size="11">Track maximum peak reached</text>
  
  <line x1="250" y1="125" x2="250" y2="155" stroke="#00f0ff" stroke-width="2"/>

  <!-- Decision: N == 1 ? -->
  <polygon points="250,155 330,195 250,235 170,195" fill="#1b263b" stroke="#00f0ff" stroke-width="2"/>
  <text x="250" y="200" text-anchor="middle" fill="#ffffff" font-size="13" font-weight="bold">N == 1 ?</text>

  <!-- Yes branch -> End -->
  <line x1="330" y1="195" x2="420" y2="195" stroke="#00f0ff" stroke-width="2"/>
  <text x="360" y="185" fill="#48cae4" font-size="12">YES</text>
  <rect x="360" y="250" width="120" height="45" rx="20" fill="#03045e" stroke="#00f0ff" stroke-width="2"/>
  <text x="420" y="278" text-anchor="middle" fill="#ffffff" font-size="13">Print steps, peak</text>
  <line x1="420" y1="195" x2="420" y2="250" stroke="#00f0ff" stroke-width="2"/>

  <!-- No branch -> Check Even/Odd -->
  <line x1="250" y1="235" x2="250" y2="270" stroke="#00f0ff" stroke-width="2"/>
  <text x="260" y="255" fill="#48cae4" font-size="12">NO</text>
  <polygon points="250,270 320,305 250,340 180,305" fill="#1b263b" stroke="#7209b7" stroke-width="2"/>
  <text x="250" y="310" text-anchor="middle" fill="#ffffff" font-size="12">N % 2 == 0 ?</text>

  <!-- Left: N / 2, Right: 3N + 1 -->
  <line x1="180" y1="305" x2="110" y2="305" stroke="#00f0ff" stroke-width="2"/>
  <rect x="40" y="285" width="110" height="40" rx="4" fill="#0d1b2a" stroke="#00f0ff" stroke-width="1.5"/>
  <text x="95" y="310" text-anchor="middle" fill="#90e0ef" font-size="12">N = N / 2</text>

  <line x1="320" y1="305" x2="350" y2="305" stroke="#00f0ff" stroke-width="2"/>
  <rect x="350" y="285" width="110" height="40" rx="4" fill="#0d1b2a" stroke="#00f0ff" stroke-width="1.5"/>
  <text x="405" y="310" text-anchor="middle" fill="#90e0ef" font-size="12">N = 3*N + 1</text>

  <!-- Loop back -->
  <path d="M 95 325 L 95 380 L 250 380 L 250 140" fill="none" stroke="#00f0ff" stroke-dasharray="4,4" stroke-width="1.5"/>
  <text x="175" y="395" text-anchor="middle" fill="#48cae4" font-size="11">Increment steps; peak = max(peak, N); repeat</text>
</svg>"""

        svg_base_convert = """<svg viewBox="0 0 500 380" xmlns="http://www.w3.org/2000/svg">
  <!-- Start -->
  <rect x="170" y="10" width="160" height="40" rx="20" fill="#03045e" stroke="#00f0ff" stroke-width="2"/>
  <text x="250" y="35" text-anchor="middle" fill="#ffffff" font-size="14" font-weight="bold">START (Read D, B)</text>
  
  <line x1="250" y1="50" x2="250" y2="85" stroke="#00f0ff" stroke-width="2"/>

  <!-- Process -->
  <rect x="150" y="85" width="200" height="40" rx="5" fill="#0d1b2a" stroke="#0072ff" stroke-width="2"/>
  <text x="250" y="110" text-anchor="middle" fill="#e0e1dd" font-size="13">digits = [] ; temp = D</text>

  <line x1="250" y1="125" x2="250" y2="160" stroke="#00f0ff" stroke-width="2"/>

  <!-- Decision: temp > 0 -->
  <polygon points="250,160 330,195 250,230 170,195" fill="#1b263b" stroke="#00f0ff" stroke-width="2"/>
  <text x="250" y="200" text-anchor="middle" fill="#ffffff" font-size="13">temp &gt; 0 ?</text>

  <!-- Loop body -->
  <line x1="170" y1="195" x2="100" y2="195" stroke="#00f0ff" stroke-width="2"/>
  <rect x="20" y="170" width="140" height="50" rx="5" fill="#0d1b2a" stroke="#00f0ff" stroke-width="1.5"/>
  <text x="90" y="192" text-anchor="middle" fill="#90e0ef" font-size="11">rem = temp % B</text>
  <text x="90" y="210" text-anchor="middle" fill="#90e0ef" font-size="11">temp = temp / B</text>
  <path d="M 90 220 L 90 250 L 250 250 L 250 230" fill="none" stroke="#00f0ff" stroke-width="1.5"/>

  <!-- False branch -->
  <line x1="330" y1="195" x2="390" y2="195" stroke="#00f0ff" stroke-width="2"/>
  <rect x="340" y="250" width="140" height="45" rx="20" fill="#03045e" stroke="#00f0ff" stroke-width="2"/>
  <text x="410" y="278" text-anchor="middle" fill="#ffffff" font-size="12">Reverse &amp; Print</text>
  <line x1="410" y1="195" x2="410" y2="250" stroke="#00f0ff" stroke-width="2"/>
</svg>"""

        svg_pascal = """<svg viewBox="0 0 500 360" xmlns="http://www.w3.org/2000/svg">
  <rect x="170" y="10" width="160" height="40" rx="20" fill="#03045e" stroke="#00f0ff" stroke-width="2"/>
  <text x="250" y="35" text-anchor="middle" fill="#ffffff" font-size="14" font-weight="bold">START (Read Row N)</text>
  <line x1="250" y1="50" x2="250" y2="90" stroke="#00f0ff" stroke-width="2"/>

  <rect x="150" y="90" width="200" height="45" rx="6" fill="#0d1b2a" stroke="#0072ff" stroke-width="2"/>
  <text x="250" y="112" text-anchor="middle" fill="#e0e1dd" font-size="13">row = [1]; val = 1</text>
  <text x="250" y="128" text-anchor="middle" fill="#90e0ef" font-size="11">Loop k from 1 to N</text>

  <line x1="250" y1="135" x2="250" y2="175" stroke="#00f0ff" stroke-width="2"/>

  <polygon points="250,175 330,210 250,245 170,210" fill="#1b263b" stroke="#00f0ff" stroke-width="2"/>
  <text x="250" y="215" text-anchor="middle" fill="#ffffff" font-size="13">k &lt;= N ?</text>

  <line x1="170" y1="210" x2="110" y2="210" stroke="#00f0ff" stroke-width="2"/>
  <rect x="10" y="185" width="160" height="50" rx="5" fill="#0d1b2a" stroke="#00f0ff" stroke-width="1.5"/>
  <text x="90" y="206" text-anchor="middle" fill="#90e0ef" font-size="11">val = val * (N - k + 1) / k</text>
  <text x="90" y="224" text-anchor="middle" fill="#90e0ef" font-size="11">row.append(val)</text>

  <path d="M 90 235 L 90 270 L 250 270 L 250 245" fill="none" stroke="#00f0ff" stroke-width="1.5"/>

  <line x1="330" y1="210" x2="410" y2="210" stroke="#00f0ff" stroke-width="2"/>
  <rect x="340" y="270" width="140" height="45" rx="20" fill="#03045e" stroke="#00f0ff" stroke-width="2"/>
  <text x="410" y="298" text-anchor="middle" fill="#ffffff" font-size="12">Print row space-sep</text>
  <line x1="410" y1="210" x2="410" y2="270" stroke="#00f0ff" stroke-width="2"/>
</svg>"""

        flowchart_problems = [
            # Python
            {
                "language": "python",
                "title": "Collatz Sequence Extrema Tracker",
                "desc": "Translate the visual flowchart into a complete program. Read an integer N. Apply the 3N+1 Collatz logic until reaching 1. Output the total transformation steps followed by the maximum peak value reached, space-separated on one line.",
                "svg": svg_collatz,
                "input_spec": "A single positive integer N (1 <= N <= 100000).",
                "output_spec": "Two space-separated integers: steps and peak.",
                "sample_in": "6",
                "sample_out": "8 16",
                "starter": "import sys\n\n# Read input integer N\nline = sys.stdin.read().strip()\nif line:\n    n = int(line)\n    # TODO: Implement the Collatz sequence logic based on the flowchart\n    pass\n",
                "ref": "import sys\nline = sys.stdin.read().strip()\nif line:\n    n = int(line)\n    steps = 0\n    peak = n\n    curr = n\n    while curr != 1:\n        if curr % 2 == 0:\n            curr = curr // 2\n        else:\n            curr = 3 * curr + 1\n        if curr > peak:\n            peak = curr\n        steps += 1\n    print(f\"{steps} {peak}\")\n",
                "cases": [
                    ("6", "8 16", False),
                    ("1", "0 1", False),
                    ("19", "20 88", True),
                ]
            },
            {
                "language": "python",
                "title": "Arbitrary Base Digit Transmutation",
                "desc": "Implement the base transformation algorithm depicted in the flowchart. Read a decimal integer D and target base B (2 <= B <= 16). For digits above 9, use uppercase characters 'A' through 'F'. Output the converted representation.",
                "svg": svg_base_convert,
                "input_spec": "Two integers D and B separated by space.",
                "output_spec": "String representation in base B.",
                "sample_in": "255 16",
                "sample_out": "FF",
                "starter": "import sys\n# TODO: Convert D to base B according to the flowchart\n",
                "ref": "import sys\nline = sys.stdin.read().strip()\nif line:\n    d, b = map(int, line.split())\n    if d == 0:\n        print('0')\n    else:\n        digits = []\n        hex_chars = '0123456789ABCDEF'\n        temp = d\n        while temp > 0:\n            rem = temp % b\n            digits.append(hex_chars[rem])\n            temp //= b\n        print(''.join(reversed(digits)))\n",
                "cases": [
                    ("255 16", "FF", False),
                    ("10 2", "1010", False),
                    ("75 8", "113", True),
                ]
            },
            {
                "language": "python",
                "title": "Pascal's Triangle Row Synthesizer",
                "desc": "Follow the mathematical recurrence in the flowchart to compute the N-th row of Pascal's triangle (0-indexed). Output all elements separated by a single space.",
                "svg": svg_pascal,
                "input_spec": "A single non-negative integer N (0 <= N <= 30).",
                "output_spec": "The N-th row of Pascal's triangle formatted with single spaces.",
                "sample_in": "4",
                "sample_out": "1 4 6 4 1",
                "starter": "import sys\n# TODO: Synthesize N-th row of Pascal's triangle\n",
                "ref": "import sys\nline = sys.stdin.read().strip()\nif line:\n    n = int(line)\n    row = [1]\n    val = 1\n    for k in range(1, n + 1):\n        val = val * (n - k + 1) // k\n        row.append(val)\n    print(' '.join(map(str, row)))\n",
                "cases": [
                    ("4", "1 4 6 4 1", False),
                    ("0", "1", False),
                    ("6", "1 6 15 20 15 6 1", True),
                ]
            },

            # C
            {
                "language": "c",
                "title": "Collatz Sequence Extrema Tracker (C)",
                "desc": "Translate the visual flowchart into a robust C program. Read positive integer N from stdin, apply Collatz 3N+1 rules until N reaches 1, and print total steps and maximum peak reached.",
                "svg": svg_collatz,
                "input_spec": "A single integer N.",
                "output_spec": "Two space-separated integers: steps peak",
                "sample_in": "6",
                "sample_out": "8 16",
                "starter": "#include <stdio.h>\n\nint main() {\n    long long n;\n    if (scanf(\"%lld\", &n) == 1) {\n        // TODO: Implement logic from flowchart\n    }\n    return 0;\n}\n",
                "ref": "#include <stdio.h>\n\nint main() {\n    long long n;\n    if (scanf(\"%lld\", &n) == 1) {\n        long long steps = 0;\n        long long peak = n;\n        long long curr = n;\n        while (curr != 1) {\n            if (curr % 2 == 0) {\n                curr = curr / 2;\n            } else {\n                curr = 3 * curr + 1;\n            }\n            if (curr > peak) peak = curr;\n            steps++;\n        }\n        printf(\"%lld %lld\\n\", steps, peak);\n    }\n    return 0;\n}\n",
                "cases": [
                    ("6", "8 16", False),
                    ("1", "0 1", False),
                    ("19", "20 88", True),
                ]
            },
            {
                "language": "c",
                "title": "Arbitrary Base Digit Transmutation (C)",
                "desc": "Implement the base transformation flowchart in C. Convert decimal integer D to base B (2 <= B <= 16). Use characters 0-9 and A-F.",
                "svg": svg_base_convert,
                "input_spec": "Two space-separated integers: D and B.",
                "output_spec": "Converted string representation.",
                "sample_in": "255 16",
                "sample_out": "FF",
                "starter": "#include <stdio.h>\n\nint main() {\n    // TODO: Implement base conversion\n    return 0;\n}\n",
                "ref": "#include <stdio.h>\n#include <string.h>\n\nint main() {\n    long long d;\n    int b;\n    if (scanf(\"%lld %d\", &d, &b) == 2) {\n        if (d == 0) {\n            printf(\"0\\n\");\n            return 0;\n        }\n        char hex_chars[] = \"0123456789ABCDEF\";\n        char buffer[100];\n        int idx = 0;\n        while (d > 0) {\n            buffer[idx++] = hex_chars[d % b];\n            d /= b;\n        }\n        for (int i = idx - 1; i >= 0; i--) {\n            putchar(buffer[i]);\n        }\n        putchar('\\n');\n    }\n    return 0;\n}\n",
                "cases": [
                    ("255 16", "FF", False),
                    ("10 2", "1010", False),
                    ("75 8", "113", True),
                ]
            },
            {
                "language": "c",
                "title": "Pascal's Triangle Row Synthesizer (C)",
                "desc": "Construct the N-th row of Pascal's triangle in C using 64-bit integers and the sequential multiplicative formula from the flowchart.",
                "svg": svg_pascal,
                "input_spec": "A single integer N (0 <= N <= 30).",
                "output_spec": "Space-separated row values.",
                "sample_in": "4",
                "sample_out": "1 4 6 4 1",
                "starter": "#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf(\"%d\", &n) == 1) {\n        // TODO: Compute Pascal row\n    }\n    return 0;\n}\n",
                "ref": "#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf(\"%d\", &n) == 1) {\n        long long val = 1;\n        printf(\"1\");\n        for (int k = 1; k <= n; k++) {\n            val = val * (n - k + 1) / k;\n            printf(\" %lld\", val);\n        }\n        printf(\"\\n\");\n    }\n    return 0;\n}\n",
                "cases": [
                    ("4", "1 4 6 4 1", False),
                    ("0", "1", False),
                    ("6", "1 6 15 20 15 6 1", True),
                ]
            },

            # Java
            {
                "language": "java",
                "title": "Collatz Sequence Extrema Tracker (Java)",
                "desc": "Translate the visual flowchart into a clean Java class named Solution. Output steps and peak reached.",
                "svg": svg_collatz,
                "input_spec": "A single integer N.",
                "output_spec": "Two space-separated integers: steps peak",
                "sample_in": "6",
                "sample_out": "8 16",
                "starter": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long n = sc.nextLong();\n            // TODO: Flowchart logic\n        }\n    }\n}\n",
                "ref": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long n = sc.nextLong();\n            long steps = 0;\n            long peak = n;\n            long curr = n;\n            while (curr != 1) {\n                if (curr % 2 == 0) {\n                    curr = curr / 2;\n                } else {\n                    curr = 3 * curr + 1;\n                }\n                if (curr > peak) peak = curr;\n                steps++;\n            }\n            System.out.println(steps + \" \" + peak);\n        }\n    }\n}\n",
                "cases": [
                    ("6", "8 16", False),
                    ("1", "0 1", False),
                    ("19", "20 88", True),
                ]
            },
            {
                "language": "java",
                "title": "Arbitrary Base Digit Transmutation (Java)",
                "desc": "Implement the base transformation flowchart in Java. Convert decimal D to base B (2 to 16).",
                "svg": svg_base_convert,
                "input_spec": "Two integers D and B.",
                "output_spec": "Base B string representation.",
                "sample_in": "255 16",
                "sample_out": "FF",
                "starter": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        // TODO\n    }\n}\n",
                "ref": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextLong()) {\n            long d = sc.nextLong();\n            int b = sc.nextInt();\n            if (d == 0) {\n                System.out.println(\"0\");\n                return;\n            }\n            String hexChars = \"0123456789ABCDEF\";\n            StringBuilder sb = new StringBuilder();\n            long temp = d;\n            while (temp > 0) {\n                int rem = (int)(temp % b);\n                sb.append(hexChars.charAt(rem));\n                temp /= b;\n            }\n            System.out.println(sb.reverse().toString());\n        }\n    }\n}\n",
                "cases": [
                    ("255 16", "FF", False),
                    ("10 2", "1010", False),
                    ("75 8", "113", True),
                ]
            },
            {
                "language": "java",
                "title": "Pascal's Triangle Row Synthesizer (Java)",
                "desc": "Construct the N-th row of Pascal's triangle in Java based on the provided flowchart.",
                "svg": svg_pascal,
                "input_spec": "A single integer N (0 <= N <= 30).",
                "output_spec": "N-th row values space-separated.",
                "sample_in": "4",
                "sample_out": "1 4 6 4 1",
                "starter": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        // TODO\n    }\n}\n",
                "ref": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        if (sc.hasNextInt()) {\n            int n = sc.nextInt();\n            long val = 1;\n            System.out.print(\"1\");\n            for (int k = 1; k <= n; k++) {\n                val = val * (n - k + 1) / k;\n                System.out.print(\" \" + val);\n            }\n            System.out.println();\n        }\n    }\n}\n",
                "cases": [
                    ("4", "1 4 6 4 1", False),
                    ("0", "1", False),
                    ("6", "1 6 15 20 15 6 1", True),
                ]
            }
        ]

        for idx, item in enumerate(flowchart_problems):
            fq = FlowchartQuestion.objects.create(
                title=item["title"],
                description=item["desc"],
                language=item["language"],
                flowchart_svg=item["svg"],
                input_specification=item["input_spec"],
                output_specification=item["output_spec"],
                sample_input=item["sample_in"],
                sample_output=item["sample_out"],
                starter_template=item["starter"],
                reference_solution=item["ref"],
                marks=10.0,
                order=(idx % 3) + 1
            )
            for in_d, out_d, hidden in item["cases"]:
                TestCase.objects.create(
                    flowchart_question=fq,
                    input_data=in_d,
                    expected_output=out_d,
                    is_hidden=hidden
                )
        self.stdout.write(self.style.SUCCESS(f"✓ 9 Round 3 Flowchart Challenges (C, Python, Java) created."))

        # 6. Create Default Admin & Sample Participant
        if not User.objects.filter(username="admin").exists():
            admin_user = User.objects.create_superuser("admin", "admin@bughunters.edu", "admin123")
            ParticipantProfile.objects.create(
                user=admin_user,
                full_name="Competition Administrator",
                roll_number="ADMIN-001",
                department="Computer Science & Engineering",
                year="4th Year"
            )
            self.stdout.write(self.style.SUCCESS("✓ Superuser created: admin / admin123"))

        # Sample registered participant for instant testing
        if not User.objects.filter(username="hunter1").exists():
            demo_user = User.objects.create_user("hunter1", "hunter1@college.edu", "hunter123")
            ParticipantProfile.objects.create(
                user=demo_user,
                full_name="Alex Chen",
                roll_number="22CS104",
                department="Computer Science & Engineering",
                year="3rd Year"
            )
            ParticipantRound.objects.create(
                participant=demo_user,
                round_number=1,
                status='UNLOCKED',
                total_possible_score=15.0
            )
            ParticipantRound.objects.create(
                participant=demo_user,
                round_number=2,
                status='LOCKED',
                total_possible_score=25.0
            )
            ParticipantRound.objects.create(
                participant=demo_user,
                round_number=3,
                status='LOCKED',
                total_possible_score=30.0
            )
            RoundResult.objects.create(participant=demo_user)
            self.stdout.write(self.style.SUCCESS("✓ Demo participant created: hunter1 / hunter123"))

        self.stdout.write(self.style.SUCCESS("All BUG HUNTERS competition data seeded successfully!"))

