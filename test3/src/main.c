#include "path.h"
#include "io.h"

int main(int argc, char *argv[]) {
	char buffer[1000];
	path_normalize(argv[0], buffer);
	io_log(buffer);
	return 0;
}