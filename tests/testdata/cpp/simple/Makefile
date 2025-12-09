TARGETS = simple variables struct printer threads tiny buffer

CXXFLAGS = -g -O0 -std=c++17
CFLAGS = -g -O0
LDLIBS = -lpthread

ENTITLEMENTS = entitlements.plist

.PHONY: all
all: $(TARGETS)
	@$(MAKE) sign

.PHONY: clean
clean:
	rm -f $(TARGETS)
	rm -rf $(TARGETS:%=%.dSYM)

.PHONY: sign
sign:
	@uname | grep -q Darwin && for bin in $(TARGETS); do \
		if [ -f $$bin ]; then \
			codesign --entitlements $(ENTITLEMENTS) --force --sign - $$bin; \
		fi; \
	done || true
