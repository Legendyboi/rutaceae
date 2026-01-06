import llvmlite.ir as ir
import llvmlite.binding as llvm
from core.pipeline.nodes import ValueNode


class CodeGenVisitor:
    def __init__(self):
        self.module = ir.Module(name="module")
        self.builder = None
        self.func = None
        self.functions = {}  # name -> ir.Function for function calls
        self.scope_stack = [{}]  # Stack of variable scopes (for local vs global)
        self.const_variables = set()
        self.loop_stack = []

    @property
    def variables(self):
        """Current scope's variables."""
        return self.scope_stack[-1]

    def push_scope(self):
        """Push a new scope for function/block."""
        self.scope_stack.append({})

    def pop_scope(self):
        """Pop the current scope."""
        self.scope_stack.pop()

    def lookup_variable(self, name):
        """Look up a variable in all scopes (innermost first)."""
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def _get_llvm_type(self, type_str):
        """Convert Rutaceae type string to LLVM type."""
        if type_str == "int":
            return ir.IntType(32)
        elif type_str == "float":
            return ir.DoubleType()
        elif type_str == "bool":
            return ir.IntType(1)
        elif type_str == "string":
            return ir.IntType(8).as_pointer()
        elif type_str == "void":
            return ir.VoidType()
        else:
            return ir.IntType(32)  # Default

    def visit(self, node):
        method_name = "visit_" + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{node.__class__.__name__} method")

    def visit_ProgramNode(self, node):
        # Two-pass: first declare all functions, then define them
        # This allows forward references and mutual recursion
        for func_def in node.func_defs:
            self._declare_function(func_def)
        for func_def in node.func_defs:
            self._define_function(func_def)
        return self.module

    def _declare_function(self, node):
        """First pass: declare function signature."""
        param_types = [self._get_llvm_type(p.type) for p in node.params]
        ret_type = self._get_llvm_type(node.type)
        func_type = ir.FunctionType(ret_type, param_types)
        func = ir.Function(self.module, func_type, name=node.identifier)

        # Name the parameters
        for i, param in enumerate(node.params):
            func.args[i].name = param.name

        self.functions[node.identifier] = func
        return func

    def _define_function(self, node):
        """Second pass: define function body."""
        func = self.functions[node.identifier]

        # Create entry block
        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.func = func

        # Push new scope for this function
        self.push_scope()

        # Allocate stack space for parameters and store their values
        for i, param in enumerate(node.params):
            param_type = self._get_llvm_type(param.type)
            alloca = self.builder.alloca(param_type, name=param.name)
            self.builder.store(func.args[i], alloca)
            self.variables[param.name] = alloca

        # Generate function body
        self.visit(node.body)

        # Pop scope
        self.pop_scope()

        return func

    def visit_FuncDefNode(self, node):
        # This is now handled by _declare_function and _define_function
        # Keep for compatibility with direct calls
        pass

    def visit_BlockNode(self, node):
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_ReturnStmtNode(self, node):
        ret_val = self.visit(node.expr)
        self.builder.ret(ret_val)

    def visit_LiteralExprNode(self, node):
        return ir.Constant(ir.IntType(32), node.value)

    def visit_IdentifierExprNode(self, node):
        var_ptr = self.lookup_variable(node.value)
        if var_ptr is None:
            raise Exception(f"Undefined variable: {node.value}")

        # Load the value - for strings this loads the i8* pointer
        return self.builder.load(var_ptr, node.value)

    def visit_CallExprNode(self, node):
        """Generate LLVM IR for function call."""
        func = self.functions.get(node.name)
        if func is None:
            raise Exception(f"Undefined function: {node.name}")

        # Evaluate arguments
        args = [self.visit(arg) for arg in node.args]

        # Type check argument count
        if len(args) != len(func.args):
            raise Exception(
                f"Function '{node.name}' expects {len(func.args)} arguments, got {len(args)}"
            )

        return self.builder.call(func, args, "calltmp")

    def visit_CastExprNode(self, node):
        """Generate LLVM IR for type casting."""
        val = self.visit(node.expr)
        target_type = node.target_type

        # Same type - no op
        current_type_name = self._get_type_name(val.type)
        if current_type_name == target_type:
            return val

        # Handle conversions
        if target_type == "int":
            if val.type == ir.DoubleType():
                # float -> int (truncate)
                return self.builder.fptosi(val, ir.IntType(32), "cast_f_to_i")
            elif val.type == ir.IntType(1):
                # bool -> int (zero extend)
                return self.builder.zext(val, ir.IntType(32), "cast_b_to_i")

        elif target_type == "float":
            if val.type == ir.IntType(32):
                # int -> float
                return self.builder.sitofp(val, ir.DoubleType(), "cast_i_to_f")
            elif val.type == ir.IntType(1):
                # bool -> float (uitofp unsigned int to fp)
                return self.builder.uitofp(val, ir.DoubleType(), "cast_b_to_f")

        elif target_type == "bool":
            if val.type == ir.IntType(32):
                # int -> bool (icmp != 0)
                return self.builder.icmp_signed(
                    "!=", val, ir.Constant(ir.IntType(32), 0), "cast_i_to_b"
                )
            elif val.type == ir.DoubleType():
                # float -> bool (fcmp != 0.0)
                return self.builder.fcmp_ordered(
                    "!=", val, ir.Constant(ir.DoubleType(), 0.0), "cast_f_to_b"
                )

        raise Exception(
            f"Cannot cast type {current_type_name} to {target_type}"
        )

    def _get_type_name(self, llvm_type):
        """Helper to get human-readable type names."""
        if llvm_type == ir.IntType(32):
            return "int"
        elif llvm_type == ir.DoubleType():
            return "float"
        elif llvm_type == ir.IntType(1):
            return "bool"
        elif llvm_type == ir.IntType(8).as_pointer():
            return "string"
        else:
            return str(llvm_type)

    def visit_BinaryOpNode(self, node):
        """Generate LLVM IR for binary operations"""
        # Visit left and right operands
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        if left_val.type != right_val.type:
            if left_val.type == ir.IntType(32) and right_val.type == ir.DoubleType():
                # Promote int to float
                left_val = self.builder.sitofp(
                    left_val, ir.DoubleType(), "int_to_float"
                )
            elif left_val.type == ir.DoubleType() and right_val.type == ir.IntType(32):
                # Promote int to float
                right_val = self.builder.sitofp(
                    right_val, ir.DoubleType(), "int_to_float"
                )
            elif left_val.type == ir.IntType(1) and right_val.type == ir.IntType(32):
                # Promote bool to int for arithmetic
                left_val = self.builder.zext(left_val, ir.IntType(32), "bool_to_int")
            elif left_val.type == ir.IntType(32) and right_val.type == ir.IntType(1):
                # Promote bool to int for arithmetic
                right_val = self.builder.zext(right_val, ir.IntType(32), "bool_to_int")
            else:
                # Incompatible types - clear error message
                left_type_name = self._get_type_name(left_val.type)
                right_type_name = self._get_type_name(right_val.type)
                raise Exception(
                    f"Type mismatch in binary operation: {left_type_name} {node.op} {right_type_name}"
                )

        # Check if either operand is a float
        is_float = left_val.type == ir.DoubleType() or right_val.type == ir.DoubleType()

        # Arithmetic operations
        if node.op == "+":
            return (
                self.builder.fadd(left_val, right_val, "addtmp")
                if is_float
                else self.builder.add(left_val, right_val, "addtmp")
            )
        elif node.op == "-":
            return (
                self.builder.fsub(left_val, right_val, "subtmp")
                if is_float
                else self.builder.sub(left_val, right_val, "subtmp")
            )
        elif node.op == "*":
            return (
                self.builder.fmul(left_val, right_val, "multmp")
                if is_float
                else self.builder.mul(left_val, right_val, "multmp")
            )
        elif node.op == "/":
            return (
                self.builder.fdiv(left_val, right_val, "divtmp")
                if is_float
                else self.builder.sdiv(left_val, right_val, "divtmp")
            )
        elif node.op == "%":
            return (
                self.builder.frem(left_val, right_val, "modtmp")
                if is_float
                else self.builder.srem(left_val, right_val, "modtmp")
            )

        # Comparison operations (return i1 boolean)
        elif node.op == "==":
            return (
                self.builder.fcmp_ordered("==", left_val, right_val, "eqtmp")
                if is_float
                else self.builder.icmp_signed("==", left_val, right_val, "eqtmp")
            )
        elif node.op == "!=":
            return (
                self.builder.fcmp_ordered("!=", left_val, right_val, "neqtmp")
                if is_float
                else self.builder.icmp_signed("!=", left_val, right_val, "neqtmp")
            )
        elif node.op == "<":
            return (
                self.builder.fcmp_ordered("<", left_val, right_val, "lttmp")
                if is_float
                else self.builder.icmp_signed("<", left_val, right_val, "lttmp")
            )
        elif node.op == "<=":
            return (
                self.builder.fcmp_ordered("<=", left_val, right_val, "letmp")
                if is_float
                else self.builder.icmp_signed("<=", left_val, right_val, "letmp")
            )
        elif node.op == ">":
            return (
                self.builder.fcmp_ordered(">", left_val, right_val, "gttmp")
                if is_float
                else self.builder.icmp_signed(">", left_val, right_val, "gttmp")
            )
        elif node.op == ">=":
            return (
                self.builder.fcmp_ordered(">=", left_val, right_val, "getmp")
                if is_float
                else self.builder.icmp_signed(">=", left_val, right_val, "getmp")
            )

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

        if var_name in self.variables:
            raise Exception(f"Variable '{var_name}' is already declared in this scope")

        # Visit the initializer to get its value and infer type
        if node.val is not None:
            var_val = self.visit(node.val)

            # Infer type from the initializer's LLVM type
            # CHECK ORDER MATTERS: bool before int because bool IS int in Python!
            if var_val.type == ir.IntType(1):
                # Boolean (i1)
                var_type = ir.IntType(1)
            elif var_val.type == ir.DoubleType():
                # Float (double)
                var_type = ir.DoubleType()
            elif var_val.type == ir.IntType(8).as_pointer():
                # String pointer
                var_type = ir.IntType(8).as_pointer()
            elif var_val.type == ir.IntType(32):
                # Integer
                var_type = ir.IntType(32)
            else:
                # Default to i32
                var_type = ir.IntType(32)

            # Allocate stack space for the variable
            var_ptr = self.builder.alloca(var_type, name=var_name)
            self.variables[var_name] = var_ptr

            # Store the initial value
            self.builder.store(var_val, var_ptr)

            if node.is_const:
                self.const_variables.add(var_name)
        else:
            # No initializer - use declared type
            if node.type == "int":
                var_type = ir.IntType(32)
            elif node.type == "float":
                var_type = ir.DoubleType()
            elif node.type == "string":
                var_type = ir.IntType(8).as_pointer()
            elif node.type == "bool":
                var_type = ir.IntType(1)
            else:
                var_type = ir.IntType(32)  # Default

            var_ptr = self.builder.alloca(var_type, name=var_name)
            self.variables[var_name] = var_ptr

    def visit_AssignmentStmtNode(self, node):
        """Generate LLVM IR for variable assignment."""

        if node.identifier in self.const_variables:
            raise Exception(f"Cannot assign to const variable: {node.identifier}")

        # Look up the variable in the symbol table
        var_ptr = self.lookup_variable(node.identifier)
        if var_ptr is None:
            raise Exception(f"Assignment to undefined variable: {node.identifier}")

        # Evaluate the new value
        new_val = self.visit(node.expr)

        # Store the new value at the variable's pointer
        self.builder.store(new_val, var_ptr)

    def visit_IfStmtNode(self, node):
        """Generate LLVM IR for if/else statement using basic blocks"""
        # Evaluate condition
        condition_val = self.visit(node.condition)

        # Convert condition to i1 (boolean) if it's not already
        if condition_val.type != ir.IntType(1):
            condition_val = self.builder.icmp_signed(
                "!=", condition_val, ir.Constant(condition_val.type, 0)
            )

        # Create basic blocks
        then_block = self.builder.append_basic_block("if.then")
        merge_block = self.builder.append_basic_block("if.merge")

        if node.else_block:
            else_block = self.builder.append_basic_block("if.else")
            self.builder.cbranch(condition_val, then_block, else_block)
        else:
            self.builder.cbranch(condition_val, then_block, merge_block)

        # Generate 'then' block
        self.builder.position_at_end(then_block)
        self.visit(node.then_block)
        # Only branch if block doesn't already have a terminator (return statement)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)

        # Generate 'else' block if present
        if node.else_block:
            self.builder.position_at_end(else_block)
            self.visit(node.else_block)
            # Only branch if block doesn't already have a terminator
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_block)

        # Continue at merge block
        self.builder.position_at_end(merge_block)

    def visit_WhileStmtNode(self, node):
        """Generate LLVM IR for while loop using basic blocks"""

        # Create basic blocks
        loop_condition = self.builder.append_basic_block("while.condition")
        loop_body = self.builder.append_basic_block("while.body")
        loop_exit = self.builder.append_basic_block("while.exit")

        # Push loop context (continue goes to condition, break goes to exit)
        self.loop_stack.append((loop_condition, loop_exit))

        # Jump to condition check
        self.builder.branch(loop_condition)

        # Generate condition block
        self.builder.position_at_end(loop_condition)
        condition_val = self.visit(node.condition)

        # Convert condition to i1 (boolean) if it's not already
        if condition_val.type != ir.IntType(1):
            condition_val = self.builder.icmp_signed(
                "!=", condition_val, ir.Constant(condition_val.type, 0)
            )

        # Branch based on condition: if true -> body, if false -> exit
        self.builder.cbranch(condition_val, loop_body, loop_exit)

        # Generate body block
        self.builder.position_at_end(loop_body)
        self.visit(node.body)

        # Jump back to condition (only if no terminator like return/break)
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_condition)

        # Pop loop context
        self.loop_stack.pop()

        # Continue at exit block
        self.builder.position_at_end(loop_exit)

    def visit_ForStmtNode(self, node):
        """Generate LLVM IR for for loop using basic blocks"""

        # Execute initialization statement if present
        if node.init is not None:
            self.visit(node.init)

        # Create basic blocks
        loop_condition = self.builder.append_basic_block("for.condition")
        loop_body = self.builder.append_basic_block("for.body")
        loop_update = self.builder.append_basic_block("for.update")
        loop_exit = self.builder.append_basic_block("for.exit")

        # Push loop context (continue goes to update, break goes to exit)
        self.loop_stack.append((loop_update, loop_exit))

        # Jump to condition check
        self.builder.branch(loop_condition)

        # Generate condition block
        self.builder.position_at_end(loop_condition)
        condition_val = self.visit(node.condition)

        # Convert condition to i1 (boolean) if it's not already
        if condition_val.type != ir.IntType(1):
            condition_val = self.builder.icmp_signed(
                "!=", condition_val, ir.Constant(condition_val.type, 0)
            )

        # Branch based on condition: if true -> body, if false -> exit
        self.builder.cbranch(condition_val, loop_body, loop_exit)

        # Generate body block
        self.builder.position_at_end(loop_body)
        self.visit(node.body)

        # Jump to update block (only if no terminator like return/break)
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_update)

        # Generate update block
        self.builder.position_at_end(loop_update)
        self.visit(node.update)

        # Jump back to condition check
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_condition)

        # Pop loop context
        self.loop_stack.pop()

        # Continue at exit block
        self.builder.position_at_end(loop_exit)

    def visit_ValueNode(self, node):
        # CHECK BOOL BEFORE INT! (bool is subclass of int in Python)
        if isinstance(node.value, bool):
            # Boolean: i1 type (1 bit integer)
            return ir.Constant(ir.IntType(1), int(node.value))
        elif isinstance(node.value, float):
            # Float: double type (64-bit floating point)
            return ir.Constant(ir.DoubleType(), node.value)
        elif isinstance(node.value, int):
            # Integer: i32 type
            return ir.Constant(ir.IntType(32), node.value)
        elif isinstance(node.value, str):
            # String: create global constant and return pointer
            string_bytes = bytearray((node.value + "\0").encode("utf8"))
            string_const = ir.Constant(
                ir.ArrayType(ir.IntType(8), len(string_bytes)), string_bytes
            )

            global_str = ir.GlobalVariable(
                self.module, string_const.type, name=f".str.{len(self.module.globals)}"
            )
            global_str.linkage = "internal"
            global_str.global_constant = True
            global_str.initializer = string_const

            return self.builder.bitcast(global_str, ir.IntType(8).as_pointer())

    def visit_IncrementStmtNode(self, node):
        """Generate LLVM IR for increment statement (x++)"""
        # Check if trying to increment const variable
        if node.identifier in self.const_variables:
            raise Exception(f"Cannot increment const variable: {node.identifier}")

        # Look up the variable
        var_ptr = self.lookup_variable(node.identifier)
        if var_ptr is None:
            raise Exception(f"Increment of undefined variable: {node.identifier}")

        # Load current value, add 1, store back
        current_val = self.builder.load(var_ptr, node.identifier)
        one = ir.Constant(current_val.type, 1)

        # Handle different types
        if current_val.type == ir.DoubleType():
            new_val = self.builder.fadd(current_val, one, "inc")
        else:
            new_val = self.builder.add(current_val, one, "inc")

        self.builder.store(new_val, var_ptr)

    def visit_DecrementStmtNode(self, node):
        """Generate LLVM IR for decrement statement (x--)"""
        # Check if trying to decrement const variable
        if node.identifier in self.const_variables:
            raise Exception(f"Cannot decrement const variable: {node.identifier}")

        # Look up the variable
        var_ptr = self.lookup_variable(node.identifier)
        if var_ptr is None:
            raise Exception(f"Decrement of undefined variable: {node.identifier}")

        # Load current value, subtract 1, store back
        current_val = self.builder.load(var_ptr, node.identifier)
        one = ir.Constant(current_val.type, 1)

        # Handle different types
        if current_val.type == ir.DoubleType():
            new_val = self.builder.fsub(current_val, one, "dec")
        else:
            new_val = self.builder.sub(current_val, one, "dec")

        self.builder.store(new_val, var_ptr)

    def visit_CompoundAssignStmtNode(self, node):
        """Generate LLVM IR for compound assignment (x += y)"""
        # Check if trying to assign to const variable
        if node.identifier in self.const_variables:
            raise Exception(f"Cannot assign to const variable: {node.identifier}")

        # Look up the variable
        var_ptr = self.lookup_variable(node.identifier)
        if var_ptr is None:
            raise Exception(
                f"Compound assignment to undefined variable: {node.identifier}"
            )

        # Load current value and evaluate RHS expression
        current_val = self.builder.load(var_ptr, node.identifier)
        rhs_val = self.visit(node.expr)

        # Perform the operation based on operator
        is_float = (
            current_val.type == ir.DoubleType() or rhs_val.type == ir.DoubleType()
        )

        if node.operator == "+=":
            new_val = (
                self.builder.fadd(current_val, rhs_val, "add_assign")
                if is_float
                else self.builder.add(current_val, rhs_val, "add_assign")
            )
        elif node.operator == "-=":
            new_val = (
                self.builder.fsub(current_val, rhs_val, "sub_assign")
                if is_float
                else self.builder.sub(current_val, rhs_val, "sub_assign")
            )
        elif node.operator == "*=":
            new_val = (
                self.builder.fmul(current_val, rhs_val, "mul_assign")
                if is_float
                else self.builder.mul(current_val, rhs_val, "mul_assign")
            )
        elif node.operator == "/=":
            new_val = (
                self.builder.fdiv(current_val, rhs_val, "div_assign")
                if is_float
                else self.builder.sdiv(current_val, rhs_val, "div_assign")
            )
        elif node.operator == "%=":
            new_val = (
                self.builder.frem(current_val, rhs_val, "mod_assign")
                if is_float
                else self.builder.srem(current_val, rhs_val, "mod_assign")
            )
        else:
            raise Exception(f"Unknown compound operator: {node.operator}")

        # Store the result
        self.builder.store(new_val, var_ptr)

    def visit_BreakStmtNode(self, node):
        """Generate LLVM IR for break statement"""
        if not self.loop_stack:
            raise Exception("Break statement outside of loop")

        # Get the break target (exit block) from current loop context
        _, break_block = self.loop_stack[-1]

        # Jump to break target
        self.builder.branch(break_block)

    def visit_ContinueStmtNode(self, node):
        """Generate LLVM IR for continue statement"""
        if not self.loop_stack:
            raise Exception("Continue statement outside of loop")

        # Get the continue target from current loop context
        continue_block, _ = self.loop_stack[-1]

        # Jump to continue target
        self.builder.branch(continue_block)

    def visit_PrintStmtNode(self, node):
        """Enhanced print statement supporting multiple expressions."""

        # If it's just one expression, use the existing implementation
        if len(node.expressions) == 1:
            # Use your exact existing implementation
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

            # Determine the format string based on the LOADED VALUE's type
            if expr_val.type == ir.IntType(8).as_pointer():
                format_str = "%s\n\0"
            elif expr_val.type == ir.IntType(1):
                format_str = "%d\n\0"
            elif expr_val.type == ir.IntType(32):
                format_str = "%d\n\0"
            elif expr_val.type == ir.DoubleType():
                format_str = "%f\n\0"
            else:
                format_str = "%d\n\0"

            # Create format string constant with unique name
            c_format_str = ir.Constant(
                ir.ArrayType(ir.IntType(8), len(format_str)),
                bytearray(format_str.encode("utf8")),
            )

            fmt_name = f".fstr.{len(self.module.globals)}"
            global_format_str = ir.GlobalVariable(
                self.module, c_format_str.type, name=fmt_name
            )
            global_format_str.linkage = "internal"
            global_format_str.global_constant = True
            global_format_str.initializer = c_format_str

            fmt_arg = self.builder.bitcast(global_format_str, voidptr_ty)
            self.builder.call(printf, [fmt_arg, expr_val])

        else:
            # Multiple expressions - print them space-separated on one line
            # Setup printf function (same as above)
            voidptr_ty = ir.IntType(8).as_pointer()
            printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)

            try:
                printf = self.module.get_global("printf")
            except KeyError:
                printf = ir.Function(self.module, printf_ty, name="printf")

            # Print each expression with space separator
            for i, expr in enumerate(node.expressions):
                expr_val = self.visit(expr)

                # Determine format string
                if expr_val.type == ir.IntType(8).as_pointer():
                    base_format = "%s"
                elif expr_val.type == ir.IntType(1):
                    base_format = "%d"
                elif expr_val.type == ir.IntType(32):
                    base_format = "%d"
                elif expr_val.type == ir.DoubleType():
                    base_format = "%f"
                else:
                    base_format = "%d"

                # Add separator or newline
                if i == len(node.expressions) - 1:
                    format_str = base_format + "\n\0"  # Last expression gets newline
                else:
                    format_str = base_format + " \0"  # Others get space

                # Create and use format string (same pattern as your existing code)
                c_format_str = ir.Constant(
                    ir.ArrayType(ir.IntType(8), len(format_str)),
                    bytearray(format_str.encode("utf8")),
                )

                fmt_name = f".fstr.{len(self.module.globals)}"
                global_format_str = ir.GlobalVariable(
                    self.module, c_format_str.type, name=fmt_name
                )
                global_format_str.linkage = "internal"
                global_format_str.global_constant = True
                global_format_str.initializer = c_format_str

                fmt_arg = self.builder.bitcast(global_format_str, voidptr_ty)
                self.builder.call(printf, [fmt_arg, expr_val])
