#!/usr/bin/env bash

COMMANDS=(
    "http://example.com/index.html"
    "https://example.com/index.html"
    "http://browser.engineering/examples/example1-simple.html"
    "file://$(pwd)/test/test2.html"
    "file://$(pwd)/test/test.html"
    "file://$(pwd)/test/testx.html"
    "file://$(pwd)/test/"
    "data:text/html,Hello World"
    "data:text/html,&lt;div&gt;Hello World&lt;/div&gt;"
)

success=0
total=${#COMMANDS[@]}
for cmd in "${COMMANDS[@]}"; do
    echo "============== $cmd ==============="
    if python browser.py "$cmd"; then
        ((success++))
    fi
    echo "==================================="
done

echo "Successful commands: $success / $total"
