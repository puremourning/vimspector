struct Point {
  x: i32,
  y: i32,
}

fn main() {
  let s = "World!";
  println!("Hello, {}!", s);

  let mut p = Point{ x: 1, y: 11 };

  p.x = 11;
  p.y = 11;
  p.x += 11;
  p.y += 11;

  println!("Point: {}, {}", p.x, p.y);
}
