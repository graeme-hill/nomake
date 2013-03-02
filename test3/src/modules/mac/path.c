#include "../../path.h"

void path_normalize(char *in, char *out) {
	char ch;
	int i = 0;
	while ((ch = in[i++]) != '\0')
		out[i-1] = in[i-1];
	out[i] = '\0'; 
}