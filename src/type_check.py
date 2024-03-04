import ast
from dataclasses import dataclass
from typing import List, Self


@dataclass(unsafe_hash=True, order=True)
class PythonType:
    head: tuple[str, ...]
    args: tuple["PythonType", ...] = ()

    def __str__(self):
        h = ".".join(self.head)
        out: str
        if h.startswith("<"):
            match h:
                case "<List>":
                    out = f"[{', '.join(map(str, self.args))}]"
                case "<|>":
                    out = " | ".join(map(str, self.args))
                case "<FuncCall>":
                    out = "_FuncCall_"
                case "<Tuple>":
                    if len(self.args) == 1:
                        out = f"({str(self.args[0])},)"
                    else:
                        out = f"({', '.join(map(str, self.args))})"
                case _:
                    raise ValueError(f"Don't know how to handle special head: '{h}'")
        elif len(self.args) == 0:
            out = h
        else:
            out = f"{h}[{', '.join(map(str, self.args))}]"
        return out

    def __repr__(self) -> str:
        return f"ty'{str(self)}'"

    def all_heads(self):
        """Return an iterator of all the type heads."""
        yield self.head
        for arg in self.args:
            yield from arg.all_heads()

    def all_names(self):
        yield self.head_name()
        for arg in self.args:
            yield from arg.all_names()

    def head_name(self) -> str:
        """Return the last part of the type head."""
        if self.head == ():
            return "<empty>"
        else:
            return self.head[-1]

    def is_any(self) -> bool:
        return self.head_name() == "Any"

    def is_none(self) -> bool:
        return self.head_name() == "None"

    def is_union(self) -> bool:
        """Check whether the type is a union type."""
        return self.head_name() == "Union" or self.head_name() == "<|>"

    def is_optional(self) -> bool:
        return self.head_name() == "Optional"

    def normalized(self) -> "PythonType":
        return normalize_type(self)

    @staticmethod
    def from_name(name: str) -> "PythonType":
        return PythonType((name,))

    @staticmethod
    def from_str(s: str) -> "PythonType":
        return parse_type_str(s)

    @staticmethod
    def Any() -> "PythonType":
        return PythonType.from_name("Any")


_type_name_map = {
    "list": "List",
    "tuple": "Tuple",
    "dict": "Dict",
    "set": "Set",
}


def normalize_type_name(name: str) -> str:
    return _type_name_map.get(name, name)


def normalize_type_head(head: tuple[str, ...]) -> tuple[str, ...]:
    n = len(head)
    if n == 0:
        return head
    return (*head[0 : n - 1], normalize_type_name(head[n - 1]))


def normalize_type(typ: PythonType) -> PythonType:
    n_args = tuple(map(normalize_type, typ.args))
    if typ.is_union() or typ.is_optional():
        arg_set = set[PythonType]()
        if typ.is_optional():
            arg_set.add(PythonType(("None",)))
            if len(typ.args) == 0:
                arg_set.add(PythonType.Any())
        for arg in n_args:
            if arg.is_union():
                arg_set.update(arg.args)
            else:
                arg_set.add(arg)
        union_args = tuple(sorted(arg_set))
        return PythonType(("Union",), union_args)
    if all(a.is_any() for a in n_args):
        # if all arguments are Any, we can drop them all
        n_args = tuple()

    return PythonType(normalize_type_head(typ.head), n_args)


def remove_top_optional(t: PythonType) -> PythonType:
    """
    Remove the top-level Optional. i.e., convert Optional[T] to T.
    """
    if t.is_optional():
        if len(t.args) == 1:
            return t.args[0]
        else:
            return PythonType.Any()
    elif t.is_union():
        new_args = tuple(a for a in t.args if not a.is_none())
        if len(new_args) == 1:
            return new_args[0]
        else:
            return PythonType(("Union",), tuple(new_args))
    else:
        return t


def remove_top_final(t: PythonType) -> PythonType:
    """
    Remove the top-level Final. i.e., convert Final[T] to T.
    """
    if t.head_name() == "Final":
        if len(t.args) == 1:
            return t.args[0]
        else:
            return PythonType.Any()
    else:
        return t


def remove_type_namespace(typ: PythonType) -> PythonType:
    """
    Remove the namespace from the type. i.e., convert typing.List[T] to List[T].
    """
    new_args = tuple(map(remove_type_namespace, typ.args))
    new_head = (typ.head[-1],) if typ.head else ()
    return PythonType(new_head, new_args)


def limit_type_depth(typ: PythonType, max_depth: int) -> PythonType:
    """
    Limit the depth of the type to max_depth.
    """
    if max_depth <= 0:
        return PythonType.Any()
    new_args = tuple(map(lambda t: limit_type_depth(t, max_depth - 1), typ.args))
    return PythonType(typ.head, new_args)


def parse_type_str(typ_str: str) -> PythonType:
    tree = ast.parse(typ_str, mode="eval").body
    return parse_type_from_ast(tree)


