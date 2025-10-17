TARGETS = simple variables struct printer threads tiny buffer

CXXFLAGS = -g -O0 -std=c++17
CFLAGS = -g -O0
LDLIBS = -lpthread

ENTITLEMENTS = entitlements.plist

.PHONY: all
all: $(TARGETS)

.PHONY: clean
clean:
	rm -f $(TARGETS)
	rm -rf $(TARGETS:%=%.dSYM)

.PHONY: sign
sign: $(TARGETS)
	@uname | grep -q Darwin && for bin in $(TARGETS); do \
		codesign --entitlements $(ENTITLEMENTS) --force --sign - $$bin; \
	done || true
