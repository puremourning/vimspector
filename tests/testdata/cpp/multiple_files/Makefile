CXXFLAGS=-g -O0

foo: lib.o main.o
	$(CXX) -o foo lib.o main.o

.PHONY: clean
clean:
	rm -f *.o foo
