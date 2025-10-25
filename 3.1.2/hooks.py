"""Utility hooks for mkDocs."""
import re
import urllib.request


def replacer(match: re.Match) -> str:
    """Find and replace github links with code snippets.

    This function parses a Github link and retreives the specified
    lines of code from the file, formatting it as a markdown code block.
    """
    filename = f'{match.group(3)}.{match.group(4)}'
    url = (
        f'https://raw.githubusercontent.com/{match.group(1)}/{match.group(2)}/{filename}'
    )
    code = urllib.request.urlopen(url).read().decode('utf-8')  # noqa: S310
    extension = 'js' if match.group(4) == 'vue' else match.group(4)
    return '\n'.join(
        [f'``` {extension} title="{filename}"']
        + code.split('\n')[int(match.group(5)) - 1: int(match.group(6))]
        + ['```', f'View at [GitHub]({match.group(0)})']
    )


def on_page_markdown(markdown: str, **kwargs) -> str:  # noqa: ARG001, ANN003
    """Replace GitHub links with code snippets."""
    return re.sub(
        re.compile(
            r'^https://github.com/([\w/\-]+)/blob/([0-9a-f]+)/([\w\d\-/\.]+)\.(\w+)#L(\d+)-L(\d+)$',
            re.MULTILINE,
        ),
        replacer,
        markdown,
    )
