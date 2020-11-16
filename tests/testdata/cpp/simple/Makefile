CXXFLAGS=-g -O0 -std=c++17

.PHONY: all

TARGETS=simple variables struct printer threads

all: $(TARGETS)

clean:
	rm -f $(TARGETS)
	rm -rf $(TARGETS:%=%.dSYM)