def parse_type_from_ast(tree: ast.expr) -> PythonType:
    assert isinstance(tree, ast.expr)
    match tree:
        case ast.Name() | ast.Attribute():
            return PythonType(parse_qualified_name(tree))
        case ast.Constant(value=str() as s):
            ty = parse_type_from_ast(ast.parse(s, mode="eval").body)
            return ty
        case ast.Constant(value=v):
            if v == None:
                return PythonType(("None",))
            elif v == (...):
                return PythonType(("...",))
            else:
                return PythonType((str(v),))
        case ast.List(elts=elts):  # this can happen inside Callable
            args = tuple(map(parse_type_from_ast, elts))
            return PythonType(("<List>",), args)
        case ast.Subscript(value=(ast.Attribute() | ast.Name()) as v, slice=slice):
            head = parse_qualified_name(v)
            if head[-1] == "Literal":
                return PythonType(head)  # discard the parameters
            match slice:
                case ast.Tuple(elts=elts):
                    args = tuple(map(parse_type_from_ast, elts))
                case _:
                    args = (parse_type_from_ast(slice),)
            return PythonType(head, args)
        case ast.BinOp(left=left, right=right, op=ast.BitOr()):
            return PythonType(
                ("<|>",), (parse_type_from_ast(left), parse_type_from_ast(right))
            )
        case ast.Call():
            return PythonType(("<FuncCall>",))
        case ast.Tuple(elts=elts):
            return PythonType(("<Tuple>",), tuple(map(parse_type_from_ast, elts)))
        case _:
            raise SyntaxError(
                f"Unsupported ast type: {ast.dump(tree, include_attributes=True)}"
            )


def parse_qualified_name(tree: ast.Attribute | ast.Name):
    segs = []
    while isinstance(tree, ast.Attribute):
        segs.append(tree.attr)
        tree = tree.value  # type: ignore
    assert isinstance(tree, ast.Name)
    segs.append(tree.id)
    return tuple(reversed(segs))


@dataclass
class AccuracyMetric:
    common_type_names: set[str]
    normalize_types: bool = True
    relaxed_equality: bool = True
    filter_none_any: bool = True
    match_base_only: bool = False
    ignore_namespace: bool = True
    ast_depth_limit: int | None = None
    filter_rare: bool = (
        False  # when filter_rare=True and keep_rare=False, only common types are kept
    )
    keep_rare: bool = (
        False  # when filter_rare=True and keep_rare=True, only rare types are kept
    )
    name: str = "acc"

    def process_type(self, t: PythonType) -> PythonType:
        if self.normalize_types:
            t = normalize_type(t)
        if self.relaxed_equality:
            t = remove_top_final(t)
            t = remove_top_optional(t)
        if self.match_base_only:
            t = PythonType(t.head, ())
        if self.ignore_namespace:
            t = remove_type_namespace(t)
        if self.ast_depth_limit is not None:
            t = limit_type_depth(t, self.ast_depth_limit)
        return t

    _NoneOrAny = {"None", "Any"}

    def to_keep_type(self, t: PythonType) -> bool:
        return (not self.filter_none_any or t.head_name() not in self._NoneOrAny) and (
            not self.filter_rare or (self.is_common_type(t) != self.keep_rare)
        )

    def is_common_type(self, t: PythonType) -> bool:
        return t.head_name() in self.common_type_names and all(
            map(self.is_common_type, t.args)
        )

    @staticmethod
    def default_metrics(
        common_type_names: set[str], ast_depth_limit: int | None = None
    ) -> List[Self]:
        return [
            AccuracyMetric(
                common_type_names,
                relaxed_equality=False,
                filter_none_any=False,
                ignore_namespace=False,
                ast_depth_limit=ast_depth_limit,
                name="full_acc",
            ),
            AccuracyMetric(
                common_type_names,
                relaxed_equality=False,
                filter_none_any=False,
                ignore_namespace=False,
                filter_rare=True,
                ast_depth_limit=ast_depth_limit,
                name="full_acc_common",
            ),
            AccuracyMetric(
                common_type_names,
                relaxed_equality=False,
                filter_none_any=False,
                ignore_namespace=False,
                filter_rare=True,
                keep_rare=True,
                ast_depth_limit=ast_depth_limit,
                name="full_acc_rare",
            ),
            AccuracyMetric(
                common_type_names, ast_depth_limit=ast_depth_limit, name="acc"
            ),
            AccuracyMetric(
                common_type_names,
                ast_depth_limit=ast_depth_limit,
                filter_rare=True,
                name="acc_common",
            ),
            AccuracyMetric(
                common_type_names,
                filter_rare=True,
                keep_rare=True,
                ast_depth_limit=ast_depth_limit,
                name="acc_rare",
            ),
            AccuracyMetric(
                common_type_names,
                match_base_only=True,
                ast_depth_limit=ast_depth_limit,
                name="base_acc",
            ),
            AccuracyMetric(
                common_type_names,
                match_base_only=True,
                filter_rare=True,
                ast_depth_limit=ast_depth_limit,
                name="base_acc_common",
            ),
            AccuracyMetric(
                common_type_names,
                match_base_only=True,
                filter_rare=True,
                keep_rare=True,
                ast_depth_limit=ast_depth_limit,
                name="base_acc_rare",
            ),
        ]

    @staticmethod
    def condensed_default_metrics(
        common_type_names: set[str], ast_depth_limit: int | None = None
    ) -> List[Self]:
        return [
            # AccuracyMetric(
            #     common_type_names,
            #     relaxed_equality=False,
            #     filter_none_any=False,
            #     ignore_namespace=False,
            #     ast_depth_limit=ast_depth_limit,
            #     name="full_acc",
            # ),
            AccuracyMetric(
                common_type_names, ast_depth_limit=ast_depth_limit, name="adjusted_acc"
            ),
            AccuracyMetric(
                common_type_names,
                match_base_only=True,
                ast_depth_limit=ast_depth_limit,
                name="base_acc",
            ),
        ]
