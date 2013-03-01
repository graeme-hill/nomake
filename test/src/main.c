#include <stdio.h>
 
#include "one.h"
#include "two.h"
#include "foo.h"

int main(int argc, char *argv[]) {
	int one = get_one();
	int two = get_two();
	int foo = get_foo();

	printf("One: %d | Two: %d | Foo: %d\n", one, two, foo);
	
	return 0;
}