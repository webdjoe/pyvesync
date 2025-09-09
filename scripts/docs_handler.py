"""The Griffe extension."""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Any

from griffe import (
    AliasResolutionError,
    Docstring,
    DocstringSectionText,
    Extension,
    GriffeLoader,
)

if TYPE_CHECKING:
    from griffe import Module, Object


logger = logging.getLogger(__name__)


def _docstring_above(obj: Object) -> str | None:
    with contextlib.suppress(IndexError, KeyError):
        for parent in obj.parent.mro():  # type: ignore[union-attr]
            if obj.name in parent.members and not parent.members[obj.name].is_alias:
                # Use parent of the parent object to avoid linking private methods
                return (
                    f'Inherited From [`{parent.members[obj.name].parent.name}`]'  # type: ignore[union-attr]
                    f'[{parent.members[obj.name].parent.canonical_path}]'  # type: ignore[union-attr]
                )
    return None


def _inherit_docstrings(  # noqa: C901
    obj: Object, loader: GriffeLoader, *, seen: set[str] | None = None
) -> None:
    if seen is None:
        seen = set()

    # if obj.path in seen:
    #     return  # noqa: ERA001

    seen.add(obj.path)

    if obj.is_module:
        for member in obj.members.values():
            if not member.is_alias:
                with contextlib.suppress(AliasResolutionError):
                    _inherit_docstrings(member, loader, seen=seen)  # type: ignore[arg-type]

    elif obj.is_class:
        for member in obj.all_members.values():
            if docstring_above := _docstring_above(member):  # type: ignore[arg-type]
                if member.docstring is None:
                    member.docstring = Docstring(
                        '',
                        parent=member,  # type: ignore[arg-type]
                        parser=loader.docstring_parser,
                        parser_options=loader.docstring_options,
                    )
                sections = member.docstring.parsed

                # Prevent inserting duplicate docstrings
                if (
                    sections
                    and sections[0].kind == 'text'
                    and sections[0].value.startswith('Inherited From')
                ):
                    continue
                sections.insert(0, DocstringSectionText(docstring_above))
                # This adds the Inherited notation to the base class, can't
                # figure out why.
            if member.is_class:
                _inherit_docstrings(member, loader, seen=seen)  # type: ignore[arg-type]


class InheritedNotation(Extension):
    """Griffe extension for inheriting docstrings."""

    def on_package_loaded(
        self,
        *,
        pkg: Module,
        loader: GriffeLoader,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> None:
        """Inherit docstrings from parent classes once the whole package is loaded."""
        _inherit_docstrings(pkg, loader)
