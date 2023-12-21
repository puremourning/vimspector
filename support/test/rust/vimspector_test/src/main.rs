struct Foo {
  x: i32,
}

fn main() {
  let s = "World!";
  let f = Foo { x: 42 };
  let g = &f;
  println!("Hello, {} {} {}!", s, g.x, f.x);
}
