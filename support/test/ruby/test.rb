class Foo
  def initialize
    @bar = 'bar'
  end

  def bar
    @bar
  end
end

f = Foo.new
puts f.bar
