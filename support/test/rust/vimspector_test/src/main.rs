struct Point {
  x: i32,
  y: i32,
}

struct Foo {
  x: i32,
}

fn main() {
  let s = "World!";
  println!("Hello, {}!", s);

  let f = Foo { x: 42 };
  let g = &f;
  println!("Hello, {} {} {}!", s, g.x, f.x);

  let mut p = Point{ x: 1, y: 11 };

  p.x = 11;
  p.y = 11;
  p.x += 11;
  p.y += 11;

  println!("Point: {}, {}", p.x, p.y);
}
