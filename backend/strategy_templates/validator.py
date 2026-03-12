import ast
import re
from typing import List, Set, Tuple

ALLOWED_MODULES: Set[str] = {
    "datetime",
    "math",
    "statistics",
    "collections",
    "itertools",
    "functools",
    "operator",
    "copy",
    "decimal",
    "numpy",
    "pandas",
    "backtrader",
    "backend.trading.strategies.base",
}

FORBIDDEN_PATTERNS: List[str] = [
    r"\bos\s*\.",
    r"\bsubprocess\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__",
    r"\bopen\s*\(",
    r"\bcompile\s*\(",
    r"importlib\b",
    r"\bsys\s*\.",
    r"\bshutil\b",
    r"\bsocket\b",
    r"\bpickle\b",
    r"\bmarshal\b",
    r"\bshelve\b",
    r"\bctypes\b",
    r"\bmultiprocessing\b",
    r"\bthreading\b",
]

DANGEROUS_BUILTINS: Set[str] = {
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
}


class ValidationResult:
    """验证结果"""

    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        self.warnings.append(message)


def extract_imports(code: str) -> Tuple[Set[str], ValidationResult]:
    """提取代码中的所有 import 模块"""
    result = ValidationResult()
    imports: Set[str] = set()

    try:
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    imports.add(node.module)
    except SyntaxError as e:
        result.add_error(f"语法错误: {e.msg} (行 {e.lineno})")
    except Exception as e:
        result.add_error(f"解析代码时发生错误: {str(e)}")

    return imports, result


def check_forbidden_patterns(code: str) -> ValidationResult:
    """检查禁止的模式"""
    result = ValidationResult()

    for pattern in FORBIDDEN_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            result.add_error(f"检测到禁止的模式: {pattern}")

    return result


def check_dangerous_builtins(code: str) -> ValidationResult:
    """检查危险的内建函数"""
    result = ValidationResult()

    pattern = r"\b(" + "|".join(DANGEROUS_BUILTINS) + r")\s*\("
    matches = re.findall(pattern, code)
    if matches:
        for match in set(matches):
            result.add_error(f"检测到危险的内建函数: {match}")

    return result


def check_class_definition(code: str) -> ValidationResult:
    """检查是否定义了策略类"""
    result = ValidationResult()

    try:
        tree = ast.parse(code)
        has_strategy_class = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and "Strategy" in base.id:
                        has_strategy_class = True
                    elif isinstance(base, ast.Attribute) and "Strategy" in base.attr:
                        has_strategy_class = True

        if not has_strategy_class:
            result.add_warning("未检测到继承自 Strategy 的策略类，请确保代码定义了策略类")
    except Exception:
        pass

    return result


def validate_code(code: str) -> ValidationResult:
    """
    验证策略代码的安全性

    Args:
        code: 策略代码字符串

    Returns:
        ValidationResult: 验证结果对象
    """
    result = ValidationResult()

    if not code or not code.strip():
        result.add_error("代码不能为空")
        return result

    imports, parse_result = extract_imports(code)
    result.errors.extend(parse_result.errors)
    result.warnings.extend(parse_result.warnings)
    if not parse_result.is_valid:
        return result

    for module in imports:
        base_module = module.split(".")[0]
        if base_module not in {m.split(".")[0] for m in ALLOWED_MODULES}:
            if module not in ALLOWED_MODULES:
                result.add_error(f"不允许导入模块: {module}")

    pattern_result = check_forbidden_patterns(code)
    result.errors.extend(pattern_result.errors)
    result.warnings.extend(pattern_result.warnings)

    builtin_result = check_dangerous_builtins(code)
    result.errors.extend(builtin_result.errors)
    result.warnings.extend(builtin_result.warnings)

    class_result = check_class_definition(code)
    result.warnings.extend(class_result.warnings)

    return result