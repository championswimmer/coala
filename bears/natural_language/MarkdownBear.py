import json

from coalib.bearlib.abstractions.Lint import Lint
from coalib.bears.LocalBear import LocalBear


class MarkdownBear(Lint, LocalBear):
    executable = 'remark'
    diff_message = "The text does not comply to the set style."
    arguments = '--config-path {config_file}'
    gives_corrected = True
    use_stdin = True

    def config_file(self):
        config_json = json.dumps(self.remark_configs,
                                 sort_keys=True,
                                 indent=2,
                                 separators=(',', ': '))
        config_lines = config_json.splitlines(keepends=True)
        print(config_lines)
        return config_lines

    def run(self, filename, file,
            markdown_bullets: str="-",
            markdown_use_closed_headings: bool=False,
            markdown_use_setext_headings: bool=False,
            markdown_emphasis: str="_",
            markdown_strong: str="*",
            markdown_encode_entities: bool=False,
            markdown_codefence: str="`",
            markdown_usefences: bool=False,
            markdown_list_indent: str="tab",
            markdown_loose_tables: bool=False,
            markdown_spaced_tables: bool=True,
            markdown_list_increment: bool=True,
            markdown_horizontal_rule: str='*',
            markdown_horizontal_rule_spaces: bool=False,
            markdown_horizontal_rule_repeat: int=3):
        """
        Raises issues against style violations on markdown files.
        """
        self.remark_configs = {
            "bullet": markdown_bullets,                        # - or *
            "closeAtx": markdown_use_closed_headings,          # Bool
            "setext": markdown_use_setext_headings,            # Bool
            "emphasis": markdown_emphasis,                     # char (_ or *)
            "strong": markdown_strong,                         # char (_ or *)
            "entities": markdown_encode_entities,              # Bool
            "fence": markdown_codefence,                       # char (~ or `)
            "fences": markdown_usefences,                      # Bool
            "listItemIndent": markdown_list_indent,            # int or "tab"
                                                               # or "mixed"
            "looseTable": markdown_loose_tables,               # Bool
            "spacedTable": markdown_spaced_tables,             # Bool
            "incrementListMarker": markdown_list_increment,    # Bool
            "rule": markdown_horizontal_rule,                  # - or * or _
            "ruleSpaces": markdown_horizontal_rule_spaces,     # Bool
            "ruleRepetition": markdown_horizontal_rule_repeat, # int
        }
        return self.lint(filename, file)
