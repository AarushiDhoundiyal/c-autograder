import pytest
from agent import csource

ADD = '''#include <stdio.h>
/* scanf in a comment, printf too */
int add(int a, int b) { return a + b; }
int main(void){
    int a, b;
    // scanf("%d", &a);
    scanf("%d %d", &a, &b);
    printf("%d\\n", add(a, b));
    return 0;
}
'''


@pytest.mark.parametrize("ts", [False, True])
def test_functions_and_sanity(ts):
    i = csource.analyze(ADD, use_tree_sitter=ts)
    assert [f.name for f in i.functions] == ["add", "main"]
    assert i.has_main and i.has_reader and i.has_writer and i.main_returns and i.sanity_ok
    assert "add" in next(f for f in i.functions if f.name == "main").calls
    assert i.includes == ["stdio.h"]
    assert i.functions[0].start_line == 3 and i.functions[1].end_line == 10


@pytest.mark.parametrize("ts", [False, True])
def test_comments_and_strings_do_not_count(ts):
    src = 'int main(){ /* scanf("x") */ char*s="printf(1)"; return 0; }'
    i = csource.analyze(src, use_tree_sitter=ts)
    assert not i.has_reader and not i.has_writer
    assert not i.sanity_ok and i.sanity_notes()


def test_backends_agree_on_function_table():
    a = csource.analyze(ADD, use_tree_sitter=False)
    b = csource.analyze(ADD, use_tree_sitter=True)
    key = lambda i: [(f.name, f.start_line, f.end_line, f.calls) for f in i.functions]
    assert key(a) == key(b)


def test_no_main_and_no_return():
    assert not csource.analyze("int f(){return 1;}").has_main
    assert not csource.analyze("int main(){}").main_returns


def test_struct_and_initialiser_are_not_functions():
    src = "struct S { int x; };\nint t[] = {1,2,3};\nint main(){ return 0; }"
    assert [f.name for f in csource.analyze(src, use_tree_sitter=False).functions] == ["main"]
