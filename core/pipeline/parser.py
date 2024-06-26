from pathlib import Path
import lark

class Parser:
    def __init__(self, grammar_path: Path = Path("/home/Legendyboi/Dev/schoolproj/rutaceae/grammer.lark"), start: str = "program"):
        with grammar_path.open("rt") as f:
            grammar_text = f.read()

        self.lark = lark.Lark(grammar_text, start=start, ambiguity="explicit")

    def parse_text(self, program_text: str) -> lark.ParseTree:
        parsed = self.lark.parse(program_text)
        return parsed
