# Rutaceae 🍊

A modern, statically-typed compiled programming language built with Python, LLVM, and Lark.

[![Version](https://img.shields.io/badge/version-0.4.3-blue.svg)](https://github.com/Legendyboi/rutaceae)
[![License](https://img.shields.io/badge/license-GPLv3-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13+-brightgreen.svg)](https://www.python.org/)

## Features (v0.2.5)

✅ **Complete Type System**
- Integer (`int`), Float (`float`), Boolean (`bool`), String (`string`)
- Type inference and explicit type annotations
- Variable declaration and reassignment

✅ **Operators**
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Logical: `&&`, `||`, `!`

✅ **Modern CLI**
- Verbose mode (`-v`) for detailed compilation output
- Parse tree visualization (`--generate-png`)
- Clean default output for production use

✅ **Professional Compiler Pipeline**
- Lexing & Parsing (Lark)
- AST Generation
- LLVM IR Code Generation
- Native executable compilation via GCC

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Legendyboi/rutaceae.git
cd rutaceae

# Install with Poetry
poetry install
```

### Hello World

Create `hello.rut`:

```rust
fn int main() {
    print("Hello, Rutaceae!");
    return 0;
}
```

Run it:

```bash
poetry run rutaceae run hello.rut
```

## Usage

### Commands

**Run a program** (compile and execute):
```bash
poetry run rutaceae run program.rut
```

**Build an executable**:
```bash
poetry run rutaceae build program.rut -o output_name
```

### CLI Flags

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Show detailed compilation output (parse tree, LLVM IR) |
| `--generate-png` | Generate parse tree visualization in `programs/treePng/` |
| `-o`, `--output` | Specify output executable name (build command only) |

### Examples

```bash
# Clean run (only program output)
poetry run rutaceae run program.rut

# Verbose compilation
poetry run rutaceae run program.rut -v

# Generate parse tree visualization
poetry run rutaceae run program.rut --generate-png

# Build with custom output name
poetry run rutaceae build program.rut -o myapp

# All flags combined
poetry run rutaceae run program.rut -v --generate-png
```

## Language Examples

### Variables and Types

```rust
fn int main() {
    // Type inference
    let x = 10;
    let pi = 3.14159;
    let flag = true;
    let name = "Alice";

    // Explicit type annotations
    let age: int = 25;
    let height: float = 5.9;
    let active: bool = false;

    // Variable reassignment
    x = 20;
    x = x + 5;

    print(x);
    return 0;
}
```

### Arithmetic Operations

```rust
fn int main() {
    let a = 10;
    let b = 3;

    print(a + b);  // 13
    print(a - b);  // 7
    print(a * b);  // 30
    print(a / b);  // 3
    print(a % b);  // 1

    // Float arithmetic
    let x = 10.5;
    let y = 2.0;
    print(x / y);  // 5.250000

    return 0;
}
```

### Comparison and Logic

```rust
fn int main() {
    let x = 10;
    let y = 5;

    // Comparisons return booleans
    let greater = x > y;
    print(greater);  // 1 (true)

    // Logical operators
    let result = (x > 5) && (y < 10);
    print(result);  // 1 (true)

    let check = (x == 10) || (y == 20);
    print(check);  // 1 (true)

    return 0;
}
```

### Comments

```rust
fn int main() {
    // Single-line comment
    let x = 10;

    /*
       Multi-line comment
       spans multiple lines
    */
    print(x);

    return 0;
}
```

## Roadmap

### ✅ Version 0.2.x - Type System & Core Features (COMPLETE)
- [x] **0.2.0** - Arithmetic operators and comments
- [x] **0.2.1** - Boolean types and literals
- [x] **0.2.2** - Floating-point numbers
- [x] **0.2.3** - Variable reassignment
- [x] **0.2.4** - Type annotations
- [x] **0.2.5** - CLI refactor with verbose/PNG flags

### ✅ Version 0.3.x - Control Flow and Improvements (COMPLETE)
- [x] **0.3.0** - If/else statements
- [x] **0.3.1** - While loops
- [x] **0.3.2** - For loops
- [x] **0.3.3** - Break/continue statements
- [x] **0.3.4** - Nested control flow
- [x] **0.3.5** - Language ergonomics, immutability & other additions

### ✅ Version 0.4.x - Functions & Scope (COMPLETE)
- [x] **0.4.0** - Function definitions with parameters
- [x] **0.4.1** - Function calls and return values
- [x] **0.4.2** - Local vs global scope
- [x] **0.4.3** - Recursion support
- [ ] **0.4.4** - Function overloading

### 🎯 Version 0.5.x - Advanced Features
- [ ] **0.5.0** - Arrays and indexing
- [ ] **0.5.1** - Strings as first-class types
- [ ] **0.5.2** - Struct definitions
- [ ] **0.5.3** - Pointers and references
- [ ] **0.5.4** - Standard library basics (I/O, math)

## Project Structure

```
rutaceae/
├── core/
│   └── pipeline/
│       ├── ast.py          # AST transformer (Lark → AST nodes)
│       ├── codegen.py      # LLVM IR code generator
│       ├── nodes.py        # AST node definitions
│       └── parser.py       # Lark parser wrapper
├── programs/               # Example .rut programs
│   ├── treePng/            # Parse tree visualizations (git-ignored)
│   └── test*.rut           # Test programs (working examples)
├── grammer.lark            # Language grammar definition
├── run.py                  # CLI entry point (argparse)
├── pyproject.toml          # Poetry dependencies
├── LICENSE
└── README.md
```

## Architecture

```
┌──────────────┐
│  Source Code │  (.rut file)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Lexer/Parser │  (Lark)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     AST      │  (Abstract Syntax Tree)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   LLVM IR    │  (Intermediate Representation)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Object      │  (via LLVM)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Executable  │  (via GCC linker)
└──────────────┘
```

## Development

### Requirements

- Python 3.13+
- Poetry (package manager)
- GCC (for linking)
- LLVM/llvmlite (installed via Poetry)

### Setup

```bash
# Install dependencies
poetry install

# Run tests
# You may also use the ones provided in programs/ directory
poetry run rutaceae run <program_name>
```

### Adding New Features

1. Update `grammer.lark` with new syntax
2. Add AST nodes in `nodes.py`
3. Implement transformer in `ast.py`
4. Generate LLVM IR in `codegen.py`
5. Test with example programs

## Technical Details

### Type System

| Rutaceae Type | LLVM Type | Size |
|---------------|-----------|------|
| `int` | `i32` | 32-bit signed integer |
| `float` | `double` | 64-bit floating point |
| `bool` | `i1` | 1-bit boolean |
| `string` | `i8*` | Pointer to char array |

### Compilation Process

1. **Parsing**: Lark generates parse tree from source code
2. **AST Transformation**: Custom transformer converts parse tree to AST nodes
3. **Code Generation**: Visitor pattern generates LLVM IR from AST
4. **Optimization**: LLVM applies optimization passes
5. **Object Generation**: LLVM compiles IR to native object code
6. **Linking**: GCC links object file to create executable

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and test
poetry run rutaceae run programs/test.rut

# Commit with conventional commit format
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Lark](https://github.com/lark-parser/lark) parser
- Powered by [LLVM](https://llvm.org/) and [llvmlite](https://github.com/numba/llvmlite)
- Inspired by Rust, C, and modern systems languages

---

**Current Version**: 0.4.3
**Status**: Active Development
**Next Milestone**: Arrays & Advanced Features (v0.5.0)
