#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

#include <sys/mman.h>

struct Foo
{
  uint32_t a;
  uint64_t b;
  float    d;
};

static void handle_data(const unsigned char* data, size_t length)
{
  if (length < sizeof(Foo))
    return;

  Foo f;
  memcpy(&f, data, sizeof(Foo));

  std::cout << "a: " << f.a << ", b: " << f.b << ", d: " << f.d << std::endl;
}

int main(int , char**)
{
  unsigned char data[1024];
  Foo f{ 10, 20, 30.7f };

  memcpy(data + 3, &f, sizeof(Foo));

  void *ptr = mmap(nullptr, 2048, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  memcpy(ptr, data+3, sizeof(Foo));

  handle_data((unsigned char*)ptr, sizeof(f));
  munmap(ptr, 2048);

  return 0;
}
