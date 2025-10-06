import llvmlite.ir as ir
import llvmlite.binding as llvm
from core.pipeline.nodes import ValueNode


class CodeGenVisitor:
    def __init__(self):
        self.module = ir.Module(name="module")
        self.builder = None
        self.func = None
        self.variables = {}

    def visit(self, node):
        method_name = "visit_" + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{node.__class__.__name__} method")

    def visit_ProgramNode(self, node):
        for func_def in node.func_defs:
            self.visit(func_def)
        return self.module

    def visit_FuncDefNode(self, node):
        func_type = ir.FunctionType(ir.IntType(32), [])
        func = ir.Function(self.module, func_type, name=node.identifier)
        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.func = func
        self.visit(node.body)
        return func

    def visit_BlockNode(self, node):
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_ReturnStmtNode(self, node):
        ret_val = self.visit(node.expr)
        self.builder.ret(ret_val)

    def visit_LiteralExprNode(self, node):
        return ir.Constant(ir.IntType(32), node.value)

    def visit_IdentifierExprNode(self, node):
        var_ptr = self.variables.get(node.value)
        if var_ptr is None:
            raise Exception(f"Undefined variable: {node.value}")

        # Load the value - for strings this loads the i8* pointer
        return self.builder.load(var_ptr, node.value)

    def visit_BinaryOpNode(self, node):
        """Generate LLVM IR for binary operations"""
        # Visit left and right operands
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        # Arithmetic operations
        if node.op == "+":
            return self.builder.add(left_val, right_val, "addtmp")
        elif node.op == "-":
            return self.builder.sub(left_val, right_val, "subtmp")
        elif node.op == "*":
            return self.builder.mul(left_val, right_val, "multmp")
        elif node.op == "/":
            return self.builder.sdiv(left_val, right_val, "divtmp")
        elif node.op == "%":
            return self.builder.srem(left_val, right_val, "modtmp")

        # Comparison operations (return i1 boolean)
        elif node.op == "==":
            return self.builder.icmp_signed("==", left_val, right_val, "eqtmp")
        elif node.op == "!=":
            return self.builder.icmp_signed("!=", left_val, right_val, "neqtmp")
        elif node.op == "<":
            return self.builder.icmp_signed("<", left_val, right_val, "lttmp")
        elif node.op == "<=":
            return self.builder.icmp_signed("<=", left_val, right_val, "letmp")
        elif node.op == ">":
            return self.builder.icmp_signed(">", left_val, right_val, "gttmp")
        elif node.op == ">=":
            return self.builder.icmp_signed(">=", left_val, right_val, "getmp")

        # Logical operations (already i1 booleans)
        elif node.op == "&&":
            return self.builder.and_(left_val, right_val, "andtmp")
        elif node.op == "||":
            return self.builder.or_(left_val, right_val, "ortmp")

        else:
            raise Exception(f"Unknown binary operator: {node.op}")

    def visit_UnaryOpNode(self, node):
        """Generate LLVM IR for unary operations"""
        operand_val = self.visit(node.operand)

        if node.op == "-":
            # Negation: 0 - operand
            zero = ir.Constant(ir.IntType(32), 0)
            return self.builder.sub(zero, operand_val, "negtmp")
        elif node.op == "!":
            # Logical not: xor operand with 1 (assuming i1 boolean)
            one = ir.Constant(ir.IntType(1), 1)
            return self.builder.xor(operand_val, one, "nottmp")
        else:
            raise Exception(f"Unknown unary operator: {node.op}")

    def visit_DeclarationStmtNode(self, node):
        var_name = node.identifier

        # Visit the initializer to get its value and infer type
        if node.val is not None:
            var_val = self.visit(node.val)

            # Infer type from the initializer's LLVM type
            if var_val.type == ir.IntType(8).as_pointer():
                # String pointer
                var_type = ir.IntType(8).as_pointer()
            else:
                # Integer or other type
                var_type = var_val.type

            # Allocate stack space for the variable
            var_ptr = self.builder.alloca(var_type, name=var_name)
            self.variables[var_name] = var_ptr

            # Store the initial value
            self.builder.store(var_val, var_ptr)
        else:
            # No initializer - use declared type
            if node.type == "int":
                var_type = ir.IntType(32)
            elif node.type == "string":
                var_type = ir.IntType(8).as_pointer()
            else:
                var_type = ir.IntType(32)  # Default

            var_ptr = self.builder.alloca(var_type, name=var_name)
            self.variables[var_name] = var_ptr

    def visit_ValueNode(self, node):
        if isinstance(node.value, int):
            return ir.Constant(ir.IntType(32), node.value)
        elif isinstance(node.value, str):
            # Create a global string constant
            string_bytes = bytearray((node.value + "\0").encode("utf8"))
            string_const = ir.Constant(
                ir.ArrayType(ir.IntType(8), len(string_bytes)), string_bytes
            )

            # Create global variable for the string
            global_str = ir.GlobalVariable(
                self.module, string_const.type, name=f".str.{len(self.module.globals)}"
            )
            global_str.linkage = "internal"
            global_str.global_constant = True
            global_str.initializer = string_const

            # Return pointer to the first element
            return self.builder.bitcast(global_str, ir.IntType(8).as_pointer())

    def visit_PrintStmtNode(self, node):
        # Visit the expression to get its value
        expr_val = self.visit(node.expr)

        # Declare the printf function (or get existing)
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)

        # Check if printf already exists in the module
        try:
            printf = self.module.get_global("printf")
        except KeyError:
            # Doesn't exist, create it
            printf = ir.Function(self.module, printf_ty, name="printf")

        # Determine the format string based on the LOADED VALUE's type, not the node type
        if expr_val.type == ir.IntType(8).as_pointer():
            # String pointer (i8*)
            format_str = "%s\n\0"
        else:
            # Integer (i32)
            format_str = "%d\n\0"

        # Create format string constant with unique name
        c_format_str = ir.Constant(
            ir.ArrayType(ir.IntType(8), len(format_str)),
            bytearray(format_str.encode("utf8")),
        )

        # Use unique name based on number of globals
        fmt_name = f".fstr.{len(self.module.globals)}"
        global_format_str = ir.GlobalVariable(
            self.module, c_format_str.type, name=fmt_name
        )
        global_format_str.linkage = "internal"
        global_format_str.global_constant = True
        global_format_str.initializer = c_format_str

        # Get pointer to format string
        fmt_arg = self.builder.bitcast(global_format_str, voidptr_ty)

        # Call printf
        self.builder.call(printf, [fmt_arg, expr_val])
