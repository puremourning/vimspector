TARGETS=simple variables struct printer threads tiny

CXXFLAGS=-g -O0 -std=c++17
CFLAGS=-g -O0
LDLIBS=-lpthread

.PHONY: all
all: $(TARGETS)

.PHONY: clean
clean:
	rm -f $(TARGETS)
	rm -rf $(TARGETS:%=%.dSYM)
