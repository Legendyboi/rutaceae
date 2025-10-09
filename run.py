import sys
import argparse
import subprocess
from pathlib import Path
from lark.tree import pydot__tree_to_png
import rich
from core.pipeline.parser import Parser
from core.pipeline.ast import AstBuilder
from core.pipeline.codegen import CodeGenVisitor
import llvmlite.binding as llvm


def compile_to_ir(input_file: Path, verbose: bool = False, generate_png: bool = False):
    """Parse and compile a Rutaceae file to LLVM IR."""
    parser = Parser()
    with input_file.open("rt") as f:
        tree = parser.parse_text(f.read())

    if verbose:
        rich.print(tree)

    # Generate parse tree PNG if requested
    if generate_png:
        tree_png_dir = Path("programs/treePng")
        tree_png_dir.mkdir(parents=True, exist_ok=True)
        png_path = tree_png_dir / f"{input_file.stem}.png"
        pydot__tree_to_png(tree, str(png_path), rankdir="TB")
        if verbose:
            print(f"Parse tree saved to: {png_path}")

    ast = AstBuilder().transform(tree)

    # Generate LLVM IR code
    codegen_visitor = CodeGenVisitor()
    llvm_ir = codegen_visitor.visit(ast)

    if verbose:
        print(llvm_ir)

    return llvm_ir


def cmd_build(args):
    """Compile a Rutaceae program to an executable."""
    if args.verbose:
        print("-----------------")
        print("Rutaceae Compiler")
        print("-----------------")
        print(f"Compiling {args.input} into executable {args.output}")

    llvm_ir = compile_to_ir(args.input, args.verbose, args.generate_png)

    # Initialize LLVM targets
    llvm.initialize_all_targets()
    llvm.initialize_all_asmprinters()

    # Compile LLVM IR to object file
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    mod = llvm.parse_assembly(str(llvm_ir))
    mod.verify()

    with llvm.create_mcjit_compiler(mod, target_machine) as engine:
        engine.finalize_object()
        engine.run_static_constructors()

        obj_file = str(args.output.with_suffix(".o"))
        with open(obj_file, "wb") as f:
            f.write(target_machine.emit_object(mod))

    # Link the object file to create the executable
    executable = str(args.output)
    subprocess.run(["gcc", obj_file, "-o", executable], check=True)

    if args.verbose:
        print(f"Executable {executable} created successfully.")
    else:
        print(f"✓ Compiled: {executable}")


def cmd_run(args):
    """Compile and run a Rutaceae program."""
    if args.verbose:
        print("-----------------")
        print("Rutaceae Compiler")
        print("-----------------")
        print(f"Compiling and running {args.input}")

    llvm_ir = compile_to_ir(args.input, args.verbose, args.generate_png)

    # Initialize LLVM targets
    llvm.initialize_all_targets()
    llvm.initialize_all_asmprinters()

    # Compile LLVM IR to machine code
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    mod = llvm.parse_assembly(str(llvm_ir))
    mod.verify()

    with llvm.create_mcjit_compiler(mod, target_machine) as engine:
        engine.finalize_object()
        engine.run_static_constructors()
        func_ptr = engine.get_function_address("main")

        from ctypes import CFUNCTYPE, c_int

        func_type = CFUNCTYPE(c_int)
        main_func = func_type(func_ptr)
        result = main_func()

        if args.verbose:
            print(f"Program result: {result}")


def main():
    parser = argparse.ArgumentParser(
        prog="rutaceae",
        description="Rutaceae Compiler - Compile and run Rutaceae programs",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Build command
    build_parser = subparsers.add_parser("build", help="Compile a Rutaceae program")
    build_parser.add_argument("input", type=Path, help="Input .rut file")
    build_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Output executable name (default: output)",
    )
    build_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed compilation output"
    )
    build_parser.add_argument(
        "--generate-png",
        action="store_true",
        help="Generate parse tree PNG visualization",
    )
    build_parser.set_defaults(func=cmd_build)

    # Run command
    run_parser = subparsers.add_parser("run", help="Compile and run a Rutaceae program")
    run_parser.add_argument("input", type=Path, help="Input .rut file")
    run_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed compilation output"
    )
    run_parser.add_argument(
        "--generate-png",
        action="store_true",
        help="Generate parse tree PNG visualization",
    )
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
