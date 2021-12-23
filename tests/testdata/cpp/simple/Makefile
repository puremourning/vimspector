# vscode-cpptools doesn't support debugging arm64 binaries on macos, but it does
# work with x86_64 bninaries via rosetta 2. mad, but true.
# https://github.com/microsoft/vscode-cpptools/issues/7035
ifeq ($(shell uname -m),arm64)
	ifeq ($(shell uname -s),Darwin)
		ARCHFLAGS=-arch x86_64
	endif
endif

CXXFLAGS=-g -O0 -std=c++17 $(ARCHFLAGS)

.PHONY: all

TARGETS=simple variables struct printer threads
LDLIBS=-lpthread

all: $(TARGETS)

clean:
	rm -f $(TARGETS)
	rm -rf $(TARGETS:%=%.dSYM)
