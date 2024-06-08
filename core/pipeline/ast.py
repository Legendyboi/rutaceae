from typing import Any
from lark import Token, Transformer
import core.pipeline.nodes as rtc

class AstBuilder(Transformer):
    def LITERAL(self, item: Token) -> rtc.LiteralExprNode:
        return rtc.LiteralExprNode(item.line, item.column, int(item.value))

    def expr(self, items: list[Any]) -> rtc.ExprNode:
        return items[0]

    def return_stmt(self, items: list[Any]) -> rtc.ReturnStmtNode:
        expr = items[1]
        return rtc.ReturnStmtNode(expr.line, expr.column, expr)

    def block(self, items: list[Any]) -> rtc.BlockNode:
        statements = items[1:-1]
        return rtc.BlockNode(items[0].line, items[0].column, statements)

    def func_def(self, items: list[Any]) -> rtc.FuncDefNode:
        type = items[0].value
        identifier = items[1].value
        body = items[2]
        return rtc.FuncDefNode(
            items[0].line, items[0].column, type, identifier, body
        )

    def program(self, items: list[Any]) -> rtc.ProgramNode:
        return rtc.ProgramNode(0, 0, items)
