#include <iostream>
#include <string>

int main() {
    std::cout << "Hello world!" << std::endl;
    int a = 1;
    ++a;
    int& b = a;
    ++a;
    std::cout << "a: " << a << " b: " << b << std::endl;
    char c = 'a';
    std::string str = "abc";
    std::cout << "str: " << str << " c: " << c << std::endl;
    return 0;
}
