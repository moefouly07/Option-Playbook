"""
Compare two Python files for logical equivalence.

Ignores whitespace, comments, and docstrings; compares everything else via
the abstract syntax tree. Used to confirm that a transcribed copy of a file
(for example a chat export whose line breaks were lost) is the same program.

Usage:
    python scanner/tools/ast_equivalence.py FILE_A FILE_B
Exit 0 = EQUAL, exit 1 = NOT EQUAL.
"""
import ast
import sys


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return tree


def normalized_dump(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    return ast.dump(_strip_docstrings(tree), include_attributes=False)


def main(argv) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    a, b = normalized_dump(argv[1]), normalized_dump(argv[2])
    print("EQUAL" if a == b else "NOT EQUAL")
    return 0 if a == b else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
